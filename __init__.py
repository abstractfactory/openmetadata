
from openmetadata_mk2 import lib
from openmetadata_mk2 import error
from openmetadata_mk2 import service
from openmetadata_mk2.version import *

"""
Usage
    >>> import openmetadata_mk2 as om
    >>> om.version
    '0.1.0'
    >>> om.version_info
    (0, 1, 0)
    >>> om.version_info > (0, 2, 0)
    False

"""

# API

Node = lib.Node
Location = lib.Location
Group = lib.GroupFactory
Dataset = lib.DatasetFactory

# load = service.load
# loads = service.loads
read = lib.read
write = lib.write
pull = lib.pull
# commit = service.commit
exists = lib.exists
dump = lib.dump
dumps = service.dumps
remove = lib.remove

listdir = read
walk = lambda: 'whoot'


def isdataset(item):
    return True if isinstance(item, lib.Dataset) else False


def isgroup(item):
    return True if isinstance(item, lib.Group) else False


if __name__ == '__main__':
    import doctest
    doctest.testmod()
