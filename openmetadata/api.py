"""api.py provides package-level access to all supported
facilities of Open Metadata.

See help(openmetadata) for more information

Attributes:
    Path: OS-dependent path-manipulation object
    Resource: Shorthand for superclass access
    Location: Folder represention
    Entry: Metadata representation

"""

import os
import time
import errno
import shutil
import logging
import getpass

from openmetadata import lib
from openmetadata import util
from openmetadata import error

log = logging.getLogger('openmetadata.api')


# Objects

"""

Resource     -- Superclass to every other object in OM
Location    -- Path to which metadata is associated
Entry       -- Dynamically typed metadata entry
Path

"""

Path = lib.Path
Resource = lib.Resource
Location = lib.Location
Entry = lib.Entry

# Include utilities
find = util.find
find_all = util.find_all
split = util.split
default = util.default

__all__ = [
    # Main objects
    'Resource',
    'Location',
    'Entry',
    'Path',

    # Main functionality
    'flush',
    'read',
    'write',
    'convert',
    'pull',
    'recycle',
    'clear',
    'find',
    'split',
    'default',
    'entry',
    'inherit',
    'islocation',
    'isentry',
    'error'
]


# ---------------------------------------------------------------------
#
# Helper utilities
#
# ---------------------------------------------------------------------


def _currenttime():
    return time.strftime("%Y%m%d-%H%M%S", time.gmtime())


def _remove(path):
    """
    Remove `path`, regardless of it being a file or folder.

    """

    if os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.isfile(path):
        os.remove(path)
    else:
        raise TypeError("%s is not a valid path" % path)


def _move(source, target):
    """
    Move `source` to `target`, creating missing
    parts of the hierarchy is required.

    """

    dirname = os.path.dirname(target)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    shutil.move(source, target)


# ---------------------------------------------------------------------
#
# Core Functionality
# http://rfc.abstractfactory.io/spec/10
#
# ---------------------------------------------------------------------


def commit(resource):
    pass


def push():
    pass


def flush(resource, track_history=True):
    """Commit pending values to the data-store

    The flush occurs in three stages; find, track and
    store. Finding is a matter of looking up `resource`
    against the datastore::

        # We want to write..
        $ /home/marcus/.meta/new.string

        # ..but this one already exists
        $ /home/marcus/.meta/new.int

    To track means to look for an existing entry. If found,
    store its current value, along with who and when. Finally,
    commit values to disk.

    Arguments:
        resource (Resource): Location or Resource to flush
        track_history (bool, optional): Produce history of `resource`

    Returns:
        Resource: Unmodified

    """

    if isinstance(resource, Location):
        target = _flush_location

    elif isinstance(resource, lib.Resource):
        target = _flush_entry

    else:
        raise ValueError("Must pass object of type Resource")

    target(resource, track_history=track_history)


def _flush_location(resource, track_history=True):
    for child in resource:
        _flush_entry(child, track_history)


def _flush_entry(resource, track_history=True):
    parent = resource.parent
    history_resource = resource
    existing_resource = None

    #  _______________
    # |      -->      |
    # |    /  ?  \    |
    # |    \     /    |
    # |      <--      |
    # |_______________|
    #
    # Track and recycle existing

    name = resource.path.name

    existing = find(parent.path.as_str, name)
    if existing:
        existing_resource = Entry(existing, parent=parent)

    history_resource = existing_resource or resource
    if not history_resource.type in ('dict', 'list'):
        if track_history:
            _make_history(history_resource)

    #  _______________
    # |      -->      |
    # |    /  !  \    |
    # |    \     /    |
    # |      <--      |
    # |_______________|
    #
    # Recycle existing

    if existing_resource and resource.path != existing_resource.path:
        # TODO: this should really be permanent, as the copy
        # has already been stored in history. But, for safety
        # let's keep it around until someone complains about it.
        recycle(existing_resource, permanent=False)

    #  _______________
    # |      -->      |
    # |    /  y  \    |
    # |    \     /    |
    # |      <--      |
    # |_______________|
    #
    # Commit to datastore

    # Resource is a directory
    if resource.type in ('dict', 'list'):
        try:
            os.makedirs(resource.path.as_str)
        except OSError as e:
            if e.errno == errno.EEXIST:
                pass

        for child in resource:
            flush(child, track_history)

    # Resource is a file
    else:
        assert resource.type, resource.path.as_str

        path = resource.path.as_str
        value = resource.dump()

        dirname = os.path.dirname(path)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        if value is None:
            value = ''

        with open(path, 'w') as f:
            f.write(value)

        log.info("flush(): Successfully flushed: %r" % path)

    return resource


