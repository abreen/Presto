import os
import stat
import sys
import hashlib
from string import Template
import datetime

import markdown
import mdx_grid_tables
import pygments
import bleach

DRAFTS_DIR = 'drafts'
OUTPUT_DIR = 'output'
PRESTO_DIR = os.getcwd()
TEMPLATE = PRESTO_DIR + '/template.html'
CACHE_FILE = PRESTO_DIR + '/cache'
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
    os.umask(0o002)

    args = {'extensions': ['def_list', 'footnotes', 'meta', 'smarty',
                           'headerid', 'tables', 'codehilite',
                           'admonition', 'toc',
                           mdx_grid_tables.GridTableExtension()],
            'extension_configs': {'smarty': [('smart_ellipses', False)]},
            'output_format': 'html5',
            'lazy_ol': False}

    md = markdown.Markdown(**args)
    templ = Template(open(TEMPLATE).read())
    today = datetime.datetime.now().strftime("%B %e, %Y")
    footer = "Last modified on " + today + "."

    num_published, num_errors, num_skipped = 0, 0, 0

    try:
        cache = get_cache()
    except:
        pprint("could not open cache file", error=True)
        cache = {}
        num_errors +=1

    for dirpath, dirnames, filenames in os.walk(DRAFTS_DIR):
        for f in filenames:
            if '.markdown' not in f and f != 'htaccess':
                continue

            if f[0] in ['.', '#']:
                continue

            if f[-1] == '~':
                continue

            path = os.path.join(dirpath, f)
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
                    pprint("publishing '{}'".format(path))
                    cache[path] = hash
                else:
                    pprint("skipping '{}': "
                           "execute bit not set".format(f))
                    num_skipped += 1
                    continue
            else:
                # no change to this file since last time
                continue

            if f == 'htaccess':
                if not copy_htaccess(path):
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

            # create path to OUTPUT_DIR
            parts = path.replace('.markdown', '.html').split(os.sep)
            output_path = OUTPUT_DIR + os.sep + os.sep.join(parts[1:])

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
            pprint("wrote {}".format(output_path))

            md.reset()

    try:
        write_cache(cache)
    except:
        pprint("could not write cache file", error=True)
        num_errors +=1

    pprint("{} published ({} errors, "
           "{} skipped)".format(num_published, num_errors, num_skipped))


def pprint(s, error=False):
    if error:
        print("presto: error: " + s, file=sys.stderr)
    else:
        print("presto: " + s, file=sys.stdout)


def get_cache():
    cache = {}

    if not os.path.isfile(CACHE_FILE):
        return cache

    with open(CACHE_FILE, mode='r') as f:
        for line in f:
            tokens = line.split()
            cache[tokens[0]] = tokens[1]

    return cache


def write_cache(cache):
    with open(CACHE_FILE, mode='w') as f:
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


def copy_htaccess(path):
    old_umask = os.umask(0o002)

    parts = path.split(os.sep)
    parts[-1] = '.htaccess'
    output_path = OUTPUT_DIR + os.sep + os.sep.join(parts[1:])

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
