title: Advanced Presto features
head: <script type="text/javascript" src="foo.js"></script>
foo: bar
bar: one
     two
     three

## Using curly brace sequences

Python expressions or statements can be evaluated by using `\{`-sequences.

*   For any Python expression `<expr>`, `\{\~ <expr> \~\}` causes `<expr>` to
    be evaluated by the Python interpreter and the curly brace sequence is
    replaced with the string returned by `repr(<expr>)`. For example, by using

        \{\~ 3 + 4 \~\}

    in your `.markdown` draft file, the sequence will be replaced
    with {~ 3 + 4 ~}.

*   Like the `\{\~`-sequence, for any Python expression `<expr>`, `\{\= <expr> \=\}`
    causes the expression to be evaluated by the interpreter, but the sequence
    gets replaced with the string returned by `str(<expr>)`. For example,
    the sequence

        \{\= 'foo' + 'bar' \=\}

    will be replaced with: {= 'foo' + 'bar' =}.

*   For any number of Python statements `stmt1`, `stmt2`, ... `stmtN`,
    the curly brace sequence

        \{\!
        stmt1
        stmt2
        ...
        stmtN
        \!\}

    is replaced with any output sent to the standard out by the
    statements. For example,

        \{\!
        import functools

        def combine(x, y):
            return x + y

        vals = [1, 2, 3, 4]

        reduced = functools.reduce(combine, vals)
        print(reduced)
        \!\}

    is replaced with

        {!
        import functools

        def combine(x, y):
            return x + y

        vals = [1, 2, 3, 4]

        reduced = functools.reduce(combine, vals)
        print(reduced)
        !}

    If there are many lines of output, all lines are indented to match
    the indentation level of the first `\{\!`:

        {!
        print('foo')
        print('bar')
        !}

All `\{`-sequences are processed top-to-bottom by the Python interpreter, and
any variables or functions introduced by the code contained in the sequences is
available to later sequences, as you would expect. For example, we can still
access the `vals` list here: `{~ vals ~}`.

The sequences are processed and substituted before the conversion from
Markdown to HTML takes place, so your Python code could contain valid
Markdown:

{!
print('### Heading test')
print()
print('*Markdown* is **awesome**!')
print('* * *')
!}


## Helper functions

Since curly brace sequences are fed directly into the Python interpreter,
any built-in Python functions can be used. `import` statements may also
be used (see the example above).

In addition to Python built-ins, Presto's `functions` module is added
to the global namespace before code is evaluated. This module contains
some useful helper functions:

*   The `draft()` and `partial()` functions take a path to another file and
    return the contents of the file as a string. For `draft()`, a path is given
    relative to the `drafts/` directory. For `partial()`, a path is given
    relative to the `partials/` directory.

    -   `draft()` returns the contents of an entire draft file, **without** the
        metadata part at the beginning of a draft file.
    -   `partial()` simply returns an entire file from the `partials/`
        directory (*partial* refers to a file containing a part of a document
        that you may want to include in many different pages).

    Here's an example of including a partial: ***{= partial('foo.txt') =}***
    As mentioned above, you may write partials that contain Markdown, and the
    Markdown will be converted to HTML, since the conversion process occurs
    after `\{`-sequences are processed.

    Here's an example of including another draft file:
    {= draft('foo.markdown') =}

*   The `shell()` function takes a function and any arguments to it,
    and returns a representation of what calling the function on the Python
    shell would look like.

    For example, the following curly brace sequence

        \{\!
        def mult(x, y):
            return x * y

        print(shell(mult, [2, 3]))
        \!\}

    produces the following:

        {!
        def mult(x, y):
            return x * y

        print(shell(mult, [2, 3]))
        !}

    The `shell()` function can also take two additional keyword
    arguments, `prompt` and `followup`, as demonstrated below:

        \{\! print(shell(mult, [2, 3], prompt='> ', followup=False)) \!\}

    appears as the following:

        {! print(shell(mult, [2, 3], prompt='> ', followup=False)) !}

    Note that we are using `\{\!`-sequences and `print()` here, since
    the `\{\!`-sequence ensures that all lines of the output it captures
    are indented to the column where the `\{\!` is found. This ensures each
    line of the output is indented four spaces, which tells the Markdown
    converter to put it in a `<code>` HTML element.


## Using variables from the metadata

The first lines of every Markdown draft is a sequence of `variable: value`
lines. You may use this metadata section to define any variables you'd like,
whose values (as strings) are given to the Python interpreter as local
variables when curly brace sequences are processed.

For example, suppose this draft begins with the following metadata:

    title: Advanced Presto features
    foo: bar

The `foo` variable can be used anywhere in curly brace sequences. In
this case, `foo` would contain the value `{~ foo ~}`.

It is possible to specify a list of values for a variable. In this case,
the variable is a list of strings. Suppose the metadata contains the
following:

    title: Advanced Presto features
    foo: bar
    bar: one
         two
         three

Then `bar` evaluates to `{~ bar ~}`.

### Altering `sys.path`

You can add directories to Python's module search path by defining the
metadata variable `path` across one or more lines. Each line should
contain a valid absolute path to a directory containing Python modules
you'd like to be able to import in a `\{\!`-sequence.

For example, if you'd like to import a module `foo` that exists in
the file system at `/a/b/foo.py`, add the following to the metadata:

    path: /a/b

Then, simply use `import foo` in your `\{\!`-sequence.
