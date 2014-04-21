"""
-----------------------------------------------------------------------

Open Metadata API

-----------------------------------------------------------------------

Description
    pass

Functionality

    Main
    ----------------------

    dump            -- Write to database
    pull            -- Read from database
    remove          -- Remove from database
    find            -- Return first match
    find_all        -- Return generator of matches

    Temporal
    ----------------------

    history         -- Return generator of available history
    restore         -- Restore from history
    save            -- Saves as new version
    version         -- Retrieves saved version
    versions        -- Return generator of available versions

    Convenience
    ----------------------

    read            -- Convenience method for reading metadata
    write           -- Convenience method for writing metadata
    ls              -- List metacontent of node

Note
    This module isn't to be used directly, all funcionality is
    imported by the __init__.py of 'openmetadata' and retreivable
    via the package directly.

    Example
        >> import openmetadata as om
        >> om.read('/home/marcus')

"""

import logging

from openmetadata import lib
from openmetadata import util
from openmetadata import error
from openmetadata import service

log = logging.getLogger('openmetadata.api')


# Objects

"""

Location    -- Path to which metadata is associated
Entry    -- Dynamically typed metadata entry

"""

Location = lib.Location
Entry = lib.Entry


# Core Functionality


def commit(node):
    pass


def push():
    pass


def dump(node, track_history=True, simulate=False):
    assert isinstance(node, lib.Node)

    if node.iscollection:
        path = node.path.as_str

        service.dump_dir(path)

        for child in node:
            dump(child, track_history, simulate)

    else:
        if not node.type:
            log.warning("Cannot dump %r, "
                        "it has no value."
                        % node.path.as_str)
            return node

        path = node.path.as_str
        value = node.dump()

        if track_history:
            if service.exists(path):
                _make_history(node)

        service.dump(path, value)

        log.info("dump(): Successfully dumped: %r" % path)

    return node


def pull(node, lazy=False, depth=1, merge=False, _currentlevel=1):
    """Physically retrieve value from database

    Parameters
        lazy        -- Only pull if no existing value already exists
        depth       -- Pull `node` and `depth` levels of children
        merge       -- Combine results with existing value of `node`

    """

    path = node.path
    if not service.exists(path.as_str):
        """
        If the name of `node` has been entered manually, chances
        are that there is an existing node on disk under a different
        suffix. If so, find a matching name, under any suffix,
        and assume this is the one the user intended to pull from.

        """
        similar = util.find(path.parent.as_str, path.name)

        if similar:
            node._path = node.raw_path.copy(path=similar)
            return pull(node,
                        lazy=lazy,
                        depth=depth,
                        merge=merge,
                        _currentlevel=_currentlevel)
        else:
            raise error.Exists("%s does not exist" % path)

    if lazy and node.hasvalue:
        return node

    if not merge:
        node.clear()

    path = path.as_str
    if service.isdir(path):
        dirs, files = service.ls(path)
        for entry in dirs + files:
            var = Entry(entry, parent=node)
            var.iscollection = True
    else:
        value = service.open(path)
        node.load(value)

    # Continue pulling children until `depth` is reached
    if _currentlevel < depth:
        if node.iscollection:
            for child in node:
                pull(child,
                     lazy=lazy,
                     depth=depth,
                     merge=merge,
                     _currentlevel=_currentlevel + 1)

    return node


def remove(node, permanent=False):
    """Remove `node` from database, either to trash or permanently"""

    if not service.exists(node.path.as_str):
        log.warning("remove(): %s did not exist" % node.path.as_str)
        return False

    if permanent:
        service.remove(node.path.as_str)
        log.info("remote(): Permanently removed %r" % node.path.as_str)
    else:
        trash(node)

    return True


def trash(node):
    trash_path = node.path.parent + lib.TRASH

    # Ensure node.path.name is unique in trash_path, as per RFC14
    if service.exists(trash_path.as_str):
        for match in util.find_all(trash_path.as_str, node.path.name):
            match_path = trash_path + match
            service.remove(match_path.as_str)

            log.info("remove(): Removing exisisting "
                     "%r from trash" % match_path.name)

    basename = node.path.basename
    deleted_path = trash_path + basename

    assert not service.exists(deleted_path.as_str)

    service.move(node.path.as_str, deleted_path.as_str)
    log.info("remove(): Successfully removed %r" % node.path.as_str)


# def exists(node):
#     """Check if `node` exists under any suffix"""
#     return node.path.name in existing(node)


# def existing(node):
#     pass


def history(node):
    pass


def restore(node):
    pass


