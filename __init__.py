"""Open Metadata API"""

from . import lib
from . import error
from . import service

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
