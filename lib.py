import abc
import json
import logging

from openmetadata import service
from openmetadata import error
from openmetadata import path
# from openmetadata import bug

HISTORY = '.history'
VERSIONS = '.versions'
TRASH = '.trash'

LOG = logging.getLogger('openmetadata.lib')

osname = service.OSNAME
path_map = {'nt': path.WindowsPath,
            'posix': path.PosixPath}
Path = path_map[osname]


class Node(object):
    """
     ____
    |    |_______
    |            |
    |            |
    |            |
    |____________|

    A node represents an entry in a database

    """

    __metaclass__ = abc.ABCMeta

    default_value = None

    def __iter__(self):
        for child in self.children:
            yield child

    def __getitem__(self, item):
        try:
            return self._children[item]
        except KeyError:
            raise KeyError("%r not in %r"
                           % (item, self))

    def __contains__(self, key):
        return key in self._children

    def __str__(self):
        return self.path.name

    def __repr__(self):
        return u"%s(%r)" % (self.__class__.__name__, self.__str__())

    def __eq__(self, other):
        """
        Nodes within a single parent all have unique names.
        If a name is not unique, there is a bug.

        """
        return str(other) == str(self)

    def __ne__(self, other):
        return str(other) != str(self)

    def __hash__(self):
        return hash(str(self))

    def __children__(self):
        return self._children

    @abc.abstractmethod  # Prevent direct instantiation
    def __init__(self, path, data=None, parent=None):
        if isinstance(path, basestring):
            path = Path(path)

        self._path = path
        self._type = None  # cache
        self._suffix = None  # cache
        self._isvalid = None

        self._children = {}
        self._data = data
        self._parent = parent

        if data is not None:
            self.data = data

        if parent:
            parent.add(self)

    @property
    def relativepath(self):
        return self._path

    @property
    def path(self):
        path = self.relativepath

        if hasattr(self, 'parent'):
            parent = self.parent

            if not parent:
                # The node has a parent attribute,
                # but no parent has been set.
                self._isvalid = False
                return path

            parent_path = parent.path
            if hasattr(parent, 'resolved_path'):
                parent_path = parent.resolved_path

            path = parent_path + path
            self._isvalid = True

        return path

    @property
    def location(self):
        """Return location of `self`

        Note that the location is the top-most parent
        of metadata and may not be equivalent to the
        result of .parent

        This is primarily a convenience property.

        """

        return Location(self.path.location)

    @property
    def type(self):
        """
        Find type by looking in the object or its suffix
         _________         _______________
        |         |       |               |
        |  cache  |  -->  |  path.suffix  |
        |_________|       |_______________|

        """

        if not self._type:
            self._type = string_to_python(self.path.suffix)

        return self._type

    def add(self, child):
        path = child.relativepath
        key = path.name

        if path.hasoption:
            key += path.OPTIONDIV + path.option

        if key in self._children:
            self.LOG.warning("%s was overwritten" % child.path)

        self._children[key] = child

    def copy(self, path=None, data=None):
        path = path or self.relativepath
        data = data = self._data

        copy = self.__class__(path, data)
        copy._parent = self._parent

        return copy

    def clear(self):
        """Remove existing data/children"""
        while self._children:
            self._children.popitem()

        self._data = None

    def ls(self):
        """List contained children"""
        print self.path.name
        for node in self:
            print '\t' + node.path.name

    @property
    def children(self):
        for name, path in self._children.iteritems():
            if not name.startswith('.'):
                yield path

    @property
    def parent(self):
        return self._parent

    @property
    def data(self):
        if self._data is None:
            return self.default_value
        return self._data

    @data.setter
    def data(self, data):
        if not self.path.suffix:
            self._path = self._resolve_suffix(data)

        if data is None:
            self._data = data
            return

        # If data remains unchanged, don't
        # bother altering the `isdirty` bool.
        if data == self._data:
            return

        if not self.type:
            self._type = data.__class__

        try:
            data = self.type(data)

        except TypeError:
            raise TypeError("Item has no type")

        except ValueError:
            raise ValueError('%r: %r, expected %r'
                             % (data,
                                data.__class__.__name__,
                                self.type.__name__))

        self._data = data
        self.isdirty = True

    def _resolve_suffix(self, data=None):
        dt = type(data)

        if data is None:
            dt = None

        suffix = python_to_string(dt)
        return self.relativepath.copy(suffix=suffix)

    @property
    def isvalid(self):
        if self._isvalid is None:
            # Refresh path to ensure it is valid
            getattr(self, 'path')
        return self._isvalid

    @property
    def hasdata(self):
        return True if getattr(self, 'data', None) else False

    @property
    def haschildren(self):
        return self._children != {}

    @property
    def hasparent(self):
        return self.parent is not None


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

    An existing location, capable of hosting metadata.

    """

    LOG = logging.getLogger('openmetadata.lib.Location')

    def __init__(self, *args, **kwargs):
        super(Location, self).__init__(*args, **kwargs)

        if not self._path.isabsolute:
            raise error.RelativePath('Path must be absolute: %s' % path)

        if not service.exists(self.path.as_str):
            raise error.Exists("The path to a Location object "
                               "must previously exist")

    # def copy(self, path=None):
    #     node = self.__class__(path or self.path)
    #     return node

    @property
    def data(self):
        return self._children.values()

    @property
    def resolved_path(self):
        return self.path + self._path.CONTAINER

    def dump(self):
        raise NotImplementedError

    @property
    def hasparent(self):
        return True


class Group(Node):
    """
     ____
    |    |_______
    |            |
    |     om     |
    |            |
    |____________|

    A container of additional groups and datasets.

    """

    LOG = logging.getLogger('openmetadata.lib.Group')

    def __iter__(self):
        for child in self.children:
            yield child

    def __init__(self, *args, **kwargs):
        super(Group, self).__init__(*args, **kwargs)

        if self.relativepath.isabsolute:
            raise error.RelativePath('Path must be relative: %r'
                                     % self.relativepath.as_str)

    @property
    def data(self):
        return self._children.values()

    @data.setter
    def data(self, value):
        raise NotImplementedError

    def dump(self):
        raise NotImplementedError


class Blob(Node):
    """
     ______
    |       \
    |        |
    |        |
    |        |
    |________|

    """

    def __init__(self, *args, **kwargs):
        super(Blob, self).__init__(*args, **kwargs)

        if self.relativepath.isabsolute:
            raise error.RelativePath('Path must be relative: %r'
                                     % self.relativepath.as_str)

        # Nodes are dirty until they are pulled, and
        # made dirty again via setattr(self.data)
        self.isdirty = True

    def load(self, data):
        raise NotImplementedError

    def dump(self):
        """To dump a blob means to hardlink"""
        return json.dumps(self.path.as_str)

    @property
    def haschildren(self):
        return False


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

    def load(self, data):
        """De-serialise `data` into `self`"""
        try:
            self.data = json.loads(data)
        except ValueError:
            LOG.warning("%s contains invalid data" % self.path)
            self.data = data

    def dump(self):
        """Serialise contents of `self`"""
        return json.dumps(self.data)

    # def __getattr__(self, metaattr):
    #     """Retrieve meta-metadata as per RFC15"""
    #     raise NotImplementedError("Attempted to get "
    #                               "meta-metadata from %s" % self)


class History(Group):
    pass


class Versions(Group):
    pass


class Version(Group):
    pass


class Imprint(Group):
    def __init__(self, *args, **kwargs):
        super(Imprint, self).__init__(*args, **kwargs)
        self._time = None

    @property
    def time(self):
        """
        Return tuple of recorded time.

        Example
            >>> imprint = Imprint('name&20140404-105421')
            >>> imprint.time > (2013,)
            True
            >>> imprint.time > (2015,)
            False
        """

        if not self._time:

            date = self.path.option
            year = int(date[:4])
            month = int(date[4:6])
            day = int(date[6:8])

            time = date.rsplit("-")[-1]
            hour = int(time[:2])
            minute = int(time[2:4])
            second = int(time[4:])

            self._time = (year, month, day, hour, minute, second)

        return self._time


"""