def pull(resource, lazy=False, depth=1, merge=False, _currentlevel=1):
    """Physically retrieve value from datastore.

    Arguments:
        lazy (bool): Only pull if no existing value already exists
        depth (int): Pull `resource` and `depth` levels of children
        merge (bool): Combine results with existing value of `resource`

    Raises:
        error.Exists

    Returns:
        Resource: The originally passed resource, to facilitate for
            chaining commands.

    """

    path = resource.path

    if not os.path.exists(path.as_str):
        """
        If the name of `resource` has been entered manually, chances
        are that there is an existing resource on disk under a different
        suffix. If so, find a matching name, under any suffix,
        and assume this is the one the user intended to pull from.

        """

        similars = list()
        for similar in util.find_all(path.parent.as_str,
                                     path.name):
            similars.append(similar)

        if len(similars) > 1:
            raise error.Duplicate("Duplicate entries found "
                                  "@ {}".format(path))

        try:
            resource._path = path.copy(path=similars[0])
        except IndexError:
            raise error.Exists("{} does not exist".format(path))
        else:
            return pull(resource,
                        lazy=lazy,
                        depth=depth,
                        merge=merge,
                        _currentlevel=_currentlevel)

    # if not (isinstance(resource, Location) or resource.type):
    #     raise error.Corrupt(
    #         "Resource did not have type: {}".format(path))

    if lazy and resource.has_value:
        return resource

    if not merge:
        resource.clear()

    path = path.as_str
    if os.path.isdir(path):
        for _, dirs, files in os.walk(path):
            for entry in dirs:
                Entry(entry, parent=resource)

            for entry in files:
                Entry(entry, parent=resource)

            break

    else:
        try:
            with open(path, 'r') as f:
                value = f.read()
        except IOError as e:
            if e.errno == errno.ENOENT:
                raise error.Exists(path)
            elif e.errno == errno.EACCES:
                raise error.Exists("Make sure this is a file "
                                   "and that you have the appropriate "
                                   "permissions: {}".format(path))

        # Empty files return an empty string
        if value != "":
            resource.load(value)

    # Continue pulling children until `depth` is reached
    if _currentlevel < depth:
        if resource.type in ('dict', 'list'):
            for child in resource:
                pull(child,
                     lazy=lazy,
                     depth=depth,
                     merge=merge,
                     _currentlevel=_currentlevel + 1)

    resource.isdirty = False
    return resource


def recycle(resource, permanent=False):
    """Remove `resource` from datastore, either to trash or permanently

    Arguments:
        resource (Resource): Resource to recycle
        permanent (bool): Either remove from disk, or store in trash

    Returns:
        True if successful, False otherwise.

    """

    if not os.path.exists(resource.path.as_str):
        log.warning("remove(): %s did not exist" % resource.path.as_str)
        return False

    if permanent:
        _remove(resource.path.as_str)
        log.info("remote(): Permanently removed %r" % resource.path.as_str)
    else:
        trash(resource)

    return True


def trash(resource):
    """Move resource `resource` to trash bin

    Arguments:
        resource (Resource): Resource to move to trash

    Returns:
        None

    """

    trash_path = resource.path.parent + lib.TRASH

    if not lib.Path.CONTAINER in trash_path.as_str:
        # Open Metadata only bothers with .meta subfolders.
        # In cases where we trash the .meta folder, we'll
        # have to store it underneath an additional .meta
        trash_path = trash_path + lib.Path.CONTAINER

    # Ensure resource.path.name is unique in trash_path, as per RFC14
    if os.path.exists(trash_path.as_str):
        for match in util.find_all(trash_path.as_str, resource.path.name):
            match_path = trash_path + match
            _remove(match_path.as_str)

            log.info("remove(): Removing exisisting "
                     "%r from trash" % match_path.name)

    basename = resource.path.basename
    log.info("Trashing basename: %s" % basename)
    log.info("Fullname: %s" % resource.path.as_str)
    deleted_path = trash_path + basename

    assert not os.path.exists(deleted_path.as_str), deleted_path

    _move(resource.path.as_str, deleted_path.as_str)
    log.info("remove(): Successfully removed %r" % resource.path.as_str)


def history(resource):
    pass


def restore(resource):
    pass


