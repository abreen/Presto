import sys

from six.moves import configparser


_conf = configparser.ConfigParser()

if _conf.read('presto.ini') and not _conf.has_section('presto'):
    error('presto.ini could not be found, or no [presto] section found')
    _conf.add_section('presto')


def get(name):
    if _conf.has_option('presto', name):
        return _conf.get('presto', name)

def set(name, value):
    _conf.set('presto', name, value)
