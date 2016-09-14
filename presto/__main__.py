from __future__ import print_function, with_statement

import sys
import os
import io
import stat
import hashlib

import markdown
import mdx_grid_tables as grid_tables
import mdx_mathjax as mathjax
import mkdcomments as comments
import six

import presto.output as output
import presto.convert as convert
import presto.config as config
import presto.options as options


def get_cache(cache_file):
    cache = {}

    if not os.path.isfile(cache_file):
        return cache

    with io.open(cache_file) as f:
        for line in f:
            tokens = line.split()
            cache[tokens[0]] = tokens[1]

    return cache


def write_cache(cache, cache_file):
    with io.open(cache_file, mode='w') as f:
        for (k, v) in cache.items():
            f.write(six.u("{}\t{}\n").format(k, v))


def compute_hash(path):
    """Open the specified file in binary mode and use its raw bytes to compute
    and return an MD5 hex digest of the file.
    """
    with io.open(path, mode='rb') as f:
        bytes = f.read()

    h = hashlib.md5()
    h.update(bytes)
    return h.hexdigest()


def makedirs(dirpath):
    """Recursively create directories up to the leaf directory, if they
    do not already exist. Unlike os.makedirs, this function will not
    produce an error if any intermediate directories exist or have modes
    not matching the 'mode' parameter.
    """
    head, tail = os.path.split(dirpath)
    if tail == '':
        # root directory or current relative root has been reached
        return
    else:
        # make all parent directories
        makedirs(head)

        # make this directory if it does not exist
        if not os.path.isdir(dirpath):
            os.mkdir(dirpath)
            print("created directory '{}'".format(dirpath))


def should_publish(path):
    filename = os.path.basename(path)
    return filename[0] != '_'


def is_markdown(filename):
    lower = filename.lower()
    return lower.endswith('.markdown') or lower.endswith('.md')


def extension_to_html(filename):
    lower = filename.lower()
    for ext in ['.markdown', '.md']:
        if lower.endswith(ext):
            parts = filename.split('.')
            return '.'.join(parts[:-1]) + config.get('html_extension')

    return filename


def extension_drop(filename):
    config_ext = config.get('html_extension').lower()
    if '.' in config_ext:
        config_ext = config_ext.split('.')[-1]

    parts = filename.split('.')
    ext = parts[-1]
    if ext.lower() in ['md', 'markdown', config_ext]:
        return '.'.join(parts[:-1])
    else:
        return filename


def copy_htaccess(path, relpath):
    old_umask = os.umask(0o002)

    head, tail = os.path.split(relpath)
    relpath = os.path.join(head, '.htaccess')

    output_path = os.path.join(config_get_filepath('output_dir'), relpath)

    try:
        makedirs(os.path.dirname(output_path))
    except:
        if options.get('debug'):
            output.traceback()

        output.error("cannot make directories for htaccess '{}'".format(output_path))
        os.umask(old_umask)
        return False

    was_here = os.path.isfile(output_path)

    try:
        with io.open(path) as htfile:
            with io.open(output_path, mode='w') as of:
                of.write(htfile.read())
    except:
        if options.get('debug'):
            output.traceback()

        output.error("could not create htaccess '{}'".format(output_path))
        os.umask(old_umask)
        return False

    if not was_here:
        st = os.stat(output_path)
        os.chmod(output_path, st.st_mode | stat.S_IXGRP | stat.S_IXOTH)

    os.umask(old_umask)
    print("created htaccess file '{}'".format(output_path))
    return True


def config_get(name):
    value = config.get(name)
    if value is None:
        output.error('no value for required configuration variable "{}"'.format(name))
        sys.exit(1)
    else:
        return value

def config_get_filepath(name):
    value = config.get_filepath(name)
    if value is None:
        output.error('no value for required configuration variable "{}"'.format(name))
        sys.exit(1)
    else:
        return value


config.load(
    path=options.get('config')
)

# post-process the whitelist: split on commas and remove extra spaces
whitelist = [s.strip() for s in config_get('whitelist').split(',')]

os.umask(0o002)

extensions = [
    'def_list',
    'footnotes',
    'meta',
    'smarty',
    'headerid',
    'tables',
    'codehilite',
    'admonition',
    'toc',
    grid_tables.GridTableExtension(),
    mathjax.MathJaxExtension(),
    comments.CommentsExtension()
]

args = {
    'extensions': extensions,
    'extension_configs': {
        'smarty': [('smart_ellipses', False)]
    },
    'output_format': 'html5',
    'lazy_ol': False
}

md = markdown.Markdown(**args)

with io.open(config_get_filepath('template_file')) as f:
    template = f.read()

num_published = num_errors = num_skipped = num_removed = 0

try:
    cache = get_cache(config_get_filepath('cache_file'))
except:
    if options.get('debug'):
        output.traceback()

    output.error('could not open cache file')
    cache = {}
    num_errors += 1

expected_files = []

