"""api.py provides package-level access to all supported
facilities of Open Metadata.

See help(openmetadata) for more information

Attributes:
    Path: OS-dependent path-manipulation object
    Resource: Shorthand for superclass access
    Location: Folder represention
    Entry: Metadata representation

"""

import logging
import getpass

from openmetadata import lib
from openmetadata import util
from openmetadata import error
from openmetadata import service

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
    'remove',
    'clear',
    'find',
    'split',
    'default',
    # 'find_all',
    # 'exists',
    # 'existing',
    'inherit',
    # 'history',
    # 'restore',
    'islocation',
    'isentry',
    'error'
]

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
        resource (Resource): Resource to flush
        track_history (bool, optional): Produce history of `resource`

    Returns:
        Resource: Unmodified

    """

    assert isinstance(resource, lib.Resource)

    parent = next(resource.parent)
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
        if track_history and service.exists(history_resource.path.as_str):
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
        remove(existing_resource, permanent=False)

    #  _______________
    # |      -->      |
    # |    /  y  \    |
    # |    \     /    |
    # |      <--      |
    # |_______________|
    #
    # Commit to datastore

    if isinstance(resource, Location) or resource.type in ('dict', 'list'):
        service.flush_dir(resource.path.as_str)

        for child in resource:
            flush(child, track_history)

    else:
        if not resource.type:
            log.warning("Cannot flush %r, "
                        "it has no value."
                        % resource.path.as_str)
            return resource

        path = resource.path.as_str
        value = resource.dump()

        service.flush(path, value)

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
        Resource: The originally passed resource

    """

    path = resource.path

    if lazy and resource.hasvalue:
        return resource

    if not merge:
        resource.clear()

    path = path.as_str
    if service.isdir(path):
        dirs, files = service.ls(path)

        for entry in dirs:
            child = Entry(entry + ".dict", parent=resource)

        for entry in files:
            child = Entry(entry, parent=resource)

    else:
        value = service.open(path)  # raises error.Exists

        # Empty files return an emptry string
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


def remove(resource, permanent=False):
    """Remove `resource` from datastore, either to trash or permanently"""

    if not service.exists(resource.path.as_str):
        log.warning("remove(): %s did not exist" % resource.path.as_str)
        return False

    if permanent:
        service.remove(resource.path.as_str)
        log.info("remote(): Permanently removed %r" % resource.path.as_str)
    else:
        trash(resource)

    return True


def trash(resource):
    trash_path = resource.path.parent + lib.TRASH

    if not lib.Path.CONTAINER in trash_path.as_str:
        # Open Metadata only bothers with .meta subfolders.
        # In cases where we trash the .meta folder, we'll
        # have to store it underneath an additional .meta
        trash_path = trash_path + lib.Path.CONTAINER

    # Ensure resource.path.name is unique in trash_path, as per RFC14
    if service.exists(trash_path.as_str):
        for match in util.find_all(trash_path.as_str, resource.path.name):
            match_path = trash_path + match
            service.remove(match_path.as_str)

            log.info("remove(): Removing exisisting "
                     "%r from trash" % match_path.name)

    basename = resource.path.basename
    log.info("Trashing basename: %s" % basename)
    log.info("Fullname: %s" % resource.path.as_str)
    deleted_path = trash_path + basename

    assert not service.exists(deleted_path.as_str), deleted_path

    service.move(resource.path.as_str, deleted_path.as_str)
    log.info("remove(): Successfully removed %r" % resource.path.as_str)


def history(resource):
    pass


def restore(resource):
    pass


def _make_history(resource):
    """Store value of `resource` as-is on disk in history"""
    assert service.isfile(resource.path.as_str), resource.path

    # We'll be pulling data into a copy, rather than the
    # original, so as to avoid overwriting any existing value.
    copy = resource.copy()

    try:
        parent = next(resource.parent)

        # Avoid our `copy` adding itself as a child
        # to `parent`; this would cause the dictionary
        # containing the parent's children to change.
        #   Python doesn't like this.
        parent = parent.copy()
    except StopIteration:
        return

    # Prepare name of `imprint` (see RFC12)
    name = resource.path.name
    imprint_time = service.currenttime()
    imprint_name = "{name}{sep}{time}".format(name=name,
                                              sep=lib.Path.OPTSEP,
                                              time=imprint_time)
    # Get previous value
    pull(copy, lazy=True)
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


def inherit(resource, depth=0, merge=False, pull=True, lazy=False):
    """Inherit `resource` from above hierarchy

    Inheritance works much like it does in programming; any value
    present in a superclass is added, subclasses then overrides those
    values.

    Specification
        http://rfc.abstractfactory.io/spec/12/

    Parameters
        resource    -- Adding inherited values to this.
        depth   -- How far up a hierarchy to inherit from, 0 means unlimited
        merge   -- Should I add to the values currently present in `resource`?
        pull    -- Not pulling will only fill up the mro (see RFC12)
        lazy    -- Should I bother reading when values already exists?

    """

    parent = resource.location.raw_path
    metapath = resource.path.meta

    # Temporary, in preparation for MRO and Bases
    # implementations.
    while resource.mro:
        resource.mro.pop()

    for location in util.locations(parent):
        resource.mro.append(location)
    # /End temporary.

    tree = []
    level = 1
    while parent:

        if pull:
            entry = read(parent.as_str, metapath, convert=False)
            if entry:
                tree.append(entry)

        if depth and level > depth:
            break

        level += 1
        parent = parent.parent

    # Children overwrites parents
    tree.reverse()

    if not merge:
        resource.clear()

    # Assign inherited metadata in the order
    # they naturally override each other.
    # Overridden values will silently retreat
    # back into the depths from which they came.
    for entry in tree:
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
        #  Add child to resource
        #
        if isinstance(entry, list):
            for entry in entry:
                resource.add(entry)
        else:
            #  ___
            # |___|___
            # |       |\
            # |         |  <--- value
            # |_________|
            #
            resource.value = entry.value

    resource.isdirty = False
    return resource


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

    # Hidden keyword arguments
    _return_root = kwargs.pop('_return_root', False)
    _return_nonexisting = kwargs.pop('_return_nonexisting', False)

    for key, value in kwargs.iteritems():
        raise TypeError("read() got an unexpected keyword argument %r" % key)

    # Allow paths to include the container path, .meta
    # E.g. /home/marcus/.meta == /home/marcus
    path = path.rsplit(lib.Path.CONTAINER, 1)[0]

    location = Location(path)

    root = entry(location=location, metapath=metapath)

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
            children = []
            for child in root:
                children.append(child.path.name)
            return children
        else:
            # Output
            #   --> 'value of child'
            return root.value

    else:
        # Return value as-is, meaning Open Metadata
        # `Entry` and `Location` objects.
        print "NOT CONVERTING"
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
    """Get entry from `metapath` in `location`"""

    if isinstance(location, basestring):
        location = Location(location)

    root = location

    parts = util.parse_metapath(metapath)
    while parts:
        try:
            pull(root)
        except error.Exists:
            # if not _return_nonexisting:
            #     return None
            pass

        current = parts.pop(0)
        while current == '':
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
            if suffix:
                if new_root.path.suffix != suffix:
                    raise KeyError

            root = new_root

        except KeyError:
            # if not _return_nonexisting:
            #     return None

            # If we're interested in non-existent
            # entries, carry on..
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
    remove(location)


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