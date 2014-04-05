"""File-system services"""

import os
import time
import shutil

SEP = os.sep


def isabsolute(path):
    return os.path.isabs(path)


def currenttime():
    return time.strftime("%Y%m%d-%H%M%S", time.gmtime())


def suffix(path):
    return os.path.splitext(path)[1][1:]


def exists(path):
    return os.path.exists(path)


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


def push():
    """Retrieve locally-stored data and dump it"""


def readdir(path):
    """Retrieve remotely-stored data"""
    for _, dirs, files in os.walk(path):
        return dirs, files


def readfile(path):
    with open(path, 'r') as f:
        data = f.read()
    return data


def commit(node):
    """Temporarily store `node` on the local hard-drive"""
    pass


def dump(path, data):
    dirname = os.path.dirname(path)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    with open(path, 'w') as f:
        f.write(data)

    return True



if __name__ == '__main__':
    pass