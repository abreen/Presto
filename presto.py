import os
import sys
import hashlib
from string import Template
import datetime

import markdown
import mdx_grid_tables
import decomment

DRAFTS_DIR = 'drafts'
OUTPUT_DIR = '..'
TEMPLATE = 'template.html'
CACHE_FILE = 'presto-cache'         # for keeping hashes of drafts


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


def main():
    args = {'extensions': ['def_list', 'footnotes', 'meta', 'smarty',
                           'headerid', mdx_grid_tables.GridTableExtension()],
            'extension_configs': {'smarty': [('smart_ellipses', False)]},
            'output_format': 'html5',
            'safe_mode': False,         # HTML passes through unaltered
            'lazy_ol': False}

    md = markdown.Markdown(**args)
    templ = Template(open(TEMPLATE).read())
    today = datetime.datetime.now().strftime("%B %e, %Y")

    cache = get_cache()
    num_published = 0

    for dirpath, dirnames, filenames in os.walk(DRAFTS_DIR):
        for f in filenames:
            if '.markdown' not in f: continue   # ignore all non-Markdown files
            if f[0] == '.': continue            # ignore dotfiles

            path = os.path.join(dirpath, f)
            infile = open(path, mode='r', encoding='utf-8')

            hash = compute_hash(infile)
            if path not in cache:
                pprint("{} not in cache; publishing".format(path))
                cache[path] = hash
            elif cache[path] == hash:
                # no change to this file since last time
                continue
            else:
                # file changed since last time; update cache
                pprint("{} changed; publishing".format(path))
                cache[path] = hash

            body = decomment.decomment(infile.read())
            body_html = md.convert(body)

            if 'title' not in md.Meta:
                pprint("{} has no title".format(path), error=True)

                # invalidate cache so this file is not skipped next time
                cache[path] = 'error'
                continue

            html = templ.safe_substitute(body=body_html,
                                         title=md.Meta['title'][0],
                                         date=today)

            # create path to OUTPUT_DIR
            parts = path.replace('.markdown', '.html').split(os.sep)
            output_path = OUTPUT_DIR + os.sep + os.sep.join(parts[1:])

            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with open(output_path, mode='w') as of:
                of.write(html)

            num_published += 1
            pprint("wrote {}".format(output_path))

            md.reset()

    write_cache(cache)
    pprint("{} published".format(num_published))


if __name__ == '__main__':
    main()
