"""service.py is responsible for interacting with the operating system"""

import os


def suffix(path):
    return os.path.splitext(path)[1][1:]


def exists(path):
    return os.path.exists(path)


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


def commit(item):
    """Temporarily store `item` on the local hard-drive"""
    pass


def dump(item):
    if hasattr(item, 'children'):
        for child in item:
            dump(child)
    else:
        dataset = item

        path = dataset.path
        directory, file_ = os.path.split(path)
        if not os.path.exists(directory):
            os.makedirs(directory)

        with open(path, 'w') as f:
            f.write(dataset.dump())

        print "Successfully wrote: %s" % path


def dumps(item):
    root = {}

    if hasattr(item, 'children'):
        for child in item:
            root[child.name] = dumps(child)
    else:
        root = item.data

    return root


join = os.path.join


if __name__ == '__main__':
    pass