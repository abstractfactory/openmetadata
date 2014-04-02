"""Generic objects used as baseclasses for datatype.py"""

from openmetadata_mk2 import service

EXT = '.'
SEP = '/'
CONTAINER = '.meta'


class Node(object):
    """
     ____
    |    |_______
    |            |
    |            |
    |            |
    |____________|

    Node represents a physical folder on disk.

    """

    def __str__(self):
        return self._path

    def __repr__(self):
        return u"%s(%r)" % (self.__class__.__name__, self.__str__())

    def __init__(self):
        self._isvalid = None

    @property
    def name(self):
        return self._path.split(EXT)[0]

    @property
    def path(self):
        suffix = ("." + self.suffix) if self.suffix else ''
        path = self.name + suffix

        root = self
        while hasattr(root, 'parent'):
            parent = root.parent

            if not parent:
                # The item has a parent attribute,
                # but no parent has been set.
                self._isvalid = False
                break

            path = service.join(parent.path, path)
            root = parent
            self._isvalid = True

        return path

    @property
    def isvalid(self):
        if self._isvalid is None:
            # Refresh path to ensure it is valid
            getattr(self, 'path')
        return self._isvalid


class MetaNode(Node):
    """
     ____
    |    |_______
    |            |
    |   __/_     |
    |    /       |
    |____________|

    MetaNode represents a metadata entry on disk (Group or Dataset)

    """

    @property
    def datatype(self):
        """
        Find datatype by looking in the object or its suffix
         _________         __________
        |         |       |          |
        |  cache  |  -->  |  suffix  |
        |_________|       |__________|

        """

        if not self._datatype:
            self._datatype = string_to_python(self.suffix)

        return self._datatype

    @property
    def suffix(self):
        """
        Find suffix, by looking in the object or path.
         _________         ________
        |         |       |        |
        |  cache  |  -->  |  path  |
        |_________|       |________|

        """

        if not self._suffix:
            self._suffix = (self._path.split(EXT) + [None])[1]

        return self._suffix


class Location(Node):
    """
    .    ____
    |   |    |
    +-- |____|
    |   .    ____
    |   |   |    |
    |   +-- |____|
    |   |   .    ____
    |   |   |   |    |
    |   |   +-- |____|

    A physical existing location

    """

    def __iter__(self):
        for child in self.children:
            yield child

    def __init__(self, path):
        super(Location, self).__init__()
        assert service.exists(path)
        self._children = {}
        self._path = path

    def copy(self, path=None):
        node = self.__class__(path or self._path)
        return node

    def add(self, child):
        if child.name in self._children:
            print "WARNING: %s was overwritten" % child.name
        self._children[child.name] = child

    @property
    def name(self):
        return self._path.split(EXT)[0]

    @property
    def data(self):
        return self._children.values()

    @property
    def path(self):
        return service.join(self._path, CONTAINER)

    @property
    def children(self):
        return self._children.values()


class Group(MetaNode):

    def __iter__(self):
        for child in self.children:
            yield child

    def __init__(self, path, parent=None):
        super(Group, self).__init__()
        self._path = path
        self._children = {}
        self._suffix = None
        self._datatype = None
        self.parent = parent

        if parent:
            parent.add(self)

    def add(self, child):
        if child.name in self._children:
            print "WARNING: %s was overwritten" % child.name
        self._children[child.name] = child

    @property
    def data(self):
        return self._children.values()

    @property
    def children(self):
        return self._children.values()


