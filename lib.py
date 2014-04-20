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


type_to_suffix = {
    bool:       'bool',
    int:        'int',
    float:      'float',
    str:        'string',
    unicode:    'string',
    None:       'null',
    tuple:      'tuple',
    list:       'list',
    dict:       'dict'
}


class Node(object):

    __metaclass__ = abc.ABCMeta
    log = logging.getLogger('openmetadata.lib.Node')

    def __iter__(self):
        value = self._value

        if not value:
            return

        if isinstance(value, dict):
            for key, value in value.iteritems():
                # Filtering
                #
                # TODO: make this more explicit,
                # and configurable.
                if key.startswith('.'):
                    continue

                yield value
        else:
            for value in self.value:
                yield value

    def __getitem__(self, item):
        try:
            if not self.iscollection:
                raise KeyError
            return self._value[item]

        except KeyError:
            raise KeyError("%r not in %r" % (item, self))

    def __contains__(self, key):
        return key in self._value

    def __str__(self):
        return self.raw_path.name

    def __repr__(self):
        return u"%s.%s(%r)" % (__name__, type(self).__name__, self.__str__())

    def __eq__(self, other):
        """
        Variables within a parent MUST all have unique names.
        If a name is not unique, there is a bug.

        """
        return str(other) == str(self)

    def __ne__(self, other):
        return str(other) != str(self)

    def __hash__(self):
        return hash(str(self))

    @abc.abstractmethod  # Prevent direct instantiation
    def __init__(self, path, value=None, parent=None):
        if isinstance(path, basestring):
            path = Path(path)

        self._path = path
        self._type = None  # cache
        self._suffix = None  # cache
        self._isvalid = None

        self._value = value
        self._parent = []
        self._iscollection = None
        self._mro = [self]

        if parent:
            parent.add(self)

    @property
    def path(self):
        path = self.raw_path

        try:
            parent = next(self.parent)
        except StopIteration:
            return path

        parent_path = parent.path
        if hasattr(parent, 'resolved_path'):
            parent_path = parent.resolved_path

        path = parent_path + path
        self._isvalid = True

        return path

    @property
    def raw_path(self):
        return self._path

    @property
    def mro(self):
        return self._mro

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
            self._type = self.path.suffix

        return self._type

    def add(self, child):
        if not isinstance(self._value, dict):
            self._value = {}

        path = child.raw_path
        key = path.name

        if path.hasoption:
            key += path.OPTSEP + path.option

        self._value[key] = child
        child._parent.append(self)

    def copy(self, path=None, deep=False, parent=None):
        path = path or self.raw_path
        copy = self.__class__(path, parent=parent)

        # Perform a deep copy, including all children
        if self.iscollection:
            if deep:
                for _, value in self._value.iteritems():
                    value.copy(deep=True, parent=copy)
        else:
            copy._value = self._value

        # Make the copy aware of `self` parent, but `self`
        # should not be aware of `copy` as a child, as it would
        # cause `self` to get a duplicate child per copy.
        copy._parent = self._parent

        return copy

    def clear(self):
        """Remove existing value/children"""
        if isinstance(self._value, dict):
            while self._value:
                self._value.popitem()
        elif isinstance(self._value, list):
            while self._value:
                self._value.pop()
        else:
            self._value = None

    def ls(self, _level=0):
        """List contained children"""
        tree = '\t' * _level + self.path.name + '\n'

        if self.iscollection:
            for node in self:
                tree += node.ls(_level + 1)

        return tree

    @property
    def parent(self):
        for parent in self._parent:
            yield parent

    @property
    def value(self):
        if self._value is None:
            return defaults.get(self.type)
        return self._value

    @value.setter
    def value(self, value):
        raise NotImplementedError

    def _resolve_suffix(self, value=None):
        if value is None:
            dt = None
        else:
            dt = type(value)

        suffix = type_to_suffix.get(dt)
        return self.raw_path.copy(suffix=suffix)

    @property
    def iscollection(self):
        """`self` contains one or more variables

        Description
            A Variable containing other variables is referred
            to as a collection; on a file-system, a collection
            represents a folder. Non-collections are then files.

        """

        if self._iscollection is None:
            return isinstance(self._value, dict)
        return self._iscollection

    @iscollection.setter
    def iscollection(self, value):
        """Manually specify if object is a collection"""
        self._iscollection = value

    @property
    def haschildren(self):
        return self.iscollection and self._value

    @property
    def hasvalue(self):
        return self._value is not None

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

    @property
    def path(self):
        return self._path + self._path.CONTAINER

    @property
    def parent(self):
        yield Location(self._path.parent)

    def dump(self):
        raise NotImplementedError

    @property
    def haschildren(self):
        return True

    @property
    def hasparent(self):
        return True


