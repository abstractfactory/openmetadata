"""
-----------------------------------------------------------------------

Open Metadata API

-----------------------------------------------------------------------

Description
    pass

Functionality

    Main
    ----

    dump            -- Write to database
    pull            -- Read from database
    remove          -- Remove from database
    find            -- Return generator of matches

    Temporal
    --------

    history         -- Return generator of available history
    restore         -- Restore from history
    save            -- Saves as new version
    version         -- Retrieves saved version
    versions        -- Return generator of available versions

    Convenience
    -----------

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
from openmetadata import error
from openmetadata import service

log = logging.getLogger('openmetadata.api')


# Objects

"""

Location    -- Path to which metadata is associated
Variable    -- Dynamically typed metadata variable

"""

Location = lib.Location
Variable = lib.Variable


# Core Functionality


def commit(node):
    pass


def push():
    pass


def dump(node, track_history=True, simulate=False):
    assert isinstance(node, lib.Node)

    if node.haschildren:
        path = node.path.as_str

        service.dump_dir(path)

        for child in node:
            dump(child, track_history, simulate)

    else:
        assert node.path.suffix, node.path
        path = node.path.as_str
        value = node.dump()

        if track_history:
            if service.exists(path):
                _make_history(node)

        service.dump(path, value)

        log.info("_dump(): Successfully dumped: %r" % path)

    return node


def pull(node, lazy=False, depth=1, merge=False, _currentlevel=1):
    """Physically retrieve value from database

    Parameters
        lazy        -- Only pull if no existing value already exists
        depth       -- Pull `node` and `depth` levels of children
        merge       -- Combine results with existing value of `node`

    """

    path = node.path.as_str
    if not service.exists(path):
        # If the name of `node` has been entered manually, chances
        # are that the suffix does not match an existing node on disk.
        # If so, find a matching name, under any suffix, and assume
        # this is the one the user intended to pull from.
        name = node.path.name
        parent = node.path.parent
        similar = None

        try:
            found = find(parent.as_str, name)
            similar = next(found)
        except StopIteration:
            # No similar names could be found, it simply
            # does not exist. Sorry.
            pass

        if similar:
            node._path = node.rawpath.copy(path=similar)
            return pull(node,
                        lazy=lazy,
                        depth=depth,
                        merge=merge,
                        _currentlevel=_currentlevel)

        raise error.Exists("%s does not exist" % path)

    if lazy and node.hasvalue:
        return node

    if not merge:
        node.clear()

    if service.isdir(path):
        dirs, files = service.ls(path)
        for variable in dirs + files:
            Variable(variable, parent=node)
    else:
        # service.open(path)
        value = service.open(node.path.as_str)
        node.load(value)

    # Continue pulling children until `depth` is reached
    if _currentlevel < depth:
        if node.haschildren:
            for child in node:
                pull(child,
                     lazy=lazy,
                     depth=depth,
                     merge=merge,
                     _currentlevel=_currentlevel + 1)

    return node


def find(path, name):
    """Find `name` in `path`, regardless of suffix

    Return relative path to found variable

    Example
        Given the directory:

        parent
        |-- variable1.list
        |-- variable2.int
        |-- variable3.bool

        >> find(path, 'variable3')
        'variable3.bool'

    """
    try:
        dirs_, files_ = service.ls(path)
    except error.Exists:
        return

    for variable in dirs_ + files_:

        try:
            variable_no_suffix, _ = variable.rsplit(lib.Path.EXT, 1)
        except ValueError:
            variable_no_suffix = variable

        if variable_no_suffix == name:
            yield variable


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
        for match in find(trash_path.as_str, node.path.name):
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
    assert service.isfile(node.path.as_str), node.path
    copy = node.copy()

    try:
        parent = next(node.parent)

        # Avoid our `copy` adding itself as a child
        # to `parent`; this would cause the dictionary
        # containing the parents children to change.
        parent = parent.copy()
    except StopIteration:
        return

    print "Making history, this is parent: %s" % parent.path

    # Gather old value
    basename = node.path.basename
    imprint_time = service.currenttime()
    imprint_name = "{name}{sep}{time}".format(name=basename,
                                              sep='&',
                                              time=imprint_time)

    # Get previous value
    pull(copy, lazy=True)
    old_value = pull(copy).value

    # Construct history group
    history = Variable('.history', parent=parent)
    imprint = Variable(imprint_name, parent=history)

    Variable('user.string', value='marcus', parent=imprint)
    Variable('value', value=old_value, parent=imprint)

    dump(history, track_history=False)

    log.info("_make_history(): Successfully made history for %s (value=%s)"
             % (node, node.value))


# ---------------------------------------------------------------------
#
# Object-oriented Metadata, RFC12
# http://rfc.abstractfactory.io/spec/12/
#
# ---------------------------------------------------------------------


# def inherit(node, lazy=False):
#     assert isinstance(node, Variable)

#     # Find closest parent with metadata
#     # location = node.location
#     parent = node.location.path
#     metapath = node.path.meta

#     tree = []
#     while parent:
#         root = parent

#         try:
#             group = read(root.as_str, metapath, lazy=lazy, convert=False)

#             if group:
#                 print "Found %s" % group
#                 tree.append(group)

#         except error.Exists:
#             pass

#         parent = parent.parent

#     # Children overwrites parents
#     tree.reverse()

#     # print [t.path for t in tree]

#     children = {}
#     for element in tree:
#         # print "Merging %s" % element._children
#         for key, value in element.__children__().iteritems():
#             # print "\t " + key
#             if key in children:
#                 """
#                 TODO: Perform merge here
#                 At the moment, they replace each other.

