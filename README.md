presto
======

`presto` is a Python program that helps maintain a static website from Markdown
sources. It was written as a custom solution for using Markdown on a
restrictive web server, as an alternative to other static website publishers
that require elaborate libraries or superuser privileges. Its only requirement
is Python 2.6 or newer (including Python 3).


Usage
-----

In your shell, run the `presto.sh` script with no arguments.

*   `presto.sh` will determine which Python interpreter is available
    on your system, trying to locate a Python 3 interpreter first, then
    a Python 2 interpreter.
*   The Python interpreter is invoked and it runs the `main()` function
    in the `presto` package. Then `presto` determines which draft Markdown
    files have been marked for publishing and have changed since last time.
    It will only update the HTML for those files.

When a file is updated, the Markdown source is converted to HTML
and placed inside an HTML template. Then the new HTML file is saved
to the HTML output directory (`presto` uses the `output_dir` variable
defined in the configuration file).

If any HTML is found in the Markdown file, it is preserved and written
to the output HTML file. However, any HTML comments are removed from the
output file.

Markdown sources are drawn from the `markdown_dir` (from the configuration file)
directory. Each file should have the extension `.markdown`. The file tree
starting from `markdown_dir` is mirrored to `output_dir`.


Notes
-----
*   If you want to force `presto` to rewrite all HTML (if, for example,
    you changed the `template.html` file), just delete the
    cache file.
*   Markdown sources must have a metadata section with at least `title`
    defined, for the page title. You can also define your own metadata
    variables and use them in the Markdown using `{{ ... }}` or `{% ... %}`
    sequences. See the examples.


Authors
-------

`presto` was written by Alexander Breen (abreen@bu.edu).
The other source files in this repository are property of their
respective authors. See each subpackage of the `presto` package.
