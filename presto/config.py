import sys

from six.moves import configparser

import presto.output as output


_conf = None


def load(path=None):
    global _conf

    _conf = configparser.ConfigParser()

    if path is None:
        path = 'presto.ini'

    if not _conf.read(path):
        output.error('could not find presto.ini')
        sys.exit(1)
    else:
        if not _conf.has_section('presto'):
            output.error('presto.ini has no [presto] section, which is required')
            sys.exit(2)

        if not _conf.has_section('variables'):
            _conf.add_section('variables')


def get(name):
    if _conf is None:
        raise ValueError('config file is not loaded')

    if _conf.has_option('presto', name):
        return _conf.get('presto', name)


def set(name, value):
    if _conf is None:
        raise ValueError('config file is not loaded')

    _conf.set('presto', name, value)


def get_variables():
    if _conf is None:
        raise ValueError('config file is not loaded')

    return {k: _conf.get('variables', k) for k in _conf.options('variables')}