class Variable(Node):
    """
     ____
    |____|______
    |          |\
    |            |
    |            |
    |____________|

    Description
        A storage location and an associated symbolic name
        (an identifier) which contains some known or unknown
        quantity or information, a value.

        On disk, a variable is both a file and a folder; depe-
        nding on its value. E.g. a list if a folder, bool is a file.

    Reference
        http://en.wikipedia.org/wiki/Variable_(computer_science)

    """

    def __init__(self, *args, **kwargs):
        super(Variable, self).__init__(*args, **kwargs)

        if len(args) > 1:
            self.value = args[1]
        elif 'value' in kwargs:
            self.value = kwargs.get('value')

    @property
    def value(self):
        return super(Variable, self).value

    @value.setter
    def value(self, value):
        self._path = self._resolve_suffix(value)
        assert self.path.suffix

        # Reset iscollection flag.
        #
        # Whether or not `self` is a collection is
        # henceforth determined by its corresponding value.
        #
        self._iscollection = None

        # Values are always overridden.
        self.clear()

        if isinstance(value, list):
            self._value = {}

            index = 0
            for child in value:
                Variable(str(index), value=child, parent=self)
                index += 1

        elif isinstance(value, dict):
            self._value = {}

            for key, value in value.iteritems():
                Variable(key, value=value, parent=self)

        else:
            assert json.dumps(value)
            self._value = value

    def load(self, value):
        """De-serialise `value` into `self`"""
        try:
            self.value = json.loads(value)
        except ValueError:
            LOG.warning("%s contains invalid value" % self.path)
            self.value = value

    def dump(self):
        """Serialise contents of `self`"""
        assert not isinstance(self._value, dict)
        return json.dumps(self.value)


# class Imprint(Group):
#     def __init__(self, *args, **kwargs):
#         super(Imprint, self).__init__(*args, **kwargs)
#         self._time = None

#     @property
#     def time(self):
#         """
#         Return tuple of recorded time.

#         Example
#             >>> imprint = Imprint('name&20140404-105421')
#             >>> imprint.time > (2013,)
#             True
#             >>> imprint.time > (2015,)
#             False
#         """

#         if not self._time:

#             date = self.path.option
#             year = int(date[:4])
#             month = int(date[4:6])
#             day = int(date[6:8])

#             time = date.rsplit("-")[-1]
#             hour = int(time[:2])
#             minute = int(time[2:4])
#             second = int(time[4:])

#             self._time = (year, month, day, hour, minute, second)

#         return self._time


# type_to_suffix = {
#     bool:       'bool',
#     int:        'int',
#     float:      'float',
#     str:        'string',
#     unicode:    'string',
#     None:       'null',
#     tuple:      'tuple',
#     list:       'list',
#     dict:       'dict'
# }


# def python_to_string(obj):
#     if obj is type(None):
#         obj = None

#     string = type_to_suffix.get(obj)
#     if not string:
#         raise ValueError("Unrecognised Python datatype: %r" % obj)
#     return string


# def string_to_python(obj):
#     _map = dict((v, k) for (k, v) in type_to_suffix.items())
#     return _map.get(obj)


"""

Factories

"""


defaults = {
    'bool':   False,
    'int':    0,
    'float':  0.0,
    'string': '',
    'text':   '',
    'date':   service.currenttime,
    'list':   [],
    'dict':   {}
}


if __name__ == '__main__':
    import doctest
    doctest.testmod()

    import openmetadata as om
    om.setup_log('openmetadata')

    # Starting-point
    location = om.Location(r'C:\Users\marcus\om2')

    # # Add a regular string
    # ostring = om.Dataset('simple_data.string', value='whop', parent=location)
    # ostring = om.Dataset('test', value=False, parent=location)
    ostring = om.Dataset('test', value=None, parent=location)
    print ostring.path
    new_path = ostring.raw_path.copy(suffix='null')
    # print ostring.copy(path=new_path).path
    # print ostring.value
    # ostring.value = 5
    # print ostring.value
    # print ostring.dump()
    # print om.exists(ostring)
    # print ostring.path

    # # Add text
    # text = om.Dataset('story.text', parent=location)
    # text.value = 'There once was a boy'

    # # Add a list
    # olist = om.Group('mylist.list', parent=location)

    # # Containing three datasets..
    # l1 = om.Dataset(path='item1', value='a string value', parent=olist)
    # l2 = om.Dataset(path='item2', value=True, parent=olist)
    # l3 = om.Dataset(path='item3', value=5, parent=olist)

    # om.ls(olist)
    # # ..and a dictionary..
    # odict = om.Group(path='mydict.dict', parent=olist)

    # # ..with tree keys
    # key1 = om.Dataset('key1.string', value='value', parent=odict)

    # # One of which, we neglect to specify a value-type.
    # # The value-type will be determined via the Python value-type <str>
    # key2 = om.Dataset('key2', value=True, parent=odict)
    # print key2.path.suffix

    # text = om.Dataset('story.text', parent=odict)
    # text.value = 'There once was a boy'
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
    # print repr(obool.value)

    # print mylist.value

    # simple = location._children.get('simple_data')
    # om.pull(simple)
    # print simple.value
    # # print simple.path

    # print om.read(r'c:\users\marcus\om2', 'simple_data')
    # print om.read(r'c:\users\marcus\om2', 'mylist/item4/key1')
    # print om.read(r'c:\users\marcus\om2', 'mylist', 'item4', 'key1')

    # location = om.Location(r'c:\users\marcus\om2')
    # dataset = om.Dataset('suffixless', parent=location)
    # dataset.value = 3.0
    # dataset.value = 'hello'
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
    # print child.value
    # print type(child.value)

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
    #     value = om.read(path, node.name)
    #     print "%s = %s <'%s'>" % (node.name, value, type(value).__name__)

    # print om.read(path)
    # assert not om.exists(dataset)
    # dataset.value = True
    # # dataset.value = 'string'
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