def _make_history(resource):
    """Store value of `resource` as-is on disk in history

    Arguments:
        resource (Resource): Resource from which to make history.

    """

    # We'll be pulling data into a copy, rather than the
    # original, so as to avoid overwriting any existing value.
    copy = resource.copy()

    try:
        pull(copy, lazy=True)
    except error.Exists:
        # If it doesn't exist, we can't make history.
        return

    try:
        parent = resource.parent

        # Avoid our `copy` adding itself as a child
        # to `parent`; this would cause the dictionary
        # containing the parent's children to change.
        #   Python doesn't like this.
        parent = parent.copy()
    except StopIteration:
        return

    # Prepare name of `imprint` (see RFC12)
    name = resource.path.name
    imprint_time = _currenttime()
    imprint_name = "{name}{sep}{time}".format(name=name,
                                              sep=lib.Path.QUERYSEP,
                                              time=imprint_time)
    # Get previous value
    old_value = pull(copy).value
    old_suffix = copy.path.suffix

    # Construct history group
    history = Entry('.history', parent=parent)
    imprint = Entry(imprint_name, parent=history)

    Entry('user.string', value=getpass.getuser(), parent=imprint)
    Entry('value.{}'.format(old_suffix), value=old_value, parent=imprint)

    flush(history, track_history=False)

    log.info("_make_history(): Successfully made history for %s (value=%s)"
             % (copy, copy.value))


# ---------------------------------------------------------------------
#
# Cascading Metadata, RFC12
# http://rfc.abstractfactory.io/spec/12
#
# ---------------------------------------------------------------------


def inherit(resource, depth=0, merge=False, lazy=False):
    """Inherit `resource` from above hierarchy

    Inheritance works much like it does in programming; any value
    present in a superclass is added, subclasses then overrides those
    values.

    Specification - http://rfc.abstractfactory.io/spec/12/

    Parameters:
        resource (str): Adding inherited values to this.
        depth (int): How far up a hierarchy to inherit from, 0 means unlimited
        merge (bool): Either keep current values and merge new, or clear first.
        pull (bool): Not pulling will only fill up the mro (see RFC12)
        lazy (bool): Should I bother reading when values already exists?

    """

    if isinstance(resource, Location):
        return _inherit_location(resource, depth, merge, lazy)
    else:
        return _inherit_entry(resource, depth, merge, lazy)


def _inherit_entry(resource, depth=0, merge=False, lazy=False):
    """Inheriting an entry differs from inheriting a Location

    A Location is only capable of storing children, whereas an Entry
    may hold either children or a value. Inheriting children will traverse
    the hierarchy like for Location, but inheriting value means to fetch
    the closest value in the method-resolution-order.

    TODO: At the moment, values are read from top-to-bottom even though
        a great increase in performance and I/O could be made if it only
        fetched the closest value; as advertised above. It is however, an
        optimisation and thus delayed.

    """

    tree = list()

    parent = resource.location
    while parent:
        tree.insert(0, parent)
        parent = parent.parent

    # Children overwrites parents
    tree.reverse()

    parent = tree.pop()
    metapath = resource.path.meta

    while tree:
        descendant = entry(parent, metapath.as_str)

        try:
            pull(descendant)
        except error.Exists:
            pass

        else:
            #  ___
            # |___|___
            # |       |\
            # |         |
            # |_________|
            #     |    ___
            #     |   |___|___
            #     |___|       |\
            #         |         |
            #         |_________|
            #
            #  Add child to location
            if descendant.type in ('dict', 'list'):
                for child in descendant.children:
                    resource.add(child)

            else:
                #  ___
                # |___|___
                # |       |\
                # |         |  <--- value
                # |_________|
                #
                value = descendant.value

                if value:
                    resource.value = value

        parent = tree.pop()

    return resource


def _inherit_location(location, depth=0, merge=False, lazy=False):
    tree = list()

    parent = location
    while parent:
        tree.insert(0, parent)
        parent = parent.parent

    # Children overwrites parents
    tree.reverse()

    # Assign inherited metadata in the order
    # they naturally override each other.
    # Overridden values will silently retreat
    # back into the depths from which they came.
    for location in tree:
        #  ___
        # |___|___
        # |       |\
        # |         |
        # |_________|
        #     |    ___
        #     |   |___|___
        #     |___|       |\
        #         |         |
        #         |_________|
        #
        #  Add child to location

        try:
            pull(location)
        except error.Exists:
            pass
        else:
            for entry in location:
                location.add(entry)

    return location


def _inherit_value():
    """TODO: transition from inheriting location versus entries to
        inhertiing values versus children, as it more closely relates
        to the differences between the two"""


def _inherit_children():
    pass


# ---------------------------------------------------------------------
#
# Convenience functions
#
# ---------------------------------------------------------------------


