from __future__ import print_function

import sys


def error(msg):
    print('\033[31merror:\033[0m', msg, file=sys.stderr)


def published(msg):
    print('\033[32m[published]\033[0m', msg)


def removed(msg):
    print('\033[35m[removed]\033[0m', msg)


def skipped(msg):
    print('\033[36m[skipped]\033[0m', msg)