for dirpath, dirnames, filenames in os.walk(config_get_filepath('markdown_dir')):
    for f in filenames:
        if not is_markdown(f) and f != 'htaccess':
            continue

        if f[0] in ['.', '#']:
            continue

        if f[-1] == '~':
            continue

        path = os.path.join(dirpath, f)
        relpath = os.path.relpath(path, config_get_filepath('markdown_dir'))

        if should_publish(path):
            expected_files.append(extension_drop(relpath))
        else:
            cache.pop(relpath, None)

        try:
            infile = io.open(path)
        except:
            if options.get('debug'):
                output.traceback()

            output.error("unable to read '{}'".format(relpath))
            num_errors += 1
            continue

        try:
            hash = compute_hash(path)
        except:
            if options.get('debug'):
                output.traceback()

            output.error("unable to compute hash for '{}'".format(relpath))
            num_errors += 1
            continue

        if relpath not in cache or cache[relpath] != hash:
            if should_publish(path):
                cache[relpath] = hash
            else:
                if not options.get('hide_skipped'):
                    output.skipped(relpath)
                num_skipped += 1
                continue
        else:
            # no change to this file since last time
            continue

        if f == 'htaccess':
            if options.get('dry_run'):
                success = True
            else:
                success = copy_htaccess(path, relpath)

            if success:
                num_published += 1
            else:
                num_errors += 1

            continue

        try:
            html, errors = convert.md_to_html(md, template, infile, {'hash': hash})
        except:
            cache.pop(relpath, None)

            if options.get('debug'):
                output.traceback()

            output.error("unable to convert Markdown to HTML for '{}'".format(relpath))
            num_errors += 1
            continue

        if errors:
            for err in errors:
                output.error('{}: {}'.format(relpath, err))
                num_errors += 1

            if not options.get('use_empty'):
                cache.pop(relpath, None)
                num_skipped += 1
                continue

        # create path to output directory
        output_path = os.path.join(config_get_filepath('output_dir'), extension_to_html(relpath))

        try:
            if not options.get('dry_run'):
                makedirs(os.path.dirname(output_path))
        except:
            if options.get('debug'):
                output.traceback()

            output.error("cannot make directories for '{}'".format(relpath))
            cache.pop(relpath, None)
            num_errors += 1
            continue

        try:
            if not options.get('dry_run'):
                with io.open(output_path, mode='w') as of:
                    of.write(html)
        except:
            if options.get('debug'):
                output.traceback()

            output.error("cannot write output file '{}'".format(relpath))
            cache.pop(relpath, None)
            num_errors += 1
            continue

        num_published += 1
        output.published(relpath)

        md.reset()

# done publishing all HTML
# now remove the HTML files for non-existent Markdown
for dirpath, dirnames, filenames in os.walk(config_get_filepath('output_dir')):

    # skip any directories specified in the whitelist
    while True:
        for d in dirnames:
            dirname = os.path.join(dirpath, d)
            reldirname = os.path.relpath(dirname, config_get_filepath('output_dir'))

            if reldirname in whitelist:
                dirnames.remove(d)
                break
        else:
            break

    for f in filenames:
        if f[0] == '.' and f != '.htaccess':
            continue

        path = os.path.join(dirpath, f)
        relpath = os.path.relpath(path, config_get_filepath('output_dir'))

        head, tail = os.path.split(relpath)
        if f == '.htaccess':
            relpath = os.path.join(head, 'htaccess')
        else:
            relpath = os.path.join(head, extension_drop(f))

        if relpath not in expected_files:
            cache.pop(relpath, None)

            try:
                if not options.get('dry_run'):
                    os.remove(path)

                num_removed += 1
                output.removed(relpath)
            except:
                if options.get('debug'):
                    output.traceback()

                output.error("unable to remove '{}'".format(relpath))
                num_errors += 1

# make one more pass to remove any directories that are now empty
for dirpath, dirnames, filenames in os.walk(config_get_filepath('output_dir')):

    # skip any directories specified in the whitelist
    while True:
        for d in dirnames:
            dirname = os.path.join(dirpath, d)
            reldirname = os.path.relpath(dirname, config_get_filepath('output_dir'))

            if reldirname in whitelist:
                dirnames.remove(d)
                break
        else:
            break

    if len(filenames) == 0 and len(dirnames) == 0:
        try:
            if not options.get('dry_run'):
                os.rmdir(dirpath)
            output.removed('empty directory ' + dirpath)
        except:
            if options.get('debug'):
                output.traceback()

            output.error("unable to remove directory '{}'".format(dirpath))

try:
    if not options.get('dry_run'):
        write_cache(cache, config_get_filepath('cache_file'))
except:
    if options.get('debug'):
        output.traceback()

    output.error('could not write cache file')
    num_errors += 1

print('{} files published, {} files skipped, {} files removed; {} errors'.format(
    num_published, num_skipped, num_removed, num_errors
))
