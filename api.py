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
    find            -- Return generator of matches

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
            node._path = node.raw_path.copy(path=similar)
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
            variable = {}
    else:
        # service.open(path)
        value = service.open(node.path.as_str)
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

        if variable.startswith('.'):
            variable_no_suffix = variable
        else:
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
        # containing the parent's children to change.
        #   Python doesn't like this.
        parent = parent.copy()
    except StopIteration:
        return

    # Gather old value
    name = node.path.name
    imprint_time = service.currenttime()
    imprint_name = "{name}{sep}{time}".format(name=name,
                                              sep=lib.Path.OPTSEP,
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

    parent = node.location.path
    metapath = node.path.meta

    tree = []
    level = 1
    while parent:
        variable = read(parent.as_str, metapath, convert=False)
        if variable:
            tree.append(variable)

        if depth and level > depth:
            break

        level += 1
        parent = parent.parent

    # Children overwrites parents
    tree.reverse()

    if not merge:
        node.clear()

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
            for variable in entry:
                node.add(variable)
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
        # `Variable` and `Location` objects.

        if root.iscollection:
            # Output
            #   --> [Variable('child'), Variable('anotherchild')]
            value = root.value
            if value:
                assert isinstance(value, dict)
                return value.values()

        else:
            # Output
            #   --> Variable('child')

            return root


def write(path, metapath, value=None):
    location = lib.Location(path)

    parts = util.parse_metapath(metapath)

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


def isvariable(node):
    return isinstance(node, lib.Variable)


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
    'remove',
    'clear',
    # 'exists',
    # 'existing',
    'inherit',
    'history',
    'restore',
    'islocation',
    'isvariable'
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