Open Metadata data-types

"""


class Bool(Dataset):
    default_value = False


class Int(Dataset):
    default_value = 0


class Float(Dataset):
    default_value = 0.0


class String(Dataset):
    default_value = ''


class Text(Dataset):
    default_value = ''


class Date(Dataset):
    @property
    def default_value(self):
        return service.currenttime()


class Null(Dataset):
    default_value = None


class Enum(Group):
    default_value = []


class Tuple(Group):
    default_value = ()


class List(Group):
    default_value = []


class Dict(Group):
    default_value = {}


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
    unicode: 'string',
    None: 'null',
    tuple: 'tuple',
    list: 'list',
    dict: 'dict'
}


def python_to_string(obj):
    if obj == type(None):
        obj = None

    string = _python_to_string.get(obj)
    if not string:
        raise ValueError("Unrecognised Python datatype: %r" % obj)
    return string


def string_to_python(obj):
    _map = dict((v, k) for (k, v) in _python_to_string.items())
    return _map.get(obj)


"""

Factories

"""


class _FactoryBase(object):
    types = {}
    default = None

    def __new__(cls, path, *args, **kwargs):
        if isinstance(path, Path):
            suffix = path.suffix
        else:
            suffix = service.suffix(path)
        Datatype = cls.types.get(suffix) or cls.default
        return Datatype(path, *args, **kwargs)

    @classmethod
    def register(cls, type):
        cls.types[type.__name__.lower()] = type

    @classmethod
    def unregister(cls, type):
        pass


class GroupFactory(_FactoryBase):
    types = {}
    default = Group


class DatasetFactory(_FactoryBase):
    types = {}
    default = Dataset


supported_types = {
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
    for dataset in supported_types['datasets']:
        DatasetFactory.register(dataset)

    for group in supported_types['groups']:
        GroupFactory.register(group)


register()


if __name__ == '__main__':
    import doctest
    doctest.testmod()

    import openmetadata as om
    om.setup_log('openmetadata')

    # Starting-point
    location = om.Location(r'C:\Users\marcus\om2')

    # # Add a regular string
    # ostring = om.Dataset('simple_data.string', data='whop', parent=location)
    # ostring = om.Dataset('test', data=False, parent=location)
    ostring = om.Dataset('test', data=None, parent=location)
    print ostring.path
    new_path = ostring.relativepath.copy(suffix='null')
    # print ostring.copy(path=new_path).path
    # print ostring.data
    # ostring.data = 5
    # print ostring.data
    # print ostring.dump()
    # print om.exists(ostring)
    # print ostring.path

    # # Add text
    # text = om.Dataset('story.text', parent=location)
    # text.data = 'There once was a boy'

    # # Add a list
    # olist = om.Group('mylist.list', parent=location)

    # # Containing three datasets..
    # l1 = om.Dataset(path='item1', data='a string value', parent=olist)
    # l2 = om.Dataset(path='item2', data=True, parent=olist)
    # l3 = om.Dataset(path='item3', data=5, parent=olist)

    # om.ls(olist)
    # # ..and a dictionary..
    # odict = om.Group(path='mydict.dict', parent=olist)

    # # ..with tree keys
    # key1 = om.Dataset('key1.string', data='value', parent=odict)

    # # One of which, we neglect to specify a data-type.
    # # The data-type will be determined via the Python data-type <str>
    # key2 = om.Dataset('key2', data=True, parent=odict)
    # print key2.path.suffix

    # text = om.Dataset('story.text', parent=odict)
    # text.data = 'There once was a boy'
    # print repr(odict['story'])

    # print text.path
    # print text.path.meta

    # Finally, write it to disk.
    # print location.dump()
    # print text.dump()
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
    # print dataset.type
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
    # path = r'c:\users\marcus\om2'
    # om.write(path, True, 'parent/state')
    # om.write(path, 'There once was a boy', 'story')
    # om.write(path, 27, 'age')
    # om.write(path, 183.5, 'length')
    # om.write(path, False, 'female')

    # print om.read(path, 'female')

    # for node in om.read(path):
    #     data = om.read(path, node.name)
    #     print "%s = %s <'%s'>" % (node.name, data, type(data).__name__)

    # print om.read(path)
    # assert not om.exists(dataset)
    # dataset.data = True
    # # dataset.data = 'string'
    # print dataset.path
    # # print dataset.type
    # print dataset.suffix

    # print omtype_from_pythonobj(True)

    # mylist = List('test.list')
    # print mylist.type

    # location = om.Location(r'c:\users\marcus\om2')
    # group = om.Group('parent', parent=location)
    # print group.path
    # print group.isvalid

    # node = Node('/my/path')
    # print node.name
    # print node
