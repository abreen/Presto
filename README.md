presto
======

`presto` is a Python script that helps maintain a
static website from Markdown sources. It was written on
`csa2.bu.edu` to fit the... unique requirements of that system.

Usage
-----

Try `python3.3 presto.py` from this directory. If you don't use
Python 3.3, bad things might happen.

When `presto` runs, it will determine which draft Markdown files have
changed since last time. It will only update the HTML for those files.

When a file is updated, the Markdown source is converted to HTML
and placed inside an HTML template. Then the new HTML file is saved
in the web root directory (which is assumed to be the directory that
encloses this `presto` directory --- however, this can be changed in
the `presto.py` file).

Markdown sources are drawn from the `drafts` directory. Each file should
have the extension `.markdown`. The file tree starting from `drafts` is
essentially mirrored to the web root, with the exception of the `img`,
`js`, and `css` directories, which live here but are symlinked to from
the web root. This means that changes to the `img`, `js` and `css`
directories are seen immediately by the web server.


Dependencies
------------

In the absence of superuser priveleges the following dependencies
have been included and written into the `presto` code.

* Python-Markdown (from [GitHub repo][pm], commit e7b6a33f0e) in `markdown/`
* Grid Tables Extension for Python-Markdown (from [GitHub repo][gt], commit
  b4d16d5d25) in `mdx_grid_tables.py`

Authors
-------

`presto` was written by Alexander Breen (abreen@bu.edu).


[pm]: https://github.com/waylan/Python-Markdown
[gt]: https://github.com/smartboyathome/Markdown-GridTables
