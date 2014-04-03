"""service.py is responsible for interacting with the operating system"""

import os
import shutil
import time


def suffix(path):
    return os.path.splitext(path)[1][1:]


def exists(path):
    return os.path.exists(path)


def remove(path):
    if exists(path):
        dirname = os.path.dirname(path)
        basename = os.path.basename(path)
        trash = os.path.join(dirname, '.trash')

        if not os.path.exists(trash):
            os.mkdir(trash)

        deleted_time = time.strftime("%Y%m%d%H%M%S", time.gmtime())
        deleted_basename = "%s&%s" % (basename, deleted_time)
        deleted_path = os.path.join(trash, deleted_basename)

        try:
            shutil.move(path, deleted_path)
        except WindowsError:
            raise

        print "Successfully removed %s" % path

    else:
        print "%s did not exist" % path

    return True


def load(path):
    """Retrieve locally-stored data"""


# def loads(path):
#     """Retrieve data from memory"""


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


def dump(node):
    if hasattr(node, 'children'):
        os.makedirs(node.path)
        for child in node:
            dump(child)
    else:
        dataset = node

        path = dataset.path
        directory, file_ = os.path.split(path)
        if not os.path.exists(directory):
            os.makedirs(directory)

        with open(path, 'w') as f:
            f.write(dataset.dump())

        print "Successfully wrote: %s" % path


def dumps(node):
    root = {}

    if hasattr(node, 'children'):
        for child in node:
            root[child.name] = dumps(child)
    else:
        root = node.data

    return root


join = os.path.join



if __name__ == '__main__':
    pass