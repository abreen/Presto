import sys

from six.moves import configparser

import presto.output as output


_conf = configparser.ConfigParser()

if not _conf.read('presto.ini'):
    output.error('could not find presto.ini')
    sys.exit(1)

elif not _conf.has_section('presto'):
    output.error('presto.ini has no [presto] section, which is required')
    sys.exit(2)


def get(name):
    if _conf.has_option('presto', name):
        return _conf.get('presto', name)

def set(name, value):
    _conf.set('presto', name, value)
