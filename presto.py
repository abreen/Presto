#!/usr/bin/env python3

import sys

sys.path.append('lib')

import os
import stat
import configparser
import hashlib
from string import Template
import datetime
import re

import markdown
import mdx_grid_tables
import pygments

COMMENT_PATTERN = re.compile(r'(<!--.*?-->)', re.DOTALL)

def main():
    conf = configparser.ConfigParser()
    conf.read('presto.ini')

    if 'presto' not in conf:
        error('presto.ini could not be found, or no [presto] section found')
        sys.exit(1)

    markdown_dir = conf['presto']['markdown_dir']
    output_dir = conf['presto']['output_dir']
    template_file = conf['presto']['template_file']
    cache_file = conf['presto']['cache_file']
    whitelist = conf['presto']['whitelist']

    # post-process the whitelist: split on commas and remove extra spaces
    whitelist = [s.strip() for s in whitelist.split(',')]

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
        error('could not open cache file')
        cache = {}
        num_errors += 1

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
            relpath = os.path.relpath(path, markdown_dir)

            if executable(path):
                expected_files.append(relpath)
            else:
                if relpath in cache:
                    del cache[relpath]

            try:
                infile = open(path, mode='r', encoding='utf-8')
            except PermissionError:
                error("insufficient permission to read '{}'".format(relpath))
                num_errors += 1
                continue

            hash = compute_hash(infile)

            if relpath not in cache or cache[relpath] != hash:
                if executable(path):
                    cache[relpath] = hash
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

            content = infile.read()
            cleaned = re.sub(COMMENT_PATTERN, '', content)
            body_html = md.convert(cleaned)

            if 'title' not in md.Meta:
                error('{} has no title'.format(relpath))

                # invalidate cache so this file is not skipped next time
                cache[relpath] = 'bad-metadata'
                num_errors += 1
                continue

            html = templ.safe_substitute(
                body=body_html,
                title=md.Meta['title'][0],
                footer=footer
            )

            # create path to output directory
            output_path = os.path.join(
                output_dir,
                relpath.replace('.markdown', '.html')
            )

            try:
                makedirs(os.path.dirname(output_path))
            except:
                error("cannot make directories for '{}'".format(relpath))
                cache[relpath] = 'dirs-failed'
                num_errors += 1
                continue

            try:
                with open(output_path, mode='w') as of:
                    of.write(html)
            except:
                error("cannot write output file '{}'".format(relpath))
                cache[relpath] = 'write-failed'
                num_errors += 1
                continue

            num_published += 1
            published(relpath)

            md.reset()

    # done publishing all HTML
    # now remove the HTML files for non-existent Markdown
    for dirpath, dirnames, filenames in os.walk(output_dir):

        # skip any directories specified in the whitelist
        while True:
            for d in dirnames:
                dirname = os.path.join(dirpath, d)
                reldirname = os.path.relpath(dirname, output_dir)

                if reldirname in whitelist:
                    dirnames.remove(d)
                    break
            else:
                break

        for f in filenames:
            if f[0] == '.' and f != '.htaccess':
                continue

            path = os.path.join(dirpath, f)
            relpath = os.path.relpath(path, output_dir)

            head, tail = os.path.split(relpath)
            if f == '.htaccess':
                relpath = os.path.join(head, 'htaccess')
            else:
                relpath = os.path.join(head, f.replace('.html', '.markdown'))

            if relpath not in expected_files:
                if relpath in cache:
                    del cache[relpath]

                try:
                    os.remove(path)
                    num_removed += 1
                    removed(relpath)
                except PermissionError:
                    error("insufficient permissions removing '{}'".format(relpath))
                    num_errors += 1

    # make one more pass to remove any directories that are now empty
    for dirpath, dirnames, filenames in os.walk(output_dir):

        # skip any directories specified in the whitelist
        while True:
            for d in dirnames:
                dirname = os.path.join(dirpath, d)
                reldirname = os.path.relpath(dirname, output_dir)

                if reldirname in whitelist:
                    dirnames.remove(d)
                    break
            else:
                break

        if len(filenames) == 0 and len(dirnames) == 0:
            try:
                os.rmdir(dirpath)
                removed('empty directory ' + reldirname)
            except PermissionError:
                error("insufficient permissions removing directory '{}'".format(reldirname))

    try:
        write_cache(cache, cache_file)
    except:
        error('could not write cache file')
        num_errors += 1

    print('{} published, {} errors, {} skipped, {} removed'.format(
        num_published, num_errors, num_skipped, num_removed
    ))


def error(msg):
    print('\033[31merror:\033[0m', msg, file=sys.stderr)


def published(msg):
    print('\033[32m[published]\033[0m', msg)


def removed(msg):
    print('\033[35m[removed]\033[0m', msg)


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
            print("created directory '{}'".format(dirpath))


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
        error("cannot make directories for htaccess '{}'".format(output_path))
        os.umask(old_umask)
        return False

    was_here = os.path.isfile(output_path)

    try:
        with open(path, mode='r') as htfile:
            with open(output_path, mode='w') as of:
                of.write(htfile.read())
    except:
        error("could not create htaccess '{}'".format(output_path))
        os.umask(old_umask)
        return False

    if not was_here:
        st = os.stat(output_path)
        os.chmod(output_path, st.st_mode | stat.S_IXGRP | stat.S_IXOTH)

    os.umask(old_umask)
    print("created htaccess file '{}'".format(output_path))
    return True


if __name__ == '__main__':
    main()
