import sys
import os

from six.moves import configparser

import presto.output as output


_conf = None                        # configparser.ConfigParser object
_ini_path = None                    # path to valid presto.ini file
_ini_containing_dir = None          # path of directory containing presto.ini


def load(path):
    global _conf, _ini_path, _ini_containing_dir

    _conf = configparser.ConfigParser({
        'html_extension': '.html'
    })

    if not _conf.read(path):
        output.error('could not read configuration file: {}'.format(path))
        sys.exit(1)

    else:
        if not _conf.has_section('presto'):
            output.error('presto.ini has no [presto] section, which is required')
            sys.exit(2)

        _ini_path = os.path.abspath(path)
        _ini_containing_dir = os.path.dirname(_ini_path)

        if not _conf.has_section('variables'):
            # adds empty section
            _conf.add_section('variables')


def get(name):
    if _conf is None:
        raise ValueError('configuration file is not loaded')

    if _conf.has_option('presto', name):
        return _conf.get('presto', name)


def set(name, value):
    if _conf is None:
        raise ValueError('configuration file is not loaded')

    _conf.set('presto', name, value)


def get_variables():
    if _conf is None:
        raise ValueError('configuration file is not loaded')

    return {k: _conf.get('variables', k) for k in _conf.options('variables')}


def get_ini_path():
    return _ini_path


def get_ini_containing_dir():
    return _ini_containing_dir


def get_filepath(name):
    """Return the absolute path to a file referenced in the configuration file.
    This function gets the file's defined path from the configuration file. If
    the defined path is not an absolute path, it makes the path absolute by
    prepending the path of the containing directory of presto.ini. Like get(),
    this function returns None if the specified value is not in presto.ini.
    """
    if _conf is None:
        raise ValueError('configuration file is not loaded')

    filepath = get(name)

    if filepath is None:
        return None

    elif os.path.isabs(filepath):
        return filepath

    else:
        # path should be taken as relative to containing directory of presto.ini
        return os.path.join(_ini_containing_dir, filepath)
