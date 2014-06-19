import abc
import json
import logging

from openmetadata import path
from openmetadata import error
from openmetadata import service

HISTORY = '.history'
VERSIONS = '.versions'
TRASH = '.trash'

LOG = logging.getLogger('openmetadata.lib')

osname = service.OSNAME
path_map = {'nt': path.WindowsPath,
            'posix': path.PosixPath}

Path = path.Path  # unbiased path
DefaultPath = path_map[osname]
MetaPath = path.MetaPath


_type_to_suffix = {
    bool:       ['bool'],
    int:        ['int'],
    float:      ['float'],
    str:        ['string', 'text'],  # text is also valid str
    unicode:    ['string', 'text'],  # text is also valid unicode
    None:       ['null'],
    tuple:      ['tuple'],
    list:       ['list'],
    dict:       ['dict']
}


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


def type_to_suffix(typ, hint=None):
    """Return suffix for `typ`, favouring `hint` if possible"""
    suffixes = _type_to_suffix.get(typ)
    if hint in suffixes:
        return hint
    else:
        return suffixes[0]


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
            if not self.isparent:
                raise KeyError
            if self._value is None:
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
        Entrys within a parent MUST all have unique names.
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
        self._isparent = None
        self.isdirty = False
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
    def name(self):
        return self.raw_path.name

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

        self._value[key] = child
        child._parent.append(self)

    def copy(self, path=None, deep=False, parent=None):
        path = path or self.raw_path
        copy = self.__class__(path, parent=parent)

        # Perform a deep copy, including all children
        if self.isparent:
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

        if self.isparent:
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
            default = defaults.get(self.type)
            if hasattr(default, '__call__'):
                default = default()
            return default
        return self._value

    @value.setter
    def value(self, value):
        raise NotImplementedError

    def _resolve_suffix(self, value=None):
        if value is None:
            dt = None
        else:
            dt = type(value)

        suffix = type_to_suffix(dt, hint=self.path.suffix)
        return self.raw_path.copy(suffix=suffix)

    @property
    def isparent(self):
        """`self` contains one or more entrys

        Description
            A Entry containing other entrys is referred
            to as a collection; on a file-system, a collection
            represents a folder. Non-collections are then files.

        """

        if self._isparent is None:
            return isinstance(self._value, dict)
        return self._isparent

    @isparent.setter
    def isparent(self, value):
        """Manually specify if object is a collection"""
        self._isparent = value

    @property
    def haschildren(self):
        return self.isparent and self._value

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

        # Give location a platform-dependent
        # path; e.g. either WindowsPath or PosixPath.
        self._path = DefaultPath(self._path.as_str)

        if not self._path.isabsolute:
            raise error.RelativePath(
                'DefaultPath must be absolute: %s' % self._path)

    @property
    def path(self):
        return self._path + self._path.CONTAINER

    @property
    def name(self):
        return self.raw_path.parent.name

    @property
    def parent(self):
        yield Location(self._path.parent)

    def flush(self):
        """Based on HDF5 flush; calls upon separate mechanisms"""
        raise NotImplementedError

    @property
    def isparent(self):
        return True

    @property
    def hasparent(self):
        return True


class Entry(Node):
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

        On disk, a entry is both a file and a folder; depe-
        nding on its value. E.g. a list is a folder, bool is a file.

    Reference
        http://en.wikipedia.org/wiki/Entry_(computer_science)

    """

    def __init__(self, *args, **kwargs):
        """
        Example
            >>> entry = Entry('home')
            >>> entry.path.as_str
            'home'

            >>> import os
            >>> path = os.path.expanduser('~')
            >>> location = Location(path)
            >>> entry = Entry('home', parent=location)
            >>> test = os.path.join(path, DefaultPath.CONTAINER, 'home')
            >>> assert entry.path.as_str == test

        """

        super(Entry, self).__init__(*args, **kwargs)

        self._path = MetaPath(self._path.as_str)

        if not self._path.isrelative:
            raise error.RelativePath(
                'DefaultPath must be relative: %r' % self._path)

        # Initialise value to default
        if len(args) > 1:
            self.value = args[1]
        elif 'value' in kwargs:
            self.value = kwargs.get('value')

    @property
    def value(self):
        return super(Entry, self).value

    @value.setter
    def value(self, value):
        self._path = self._resolve_suffix(value)
        assert self.path.suffix

        # Reset isparent flag.
        #
        # Whether or not `self` is capable of being a parent is
        # henceforth determined by its corresponding value.
        #
        self._isparent = None

        # Values are always overridden.
        self.clear()

        if isinstance(value, list):
            self._value = {}

            index = 0
            for child in value:
                Entry(str(index), value=child, parent=self)
                index += 1

        elif isinstance(value, dict):
            self._value = {}

            for key, value in value.iteritems():
                Entry(key, value=value, parent=self)

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
        assert not isinstance(self.value, dict)
        return json.dumps(self.value)


if __name__ == '__main__':
    # import doctest
    # doctest.testmod()

    import openmetadata as om
    om.setup_log('openmetadata')

    # Starting-point
    location = om.Location(r'C:\Users\marcus\om2')
    # entry = om.Entry('test', parent=location)
    entry = om.Entry('app.string', parent=location)
    entry._path.set(r'PPP.string')
    print repr(entry.path)

    # meta = DefaultPath(r'c:\users') + MetaPath('/test')
    # print meta
