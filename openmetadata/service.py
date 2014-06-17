"""File-system services"""

import os
import time
import shutil
import __builtin__

from openmetadata import error

SEP = os.sep
OSNAME = os.name


def isabsolute(path):
    return os.path.isabs(path)


def isdir(path):
    return os.path.isdir(path)


def isfile(path):
    return os.path.isfile(path)


def currenttime():
    return time.strftime("%Y%m%d-%H%M%S", time.gmtime())


def suffix(path):
    return os.path.splitext(path)[1][1:]


def basename(path):
    return os.path.basename(path)


def exists(path, **kwargs):

    # Hidden arguments
    ignore_case = kwargs.get('ignore_case', True)

    if ignore_case:
        path = path.lower()

    return os.path.exists(path)


# def split(path, *args, **kwargs):
#     return os.path.split(path, *args, **kwargs)


def count(path):
    """Return amount of items under `path`"""
    return len(os.listdir(path))


def parent(path):
    parent = os.path.dirname(path)

    # Once we reach the highest parent (c-drive on Windows)
    # dirname continuously returns it.
    if parent == path:
        return None

    return parent


def remove(path):
    """
    Remove `path`, regardless of it being a file or folder.

    """

    if os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.isfile(path):
        os.remove(path)
    else:
        raise TypeError("%s is not a valid path" % path)


def move(source, target):
    """
    Move `source` to `target`, creating missing
    parts of the hierarchy is required.

    """

    dirname = os.path.dirname(target)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    shutil.move(source, target)


def copy(source, target):
    """
    Move `source` to `target`, creating missing
    parts of the hierarchy is required.

    """

    dirname = os.path.dirname(target)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    shutil.copy2(source, target)


def commit(node):
    """Stage `node`"""


def push():
    """Retrieve commited data and flush it"""


def ls(path):
    """Retrieve remotely-stored data"""
    if not os.path.exists(path):
        raise error.Exists(path)
    for _, dirs, files in os.walk(path):
        return dirs, files


def open(path):
    with __builtin__.open(path, 'r') as f:
        data = f.read()
    return data


def flush(path, data):
    dirname = os.path.dirname(path)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    with __builtin__.open(path, 'w') as f:
        f.write(data)

    return True


def flush_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
    return True


if __name__ == '__main__':
    pass
