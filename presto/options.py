import sys
import argparse


_parser = argparse.ArgumentParser()
_parser.add_argument(
    '-e', '--use-empty',
    action='store_true',
    help='use empty string for {-sequences that produce errors'
)
_parser.add_argument(
    '--debug',
    action='store_true',
    help='print tracebacks when exceptions occur, for debugging'
)

_args = vars(_parser.parse_args())


def get(name):
    if name in _args:
        return _args[name]
