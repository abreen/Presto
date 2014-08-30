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
to the HTML output directory (defined as `OUTPUT_DIR` in `presto.py`).

If any HTML is found in the Markdown file, it is preserved and written
to the output HTML file. However, any HTML comments are removed from the
output file.

Markdown sources are drawn from the `drafts` directory. Each file should
have the extension `.markdown`. The file tree starting from `drafts` is
essentially mirrored to the web root, with the exception of the `img`,
`js`, and `css` directories, which live here (the `presto` directory).
These directories (and any others) should be symlinked to from wherever
`OUTPUT_DIR` is set.

If you want to add another directory (for example, for PDF files), you
could just create a new directory at the web root as normal. However, it
might be a better idea to create the directory here (inside the `presto`
directory) and symlink to it from `OUTPUT_DIR`. This way if anything odd
happens with the HTML, you can just completely wipe out the files under
`OUTPUT_DIR`, delete `presto-cache`, and invoke `presto` again to
rebuild everything.


Notes
-----
* If you want to force `presto` to rewrite all HTML (if, for example,
  you've changed the `template.html` file), just delete the
  `presto-cache` file.


Dependencies
------------

In the absence of superuser privileges the following dependencies
have been included and written into the `presto` code.

* Python-Markdown (from GitHub repo, commit e7b6a33f0e) in `markdown/`


Authors
-------

`presto` was written by Alexander Breen (abreen@bu.edu).
