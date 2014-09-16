presto
======

`presto` is a Python script that helps maintain a static website from
Markdown sources. It was written as a custom solution for using Markdown
on a restrictive web server, as an alternative to other static
website publishers that require elaborate libraries or superuser
privileges. Its only requirement is Python 3.2 or newer.

*There is a Python 2 version available.* See the `retro` branch of
this repository.


Usage
-----

`presto` is a command-line program, and it runs with no arguments.

When `presto` runs, it will determine which draft Markdown files have
changed since last time. It will only update the HTML for those files.

When a file is updated, the Markdown source is converted to HTML
and placed inside an HTML template. Then the new HTML file is saved
to the HTML output directory (defined as `OUTPUT_DIR` in `presto.py`).

If any HTML is found in the Markdown file, it is preserved and written
to the output HTML file. However, any HTML comments are removed from the
output file.

Markdown sources are drawn from the `drafts` directory. Each file should
have the extension `.markdown`. The file tree starting from `drafts` is
mirrored to `OUTPUT_DIR`.


Notes
-----
* If you want to force `presto` to rewrite all HTML (if, for example,
  you changed the `template.html` file), just delete the
  `cache` file.


Authors
-------

`presto` was written by Alexander Breen (abreen@bu.edu).
The other source files in this repository are property of their
respective authors. See each `py` file.
