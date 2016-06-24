`presto` is a Python package that helps maintain a static website from Markdown
sources. It was written as a custom solution for using Markdown on a
restrictive web server, as an alternative to other static website publishers
that require elaborate libraries or superuser privileges for installation. Its
only requirement is Python 2.6 or newer (including Python 3).


## Usage

Installation of `presto` is not required, since its dependencies are located
in this repository. The only requirement is that Python knows to look in this
directory when executing an `import` statement.

The simple and common way to satisfy this requirement is to use this directory
as your working directory when running `presto`. In this case, invoking
`presto` is as simple as

    python -m presto <args>

if your system's Python interpreter is named `python`. On some systems, a
version number may be required at the end (e.g., `python3` or `python2.7`). The
`-m` flag instructs Python to find the module named `presto` and run its
`__main__.py` file.

If you want to use `presto` from other locations, you can set the `PYTHONPATH`
environment variable to refer to this directory. On most shells, you can set
the variable on the same command line you use to run `python`, and the variable
will exist for the life of that command. For example, in Bash:

    PYTHONPATH=/path/to/presto/repo python -m presto <args>

If you'd like, you can alias the command `presto` to this string in your
shell's configuration file, to save you typing. For example, in Bash:

    alias presto="PYTHONPATH=/Users/abreen/.../git/presto python -m presto"


## What it does

When you invoke `presto` with no command line arguments, it does the following:

1.  Looks for a configuration `.ini` file in the current working directory
2.  Determines which Markdown files have been marked for publishing and have
    changed since the last time `presto` was run
3.  Then, for each file to publish:
    *   Evaluates all `{{ ... }}` and `{% ... %}` sequences in the
        Markdown file to obtain a new Markdown file
        -   `{{ ... }}` sequences are replaced with the value of the
            Python expression contained by them, and `{% ... %}`
            sequences are replaced with the output produced by running
            the code in the Python interpreter; see the examples for more
    *   Converts the result of the previous step to HTML
    *   Substitutes `{{ title }}`, `{{ head }}`, and `{{ footer }}` in the
        template with values taken from the metadata
    *   Places the HTML from the previous step where `{{ body }}` appears
        in the template
    *   Saves the new HTML file to the HTML output directory

A Markdown file is eligible for publishing if it does not begin with the
characters `_`, `.`, or `#`. The common convention is to name files that
you do not want to publish yet starting with `_`.

If any HTML is found in the Markdown file, it is preserved and written
to the output HTML file. However, any HTML comments are removed from the
output file.

The configuration `.ini` file contains the locations where `presto` can
find Markdown sources, partials, the template file, and the HTML output
directory.


## Notes

*   If you want to force `presto` to rewrite all HTML (if, for example,
    you changed the `template.html` file), just delete the cache file.
*   Markdown sources must have a metadata section with at least `title`
    defined, for the page title. You can also define your own metadata
    variables and use them in the Markdown using `{{ ... }}` or `{% ... %}`
    sequences. See the examples.


## Author

`presto` was written by Alexander Breen (breen.io).

The other source files in this repository are property of their respective
authors. See each file or module outside of the `presto` package.