#                 """

#             children[key] = value

#     node._children = children

#     return node


# def _inherit_blob(node, lazy=False):
#     assert isblob(node)

#     # Find closest parent with metadata
#     # location = node.location
#     parent = node.location.path
#     metapath = node.path.meta

#     while parent:
#         value = read(parent.as_str, metapath, lazy=lazy, convert=True)

#         if value and not isgroup(value):
#             break

#         parent = parent.parent

#     node.value = value


# ---------------------------------------------------------------------
#
# Convenience functions
#
# ---------------------------------------------------------------------


def _parse_metapath(metapath):
    if metapath:
        parts = metapath.split(lib.Path.METASEP)
    else:
        parts = []
    return parts


def read(path, metapath=None, convert=True, lazy=False):
    location = Location(path)

    root = location

    parts = _parse_metapath(metapath)
    while parts:
        try:
            pull(root, lazy=lazy)
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
            # print "%s did not exist in %s" % (name, root.path)
            return None

    try:
        pull(root, lazy=lazy)
    except error.Exists:
        return None

    if convert:
        # Convert values to native Python objects.
        #
        # This is a list of string for collections,
        # representing the keys of e.g. a folder, and
        # the actual value of a dataset, such as a file.
        if root.haschildren:
            children = []
            for child in root:
                children.append(child.path.name)
            return children
        else:
            return root.value

    else:
        # Return value as-is, meaning Open Metadata
        # objects Variable and Location objects.
        if root.haschildren:
            return root.value
        else:
            return root


def write(path, metapath, value=None):
    location = lib.Location(path)

    parts = _parse_metapath(metapath)

    root = location
    variables = parts
    for variable_name in variables:
        # As each predecessor is manually specified, there is
        # a chance that a collection of existing/different
        # suffix already exists. If so, use that.
        try:
            found = find(root.path.as_str, variable_name)
            variable_name = next(found)
        except StopIteration:
            pass

        variable = Variable(variable_name, parent=root)
        root = variable

    root.value = value

    assert root.path.suffix

    dump(root)


__all__ = [
    # Main objects
    'Location',
    # 'Node',
    'Variable',

    # Main functionality
    'dump',
    'read',
    'write',
    'pull',
    'remove'
    # 'exists',
    # 'existing',
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