def _make_history(node):
    """Store value of `node` as-is on disk in history"""
    assert service.isfile(node.path.as_str), node.path

    # We'll be pulling data into a copy, rather than the
    # original, so as to avoid overwriting any existing value.
    copy = node.copy()

    try:
        parent = next(node.parent)

        # Avoid our `copy` adding itself as a child
        # to `parent`; this would cause the dictionary
        # containing the parent's children to change.
        #   Python doesn't like this.
        parent = parent.copy()
    except StopIteration:
        return

    # Prepare name of `imprint` (see RFC12)
    name = node.path.name
    imprint_time = service.currenttime()
    imprint_name = "{name}{sep}{time}".format(name=name,
                                              sep=lib.Path.OPTSEP,
                                              time=imprint_time)
    # Get previous value
    pull(copy, lazy=True)
    old_value = pull(copy).value

    # Construct history group
    history = Entry('.history', parent=parent)
    imprint = Entry(imprint_name, parent=history)

    Entry('user.string', value='marcus', parent=imprint)
    Entry('value', value=old_value, parent=imprint)

    dump(history, track_history=False)

    log.info("_make_history(): Successfully made history for %s (value=%s)"
             % (copy, copy.value))


# ---------------------------------------------------------------------
#
# Object-oriented Metadata, RFC12
# http://rfc.abstractfactory.io/spec/12/
#
# ---------------------------------------------------------------------


def inherit(node, depth=0, merge=False, pull=True, lazy=False):
    """Inherit `node` from above hierarchy

    Inheritance works much like it does in programming; any value
    present in a superclass is added, subclasses then overrides those
    values.

    Specification
        http://rfc.abstractfactory.io/spec/12/

    Parameters
        node    -- Adding inherited values to this.
        depth   -- How far up a hierarchy to inherit from, 0 means unlimited
        merge   -- Should I add to the values currently present in `node`?
        pull    -- Not pulling will only fill up the mro (see RFC12)
        lazy    -- Should I bother reading when values already exists?

    """

    parent = node.location.raw_path
    metapath = node.path.meta

    # Temporary, in preparation for MRO and Bases
    # implementations.
    while node.mro:
        node.mro.pop()

    for location in util.locations(parent):
        node.mro.append(location)
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
        node.clear()

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
        #  Add child to node
        #
        if isinstance(entry, list):
            for entry in entry:
                node.add(entry)
        else:
            #  ___
            # |___|___
            # |       |\
            # |         |  <--- value
            # |_________|
            #
            node.value = entry.value

    return node


# ---------------------------------------------------------------------
#
# Convenience functions
#
# ---------------------------------------------------------------------


def read(path, metapath=None, convert=True):
    """
    Parameters
        path        --
        metapath    --
        convert     --

    """

    # Allow paths to include the container path, .meta
    # E.g. /home/marcus/.meta == /home/marcus
    path = path.rsplit(lib.Path.CONTAINER, 1)[0]

    location = Location(path)

    root = location

    parts = util.parse_metapath(metapath)
    while parts:
        try:
            pull(root)
        except error.Exists:
            return None

        current = parts.pop(0)
        while current == '':
            current = parts.pop(0)

        # Remove suffix for query
        try:
            name, suffix = current.rsplit(lib.Path.EXT, 1)
        except ValueError:
            name, suffix = current, None

        try:
            root = root[name]

            # If metapath included a suffix,
            # ensure the child we fetch match this suffix.
            if suffix:
                if not root.suffix == suffix:
                    raise KeyError

        except KeyError:
            return None

    try:
        pull(root)
    except error.Exists:
        return None

    if convert:
        # Convert values to native Python objects.
        #
        # This is a list of string for collections,
        # representing the keys of e.g. a folder, and
        # the actual value of a dataset, such as a file.
        #
        # Output
        #   --> ['child', 'anotherchild']

        if root.iscollection:
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

        if root.iscollection:
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

    root.value = value

    assert root.type

    dump(root)


def clear(path):
    """Remove all metadata from `path`"""
    if isinstance(path, basestring):
        path = lib.Path(path)

    location = Location(path)
    remove(location)


def islocation(node):
    return isinstance(node, lib.Location)


def isentry(node):
    return isinstance(node, lib.Entry)


# Include utilities
find = util.find
find_all = util.find_all


__all__ = [
    # Main objects
    'Location',
    # 'Node',
    'Entry',

    # Main functionality
    'dump',
    'read',
    'write',
    'pull',
    'remove',
    'clear',
    'find',
    'find_all',
    # 'exists',
    # 'existing',
    'inherit',
    'history',
    'restore',
    'islocation',
    'isentry'
]


if __name__ == '__main__':
    import doctest
    doctest.testmod()

    # from pprint import pprint
    import openmetadata as om
    om.setup_log('openmetadata')

    path = r'c:\users\marcus\om2'
    location = om.Location(path)
    om.pull(location)
    history = location['.history']
    om.pull(history)
    # gen = history.children
    # gen.next()
    # age = om.history(location['age'])
    # imprint = age.next()
    # om.restore(imprint)