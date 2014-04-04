import logging

from openmetadata import error
from openmetadata.api import *
from openmetadata.version import *


def get_formatter():
    formatter = logging.Formatter(
        '%(asctime)s - '
        '%(levelname)s - '
        '%(name)s - '
        '%(message)s',
        '%Y-%m-%d %H:%M:%S')
    return formatter


def setup_log(root):
    log = logging.getLogger(root)
    # log.setLevel(logging.DEBUG)
    log.setLevel(logging.INFO)
    # log.setLevel(logging.WARNING)

    formatter = get_formatter()
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    log.addHandler(stream_handler)

    return log

setup_log('openmetadata')

"""
Usage
    >>> import openmetadata as om
    >>> om.version
    '0.1.0'
    >>> om.version_info
    (0, 1, 0)
    >>> om.version_info > (0, 2, 0)
    False

"""

if __name__ == '__main__':
    import doctest
    doctest.testmod()