class Blob(MetaNode):
    """
     ______
    |       \
    |        |
    |        |
    |        |
    |________|

    """

    def __init__(self, path, data=None, parent=None):
        super(Blob, self).__init__()
        self._path = path
        self._data = None
        self._datatype = None  # cache
        self._suffix = None  # cache
        self.parent = parent

        # Toggled by om.pull and setattr(self.data)
        # Newly created nodes are clean until data
        # has been set.
        #
        # This is so that newly created nodes
        # without data won't get written to disk.
        self.isdirty = False

        if data is not None:
            self.data = data

        if parent:
            parent.add(self)

    @property
    def data(self):
        if self._data is None:
            return None
        return self.datatype(self._data)

    @data.setter
    def data(self, data):
        if data is None:
            self._data = data
            return

        if not self.datatype:
            self._datatype = data.__class__

        try:
            data = self.datatype(data)

        except TypeError:
            # Item has no type
            raise

        except ValueError:
            # Invalid data-type
            raise ValueError('Data-type %r, expected %r'
                             % (data.__class__.__name__,
                                self.datatype.__name__))

        self._data = data
        self.isdirty = True

    @property
    def suffix(self):
        """
        Find suffix, by looking in the object, path or data-type.
         _________         ________         _____________
        |         |       |        |       |             |
        |  cache  |  -->  |  path  |  -->  |  data-type  |
        |_________|       |________|       |_____________|

        """

        if not self._suffix:
            self._suffix = super(Blob, self).suffix

        if not self._suffix:
            self._suffix = python_to_string(type(self._data))

        return self._suffix

    def dump(self):
        """To dump a blob means to hardlink"""
        raise NotImplementedError


class Dataset(Blob):
    """
     ______
    |       \
    |        |
    |   om   |
    |        |
    |________|

    A Dataset is a Open Metadata-recognisable blob

    """

    def dump(self):
        """
        Dump Python data-type to disk, unless it is None,
        in which case dump nothing

        """

        return str(self.data) if self.data is not None else ''


"""

Open Metadata data-types

"""


class Bool(Dataset):
    pass


class Int(Dataset):
    pass


class Float(Dataset):
    pass


class String(Dataset):
    pass


class Text(Dataset):
    pass


class Date(Dataset):
    pass


class Null(Dataset):
    pass


class Enum(Group):
    pass


class Tuple(Group):
    pass


class List(Group):
    pass


class Dict(Group):
    pass


_python_to_om = {
    bool: Bool,
    int: Int,
    float: Float,
    str: String,
    None: Null,
    tuple: Tuple,
    list: List,
    dict: Dict
}


def python_to_om(obj):
    return _python_to_om.get(obj)


_string_to_om = {
    'bool': Bool,
    'int': Int,
    'float': Float,
    'string': String,
    'null': Null,
    'tuple': Tuple,
    'list': List,
    'dict': Dict
}


def om_to_string(obj):
    return obj.__name__.lower()


def string_to_om(obj):
    return _string_to_om.get(obj)


_python_to_string = {
    bool: 'bool',
    int: 'int',
    float: 'float',
    str: 'string',
    None: 'null',
    tuple: 'tuple',
    list: 'list',
    dict: 'dict'
}


def python_to_string(obj):
    return _python_to_string.get(obj)


def string_to_python(obj):
    _map = dict((v, k) for (k, v) in _python_to_string.items())
    return _map.get(obj)


"""

Factories

"""


class _FactoryBase(object):
    datatypes = {}
    default = None

    def __new__(cls, path, *args, **kwargs):
        suffix = service.suffix(path)
        Datatype = cls.datatypes.get(suffix) or cls.default
        return Datatype(path, *args, **kwargs)

    @classmethod
    def register(cls, datatype):
        cls.datatypes[datatype.__name__.lower()] = datatype

    @classmethod
    def unregister(cls, datatype):
        pass


class GroupFactory(_FactoryBase):
    datatypes = {}
    default = Group


class DatasetFactory(_FactoryBase):
    datatypes = {}
    default = Dataset


supported_datatypes = {
    'datasets': (
        Bool,
        Int,
        Float,
        String,
        Text,
        Date,
        Null
    ),
    'groups': (
        Enum,
        Tuple,
        List,
        Dict
    )
}


def register():
    for dataset in supported_datatypes['datasets']:
        DatasetFactory.register(dataset)

    for group in supported_datatypes['groups']:
        GroupFactory.register(group)


register()


"""

Database transation

"""


def precheck(item):
    if hasattr(item, 'children'):
        for child in item:
            precheck(child)
    else:
        if not item.isvalid:
            raise ValueError("%s was not valid" % item.path)


def dump(item):
    precheck(item)
    service.dump(item)


def read(path, *metapaths):
    """Parse information from database into Python data-types"""
    location = Location(path)

    root = location

    for metapath in metapaths:
        parts = metapath.split(SEP)
        while parts:
            pull(root)
            root = root._children.get(parts.pop(0))

            if not root:
                return None

    pull(root)
    return root.data


