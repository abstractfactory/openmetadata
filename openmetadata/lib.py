"""Open Metadata object model

The Object Model has no concept of a data-store and
can thus not directly query or manipulate it. All
communication between the objects contained within
and a data-store is performed via :mod:`.api.py`

Attributes:
    HISTORY: Name of hidden folder containing history
    VERSIONS: Same as above but for versions
    TRASH: Same as above but for trash

    defaults: When an entry is given a suffix with no
        value, a default value is assigned. These are
        those default values.

"""

import os
import abc
import time
import json
import logging

from openmetadata import path
from openmetadata import error

HISTORY = '.history'
VERSIONS = '.versions'
TRASH = '.trash'

log = logging.getLogger('openmetadata.lib')

osname = os.name
path_map = {'nt': path.WindowsPath,
            'posix': path.PosixPath}

Path = path.Path  # unbiased path
DefaultPath = path_map[osname]
MetaPath = path.MetaPath


def _currenttime():
    return time.strftime("%Y%m%d-%H%M%S", time.gmtime())


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
    'date':   _currenttime,
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


class Resource(object):
    """Lowest-level representation of any resource, both
    files and folders but also any metadata

    Arguments:
        path (str): Absolute or relative path to resource
        value (object, optional): Contained value of any (supported) type
        parent (Resource, optional): Parent of resource. Parents
            are used to hierarchically organise resources.

    Attributes:
        path: Current path, dynamic and based on current value/children
        old_path: Initial path, updated upon flush

    """

    __metaclass__ = abc.ABCMeta
    log = logging.getLogger('openmetadata.lib.Resource')

    def __iter__(self):
        for child in self.children:
            yield child

    def __getitem__(self, item):
        try:
            return self._children[item]
        except KeyError:
            raise KeyError("%r not in %r" % (item, self))

    def __contains__(self, key):
        return key in self._value

    def __str__(self):
        return self._path.name

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
        assert path is not ''

        if isinstance(path, basestring):
            path = Path(path)

        self._path = path
        self._value = value
        self._parent = None
        self._children = dict()
        self.filter = None
        self.isdirty = False

        if parent:
            parent.add(self)

    def add(self, child):
        """Add child `child` to self

        Arguments:
            child (Resource): Child which to add to self

        """

        assert isinstance(child, Resource), repr(child)

        if not isinstance(self._value, dict):
            # Clear out value if a child is added, as there
            # can't be both value and child.
            self._value = dict()

        if not self.type in ('dict', 'list'):
            self._path = self._path.copy(suffix='dict')

        self._children[child.path.name] = child
        child._parent = self

    @property
    def path(self):
        path = self._path

        if not self._parent:
            return path

        parent_path = self._parent.path
        return parent_path + path

    @property
    def name(self):
        return self._path.name

    @property
    def location(self):
        """Return location of `self`

        Any resource is either a Location or a child
        of one. In the latter case, this method retrieves
        its Location object.

        This is primarily a convenience property.

        """

        return Location(self.path.location)

    @property
    def type(self):
        """
        `type` is shorthand for a resource's suffix
         _______________
        |               |
        |  path.suffix  |
        |_______________|

        """

        return self.path.suffix

    def copy(self, path=None, deep=False, parent=None):
        """Create copy of self, based on optional modifications

        Arguments:
            path (str): Copy with an alternative path
            deep (bool): Copy self as well as children of self
            parent (Resource): Copy and move to a different parent

        """

        path = path or self._path
        copy = self.__class__(path, parent=parent)

        # Perform a deep copy, including all children
        if self.type in ('dict', 'list'):
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
        self._children.clear()

    def ls(self, _level=0):
        """List contained children"""
        tree = '\t' * _level + self._path.name + '\n'

        if isinstance(self, Location) or self.type in ('dict', 'list'):
            for resource in self:
                tree += resource.ls(_level + 1)

        return tree

    @property
    def parent(self):
        return self._parent

    @property
    def children(self):
        for _, child in self._children.iteritems():
            if self.filter:
                if self.filter(child):
                    yield child
            else:
                yield child

    @property
    def value(self):
        if self._value is None:
            default = defaults.get(self.type)
            if hasattr(default, '__call__'):
                default = default()
            self._value = default
        return self._value

    @value.setter
    def value(self, value):
        raise NotImplementedError

    @property
    def has_children(self):
        return True if self.children else False

    @property
    def has_value(self):
        return self._value is not None

    @property
    def has_parent(self):
        return self.parent is not None


class Location(Resource):
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

    log = logging.getLogger('openmetadata.lib.Location')

    def __init__(self, *args, **kwargs):
        super(Location, self).__init__(*args, **kwargs)

        # Give location a platform-dependent
        # path; e.g. either WindowsPath or PosixPath.
        self._path = DefaultPath(self._path.as_str)

        if not self._path.isabsolute:
            raise error.RelativePath(
                'DefaultPath must be absolute: %s' % self._path)

    def add(self, child):
        """Add child `child` to self

        Arguments:
            child (Resource): Child which to add to self

        """

        self._value = None
        self._children[child.path.name] = child
        child._parent = self

    @property
    def path(self):
        return self._path + self._path.CONTAINER

    @property
    def old_path(self):
        return self.path

    @property
    def name(self):
        return self._path.parent.name

    @property
    def parent(self):
        parent = self._path.parent
        return Location(parent) if parent else None

    def flush(self):
        """Based on HDF5 flush; calls upon separate mechanisms"""
        raise NotImplementedError

    # @property
    # def isparent(self):
    #     return True

    # @property
    # def isgroup(self):
    #     return True

    @property
    def has_parent(self):
        return True


class Entry(Resource):
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
        if value is not None:
            datatype = type(value)

            suffix = type_to_suffix(datatype, hint=self.type)
            self._path = self._path.copy(suffix=suffix)

        assert self.type, self.path.as_str

        # Values always replace children
        self.clear()

        assert json.dumps(value)
        self._value = value

    def load(self, value):
        """De-serialise `value` into `self`"""
        try:
            self.value = json.loads(value)
        except ValueError:
            log.warning("%s contains invalid value" % self.path)
            self.value = None

    def dump(self):
        """Serialise contents of `self`"""
        assert not isinstance(self.value, dict)
        value = self.value
        if value is None:
            return None
        return json.dumps(value)


if __name__ == '__main__':
    import doctest
    doctest.testmod()

    # import tempfile
    # import openmetadata as om
    # om.setup_log('openmetadata')

    # # Starting-point
    # root = tempfile.mkdtemp()
    # location = om.Location(root)

    # entry = om.Entry('app.dict', parent=location)
    # child = om.Entry('child.string', value="Hello", parent=entry)
    # print repr(child.path)
