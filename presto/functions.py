"""Functions that are available for use when evaluating code inside {% ... %}
blocks found in Markdown drafts. When a function is called, the Python
interpreter's standard out stream is redirected to the Markdown file.
"""
from __future__ import print_function, with_statement

import sys
import os

import presto.config as config


def include_draft(path):
    with open(config.get('markdown_dir') + os.sep + path, 'r') as f:
        content = f.read().strip()

    content = content.split('\n')

    for i, line in enumerate(content):
        if line == '':
            break

    rest = content[i + 1:]
    print('\n'.join(rest), end='')


def include_partial(path):
    with open(config.get('partials_dir') + os.sep + path, 'r') as f:
        print(f.read().strip(), end='')


def shell(func, args=None, kwargs=None, prompt='>>> ', followup=True):
    """Given a function, a list of arguments to the function (if any), a dict
    of keyword arguments (if any), print a string representing the function
    call and its return value, as it would appear on the Python REPL. This is
    intended for use in a {% ... %} sequence, since the standard out of such
    sequences are sent to the page.
    """
    if not args:
        args = []

    if not kwargs:
        kwargs = {}

    call_str = func.__name__ + '('
    call_str += ', '.join(map(repr, args))
    call_str += ', '.join([str(k) + '=' + repr(v) for k, v in kwargs.items()])
    call_str += ')'

    print(prompt + call_str)

    rv = func(*args, **kwargs)

    if rv is not None:
        print(repr(rv))

    if followup:
        print(prompt)
