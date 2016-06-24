import sys

from six.moves import configparser

from presto.output import error


_conf = configparser.ConfigParser()
_conf.read('presto.ini')

if not _conf.has_section('presto'):
    error('presto.ini could not be found, or no [presto] section found')

def get(var):
    return _conf.get('presto', var)