def convert(path):
    """Turn a full `path` into an entry

    Example
        >> path = r'c:\users\marcus\om\.meta\test'
        >> entry = convert(path)
        >> entry
        Entry('test')

    """

    location, metapath = split(path)
    return read(location,
                metapath,
                _return_root=True,  # Return object, as opposed to values
                _return_nonexisting=True)  # Return object,
                                           # regardless of
                                           # existance.


def read(path, metapath=None, convert=True, **kwargs):
    """Convenience function with which to quickly read from an absolute path.

    Arguments:
        path (str): Absolute path from which to read metadata
        metapath (str): Path to inner metadata, e.g. /size/width
        convert (bool): Whether or not to return Plain-old-data
            or Open Metadata objects

    """

    assert isinstance(path, basestring)

    # Hidden keyword arguments
    _return_root = kwargs.pop('_return_root', False)
    _return_nonexisting = kwargs.pop('_return_nonexisting', False)

    for key, value in kwargs.iteritems():
        raise TypeError("read() got an unexpected keyword argument %r" % key)

    # Allow paths to include the container path, .meta
    # E.g. /home/marcus/.meta == /home/marcus
    path = path.rsplit(lib.Path.CONTAINER, 1)[0]

    location = Location(path)

    if metapath:
        root = entry(location=location, metapath=metapath)
    else:
        root = location

    try:
        pull(root)
    except error.Exists:
        if not _return_nonexisting:
            return None

    if _return_root:
        # Return entry immediately, don't bother breaking it apart.
        # This is used mainly for convert() and isn't meant to be used
        # on its own.
        return root

    if convert:
        # Convert values to native Python objects.
        #
        # This is a list of string for collections,
        # representing the keys of e.g. a folder, and
        # the actual value of a dataset, such as a file.
        #
        # Output
        #   --> ['child', 'anotherchild']

        if isinstance(root, Location) or root.type in ('dict', 'list'):
            return [child.path.name for child in root]
        else:
            # Output
            #   --> 'value of child'
            return root.value

    else:
        # Return value as-is, meaning Open Metadata
        # `Entry` and `Location` objects.
        if isinstance(root, Location) or root.type in ('dict', 'list'):
            # Output
            #   --> [Entry('child'), Entry('anotherchild')]
            value = root.value
            if value:
                assert isinstance(value, dict)
                return value.values()

        else:
            # Output
            #   --> Entry('child')

            return root


def entry(location, metapath):
    """Get entry from `metapath` in `location`

    Supports inputs as either string or native Location and Path objects.

    Arguments:
        location (str): Location in which entry resides
        metapath (str): Metapath which to convert into Entry

    Returns:
        Entry: Fully qualified Entry object

    """


    if isinstance(location, basestring):
        location = Location(location)

    if isinstance(metapath, basestring):
        metapath = Path(metapath)

    assert metapath

    root = location
    parts = metapath.parts

    while parts:
        try:
            pull(root)
        except error.Exists:
            pass

        current = parts.pop(0)
        while not current:
            current = parts.pop(0)

        # Remove suffix for query
        try:
            name, suffix = current.rsplit(lib.Path.EXT, 1)
        except ValueError:
            name, suffix = current, None

        try:
            new_root = root[name]

            # If metapath included a suffix,
            # ensure the child we fetch match this suffix.
            if suffix and new_root.path.suffix != suffix:
                raise KeyError

            root = new_root

        except KeyError:
            root = lib.Entry(current, parent=root)

    return root


def write(path, metapath, value=None):
    location = lib.Location(path)

    parts = util.parse_metapath(metapath)

    root = location
    entries = parts
    for entry_name in entries:
        # As each predecessor is manually specified, there is
        # a chance that a collection of existing/different
        # suffix already exists. If so, use that.
        entry_name = util.find(root.path.as_str, entry_name) or entry_name

        entry = Entry(entry_name, parent=root)
        root = entry

    # If no suffix was specified, initialise a default suffix
    # based on `value`
    root.value = value

    assert root.type

    flush(root)


def clear(path):
    """Remove all metadata from `path`"""
    if isinstance(path, basestring):
        path = lib.Path(path)

    location = Location(path)
    recycle(location)


def islocation(resource):
    return isinstance(resource, lib.Location)


def isentry(resource):
    return isinstance(resource, lib.Entry)


# if __name__ == '__main__':
#     # import os
#     import doctest
#     doctest.testmod()

#     # from pprint import pprint
#     import openmetadata as om
#     om.setup_log('openmetadata')

#     location = om.Location(r'C:\Users\marcus')
#     # entry = om.Entry('test', parent=location)
#     entry = om.Entry('Test.class', parent=location)
#     pull(entry)
#     print repr(entry.path)
# # 