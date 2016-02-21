title: Advanced Presto features
foo: bar
bar: one
     two
     three

## Using curly brace sequences

Python expressions or statements can be evaluated by using one of
two types of `\{ ... \}` sequences.

*   For any Python expression `expr`, `\{\{ expr \}\}` causes `expr` to be
    evaluated by the Python interpreter and the curly brace sequence is
    replaced with the string returned by `repr(expr)`. For example, by using

        \{\{ 3 + 4 \}\}

    in your `.markdown` draft file, the sequence will be replaced
    with {{ 3 + 4 }}.

*   For any number of Python statements `stmt1`, `stmt2`, ... `stmtN`,
    the curly brace sequence

        \{\%
        stmt1
        stmt2
        ...
        stmtN
        \%\}

    is replaced with any output sent to the standard out by the
    statements. For example,

        \{\%
        import functools

        def combine(x, y):
            return x + y

        vals = [1, 2, 3, 4]

        reduced = functools.reduce(combine, vals)
        print(reduced)
        \%\}

    is replaced with

        {%
        import functools

        def combine(x, y):
            return x + y

        vals = [1, 2, 3, 4]

        reduced = functools.reduce(combine, vals)
        print(reduced)
        %}

    If there are many lines of output, all lines are indented to match
    the indentation level of the first `\{\%`:

        {%
        print('foo')
        print('bar')
        %}

All `\{\{ ... \}\}` and `\{\% ... \%\}` sequences are processed top-to-bottom
by the Python interpreter, and any variables or functions introduced by
the code contained in the sequences is available to later sequences, as you
would expect.
For example, we can access the `vals` list here: `{{ vals }}`.

The sequences are processed and substituted before the conversion from
Markdown to HTML takes place, so your Python code could contain valid
Markdown:

{%
print('### Heading test')
print()
print('*Markdown* is **awesome**!')
print('* * *')
%}


## Helper functions

Since curly brace sequences are fed directly into the Python interpreter,
any built-in Python functions can be used. `import` statements may also
be used (see the example above).

In addition to Python built-ins, Presto's `functions` module is added
to the global namespace before code is evaluated. This module contains
some useful helper functions:

*   The `include_draft()` and `include_partial()` functions take a path to
    another file and print the contents of the file. For `include_draft()`,
    a path is given relative to the `drafts/` directory.
    For `include_partial()`, a path is given relative to the `partials/`
    directory.

    -   `include_draft()` prints an entire draft file, without the
        metadata part at the beginning of a draft file.
    -   `include_partial()` simply prints an entire file from
        the `partials/` directory (*partial* refers to a file containing
        a part of a document that you may want to include in many
        different pages).

    Since these functions print a file, they should be used within
    `\{\% ... \%\}` sequences. (If these functions returned a string
    instead of printing, using `\{\{ ... \}\}` with them would include
    the quotes around the string that `repr()` would add.)

    Here's an example of including a
    partial: ***{% include_partial('foo.txt') %}***
    As mentioned above, you may write partials that contain Markdown,
    and the Markdown will be converted to HTML, since the conversion
    process occurs after curly brace sequences are processed.

    Here's an example of including another draft file:
    {% include_draft('foo.markdown') %}

*   The `shell()` function takes a function and any arguments to it,
    and prints a representation of what calling the function on the
    Python shell would look like.

    For example, the following curly brace sequence

        \{\%
        def mult(x, y):
            return x * y

        shell(mult, [2, 3])
        \%\}

    produces the following:

        {%
        def mult(x, y):
            return x * y

        shell(mult, [2, 3])
        %}

    The `shell()` function can also take two additional keyword
    arguments, `prompt` and `followup`, as demonstrated below:

        \{\%
        shell(mult, [2, 3], prompt='> ', followup=False)
        \%\}

    appears as

        {%
        shell(mult, [2, 3], prompt='> ', followup=False)
        %}


## Using variables from the metadata

The first lines of every Markdown draft is a
sequence of `variable: value` lines, which must contain a value for `title`.
But you may use this metadata section to define any variables you'd like,
whose values (as strings) are given to the Python interpreter as local
variables when curly brace sequences are processed.

For example, suppose this draft begins with the following metadata:

    title: Advanced Presto features
    foo: bar

The `foo` variable can be used anywhere in curly brace sequences. In
this case, `foo` would contain the value `{{ foo }}`.

It is possible to specify a list of values for a variable. In this case,
the variable is a list of strings. Suppose the metadata contains the
following:

    title: Advanced Presto features
    foo: bar
    bar: one
         two
         three

Then `bar` evaluates to `{{ bar }}`.

### Altering `sys.path`

You can add directories to Python's module search path by defining the
metadata variable `path` across one or more lines. Each line should
contain a valid absolute path to a directory containing Python modules
you'd like to be able to import in a `\{\% ... \%\}` sequence.

For example, if you'd like to import a module `foo` that exists in
the file system at `/a/b/foo.py`, add the following to the metadata:

    path: /a/b

Then, simply use `import foo` in your `\{\% ... \%\}` sequence.
