"""Functions that are available for use when evaluating code inside {-sequences
found in Markdown drafts.
"""
from __future__ import print_function, with_statement

import sys
import os

import presto.config as config


def draft(path):
    with open(config.get('markdown_dir') + os.sep + path, 'r') as f:
        content = f.read().strip()

    content = content.split('\n')

    for i, line in enumerate(content):
        if line == '':
            break

    rest = content[i + 1:]
    return '\n'.join(rest)


def partial(path):
    with open(config.get('partials_dir') + os.sep + path, 'r') as f:
        return f.read().strip()


def shell(func, args=None, kwargs=None, prompt='>>> ', followup=True):
    """Given a function, a list of arguments to the function (if any), a dict
    of keyword arguments (if any), return a string representing the function
    call and its return value, as it would appear on the Python REPL.
    """
    if not args:
        args = []

    if not kwargs:
        kwargs = {}

    s = ''

    call_str = func.__name__ + '('
    call_str += ', '.join(map(repr, args))
    call_str += ', '.join([str(k) + '=' + repr(v) for k, v in kwargs.items()])
    call_str += ')'

    s += prompt + call_str + '\n'

    rv = func(*args, **kwargs)

    if rv is not None:
        s += repr(rv) + '\n'

    if followup:
        s += prompt + '\n'

    return s