def write(path, data, *metapaths):
    """
    Convenience-method for quickly writing out `data` to `path`

    """

    location = Location(path)

    metapaths = list(metapaths)
    dataset = metapaths.pop()
    groups = metapaths
    root = location
    for group in groups:
        group = GroupFactory(group, parent=root)
        root = group

    # Is it a group or a dataset?
    item_type = python_to_om(type(data))
    # print item_type

    dataset = item_type(dataset, data=data, parent=root)
    print data
    service.dump(dataset)


def pull(item):
    """Read from disk"""
    # print "Pulling %s" % item.path
    if isinstance(item, Blob):
        item.data = service.readfile(item.path)
    else:
        dirs, files = service.readdir(item.path)

        for dir_ in dirs:
            GroupFactory(dir_, parent=item)

        for file_ in files:
            DatasetFactory(file_, parent=item)

    item.isdirty = False


def exists(item):
    return service.exists(item.path)


if __name__ == '__main__':
    import openmetadata_mk2 as om

    # Starting-point
    # location = om.Location(r'C:\Users\marcus\om2')

    # # Add a regular string
    # ostring = om.Dataset('simple_data.string', parent=location)
    # ostring.data = 'my simple string'

    # # Add a list
    # olist = om.Group('mylist.list', parent=location)

    # # Containing three datasets..
    # l1 = om.Dataset(path='item1.string', data='a string value', parent=olist)
    # l2 = om.Dataset(path='item2.bool', data=True, parent=olist)
    # l3 = om.Dataset(path='item3.int', data=5, parent=olist)

    # # ..and a dictionary..
    # odict = om.Group(path='mydict.dict', parent=olist)

    # # ..with two keys
    # key1 = om.Dataset('key1.string', data='value', parent=odict)

    # # One of which, we neglect to specify a data-type.
    # # The data-type will be determined via the Python data-type <str>
    # key2 = om.Dataset('key2', data=True, parent=odict)
    # print key2.path

    # Finally, write it to disk.
    # om.dump(location)

    # location = om.Location(r'C:\Users\marcus\om2')
    # om.pull(location)

    # mylist = location._children.get('mylist')
    # om.pull(mylist)

    # obool = mylist._children.get('item2')
    # om.pull(obool)
    # print repr(obool.data)

    # print mylist.data

    # simple = location._children.get('simple_data')
    # om.pull(simple)
    # print simple.data
    # # print simple.path

    # print om.read(r'c:\users\marcus\om2', 'simple_data')
    # print om.read(r'c:\users\marcus\om2', 'mylist/item4/key1')
    # print om.read(r'c:\users\marcus\om2', 'mylist', 'item4', 'key1')

    # location = om.Location(r'c:\users\marcus\om2')
    # dataset = om.Dataset('suffixless', parent=location)
    # dataset.data = 3.0
    # dataset.data = 'hello'
    # print dataset.datatype
    # print dataset.suffix
    # print dataset.path
    # om.dump(dataset)
    # om.dump(location)
    # path = r'c:\users\marcus\om2'
    # print om.read(path, 'story')
    # print om.read(path, 'mylist')
    # print om.read(path)
    # print om.listdir(path)
    # om.pull(child)
    # print type(child)
    # print child.data
    # print type(child.data)

    # print string_to_python('bool')

    # group = GroupFactory('test', parent=location)
    path = r'c:\users\marcus\om2'
    # om.write(path, True, 'parent/state')
    # om.write(path, 'There once was a boy', 'story')
    # om.write(path, 27, 'age')
    # om.write(path, 183.5, 'length')
    om.write(path, False, 'female')

    # print om.read(path, 'female')

    # for item in om.read(path):
    #     data = om.read(path, item.name)
    #     print "%s = %s <'%s'>" % (item.name, data, type(data).__name__)

    # print om.read(path)
    # assert not om.exists(dataset)
    # dataset.data = True
    # # dataset.data = 'string'
    # print dataset.path
    # # print dataset.datatype
    # print dataset.suffix

    # print omtype_from_pythonobj(True)

    # mylist = List('test.list')
    # print mylist.datatype

    location = om.Location(r'c:\users\marcus\om2')
    group = om.Group('parent', parent=location)
    print group.path
    # print group.isvalid
