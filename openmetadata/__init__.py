"""
-----------------------------------------------------------------------

Open Metadata API

-----------------------------------------------------------------------

Description
    The Open Metadata technology is designed to organize, store,
    discover, access, analyze, share, and preserve diverse, complex
    data in continuously evolving heterogeneous computing and
    storage environments.

    The implementation you are reading about right now is LGPLv3
    licensed software, however Open Metadata itself is language- and
    implementation-agnostic and may come to support several other
    languages.

Functionality

    Main
    ----------------------

    flush           -- Write to database
    remove          -- Remove from database
    find            -- Return first match
    pull            -- Read from database
    inherit         -- Read cascading from database

    Convenience
    ----------------------

    read            -- Convenience method for reading metadata
    write           -- Convenience method for writing metadata
    ls              -- List metacontent of node


Usage

    >> import openmetadata as om
    >> om.read('/home/marcus')

Version

    >>> import openmetadata as om
    >>> om.version
    '0.1.0'
    >>> om.version_info
    (0, 1, 0)
    >>> om.version_info > (0, 2, 0)
    False


"""


import logging

# from openmetadata import lib
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


def setup_log(root=None, level=None):
    root = root or 'openmetadata'
    log = logging.getLogger(root)

    if not level:
        # log.setLevel(logging.DEBUG)
        log.setLevel(logging.INFO)
        # log.setLevel(logging.WARNING)
    else:
        log.setLevel(level)

    formatter = get_formatter()
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    log.addHandler(stream_handler)

    return log

# log = setup_log('openmetadata')

if __name__ == '__main__':
    import doctest
    doctest.testmod()
