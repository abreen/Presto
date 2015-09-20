import sys

sys.path.append('lib')

import os
import stat
import configparser
import hashlib
from string import Template
import datetime

import markdown
import mdx_grid_tables
import pygments
import bleach

ALLOWED_TAGS = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol',
                'strong', 'ul', 'img', 'table', 'thead', 'tbody', 'tr', 'td', 'th', 'div',
                'span', 'p', 'tt', 'pre', 'figure', 'caption', 'h1', 'h2', 'h3', 'h4', 'h5',
                'h6', 'dd', 'dt', 'dl', 'br', 'hr']
ALLOWED_ATTRIBUTES = {
    '*': ['title', 'class', 'name', 'id'],
    'a': ['href', 'target'],
    'img': ['src', 'alt'],
}

def main():
    conf = configparser.ConfigParser()
    conf.read('presto.ini')

    if 'presto' not in conf:
        pprint('presto.ini could not be found, or no [presto] section found',
               error=True)
        sys.exit(1)

    markdown_dir = conf['presto']['markdown_dir']
    output_dir = conf['presto']['output_dir']
    template_file = conf['presto']['template_file']
    cache_file = conf['presto']['cache_file']

    os.umask(0o002)

    args = {'extensions': ['def_list', 'footnotes', 'meta', 'smarty',
                           'headerid', 'tables', 'codehilite',
                           'admonition', 'toc',
                           mdx_grid_tables.GridTableExtension()],
            'extension_configs': {'smarty': [('smart_ellipses', False)]},
            'output_format': 'html5',
            'lazy_ol': False}

    md = markdown.Markdown(**args)
    templ = Template(open(template_file).read())
    today = datetime.datetime.now().strftime("%B %e, %Y")
    footer = "Last modified on " + today + "."

    num_published, num_errors, num_skipped, num_removed = 0, 0, 0, 0

    try:
        cache = get_cache(cache_file)
    except:
        pprint("could not open cache file", error=True)
        cache = {}
        num_errors +=1

    expected_files = []

    for dirpath, dirnames, filenames in os.walk(markdown_dir):
        for f in filenames:
            if '.markdown' not in f and f != 'htaccess':
                continue

            if f[0] in ['.', '#']:
                continue

            if f[-1] == '~':
                continue

            path = os.path.join(dirpath, f)

            if executable(path):
                expected_files.append(path)

            try:
                infile = open(path, mode='r', encoding='utf-8')
            except PermissionError:
                pprint("insufficient permission to read "
                       "draft '{}'".format(f), error=True)
                num_errors += 1
                continue

            hash = compute_hash(infile)

            if path not in cache or cache[path] != hash:
                if executable(path):
                    cache[path] = hash
                else:
                    num_skipped += 1
                    continue
            else:
                # no change to this file since last time
                continue

            if f == 'htaccess':
                if not copy_htaccess(path, output_dir):
                    num_errors += 1
                else:
                    num_published += 1
                continue

            cleaned = bleach.clean(infile.read(), ALLOWED_TAGS, ALLOWED_ATTRIBUTES)
            body_html = md.convert(cleaned)

            if 'title' not in md.Meta:
                pprint("{} has no title".format(path), error=True)

                # invalidate cache so this file is not skipped next time
                cache[path] = 'bad-metadata'
                num_errors += 1
                continue

            html = templ.safe_substitute(body=body_html,
                                         title=md.Meta['title'][0],
                                         footer=footer)

            # create path to output directory
            parts = path.replace('.markdown', '.html').split(os.sep)
            output_path = output_dir + os.sep + os.sep.join(parts[1:])

            try:
                makedirs(os.path.dirname(output_path))
            except:
                pprint("could not make directories "
                       "for '{}'".format(output_path),
                       error=True)
                cache[path] = 'dirs-failed'
                num_errors += 1
                continue

            try:
                with open(output_path, mode='w') as of:
                    of.write(html)
            except:
                pprint("could not write output file "
                       "'{}'".format(output_path),
                       error=True)
                cache[path] = 'write-failed'
                num_errors += 1
                continue

            num_published += 1
            pprint("published '{}'".format(output_path))

            md.reset()

    # done publishing all HTML
    # now remove the HTML files for non-existent Markdown
    for dirpath, dirnames, filenames in os.walk(output_dir):
        for f in filenames:
            if f[0] == '.' and f != '.htaccess':
                continue

            path = os.path.join(dirpath, f)

            orig_base = os.path.join(
                            markdown_dir,
                            os.sep.join(dirpath.split(os.sep)[1:])
                        )

            if f == '.htaccess':
                orig_path = os.path.join(orig_base, 'htaccess')
            else:
                orig_path = os.path.join(orig_base, f.replace('.html', '.markdown'))

            if orig_path not in expected_files:
                if orig_path in cache:
                    del cache[orig_path]

                os.remove(os.path.join(dirpath, f))
                num_removed += 1
                print("removed '{}'".format(path))

    # make one more pass to remove any directories that are now empty
    for dirpath, dirnames, filenames in os.walk(output_dir):
        if len(filenames) == 0 and len(dirnames) == 0:
            os.rmdir(os.path.join(dirpath))
            print("removed empty directory '{}'".format(dirpath))

    try:
        write_cache(cache, cache_file)
    except:
        pprint("could not write cache file", error=True)
        num_errors += 1

    pprint("{} published, {} errors, {} skipped, {} removed".format(
        num_published, num_errors, num_skipped, num_removed
    ))


def pprint(s, error=False):
    if error:
        print("presto: error: " + s, file=sys.stderr)
    else:
        print("presto: " + s, file=sys.stdout)


def get_cache(cache_file):
    cache = {}

    if not os.path.isfile(cache_file):
        return cache

    with open(cache_file, mode='r') as f:
        for line in f:
            tokens = line.split()
            cache[tokens[0]] = tokens[1]

    return cache


def write_cache(cache, cache_file):
    with open(cache_file, mode='w') as f:
        for (k, v) in cache.items():
            f.write("{}\t{}\n".format(k, v))


def compute_hash(file):
    h = hashlib.md5()

    for line in file:
        h.update(line.encode('utf-8'))

    file.seek(0)
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


def executable(f):
    s = os.stat(f)
    return s.st_mode & stat.S_IXUSR


def copy_htaccess(path, output_dir):
    old_umask = os.umask(0o002)

    parts = path.split(os.sep)
    parts[-1] = '.htaccess'
    output_path = output_dir + os.sep + os.sep.join(parts[1:])

    try:
        makedirs(os.path.dirname(output_path))
    except:
        pprint("could not make directories "
               "for htaccess file '{}'".format(output_path),
               error=True)
        os.umask(old_umask)
        return False

    was_here = os.path.isfile(output_path)

    try:
        with open(path, mode='r') as htfile:
            with open(output_path, mode='w') as of:
                of.write(htfile.read())
    except:
        pprint("could not write htaccess file "
               "'{}'".format(output_path), error=True)
        os.umask(old_umask)
        return False

    if not was_here:
        st = os.stat(output_path)
        os.chmod(output_path, st.st_mode | stat.S_IXGRP | stat.S_IXOTH)

    os.umask(old_umask)
    return True


if __name__ == '__main__':
    main()
