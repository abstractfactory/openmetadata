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

    Temporal
    --------

    history         -- Return generator of available history
    restore         -- Restore from history
    save            -- Saves as new version
    version         -- Retrieves saved version
    versions        -- Return generator of available versions

    Convenience
    -----------

    metadata        -- Convenience method for retrieving metadata objects
    read            -- Convenience method for reading metadata
    write           -- Convenience method for writing metadata
    ls              -- List metacontent of node

    isdataset       -- Self-explanatory convenience method
    isgroup         -- Self-explanatory convenience method
    ishistory       -- Self-explanatory convenience method
    isimprint       -- Self-explanatory convenience method

Note
    This module isn't to be used directly, all funcionality is
    imported by the __init__.py of 'openmetadata' and retreivable
    via the module directly.

    Example
        >> import openmetadata as om
        >> om.read('/home/marcus')

"""

import logging

from openmetadata import lib
from openmetadata import bug
from openmetadata import error
from openmetadata import service

METASEP = '/'
LOG = logging.getLogger('openmetadata.api')


# Objects

"""

Node        -- Superclass of below objects
Location    -- Represents physical entry in database
Group       -- Container of Group and/or Dataset nodes
Dataset     -- Main vessel of data

"""

Node = lib.Node
Location = lib.Location
Group = lib.GroupFactory
Dataset = lib.DatasetFactory
Imprint = lib.Imprint
History = lib.History


# Functionality


def _precheck(node):
    if node.haschildren:
        for child in node:
            _precheck(child)
    else:
        if not node.isvalid:
            raise ValueError("%s was not valid" % node.path.as_str)


def dump(node, nohistory=False, simulate=False):
    """
    Physically write to disk

    Description
        This method is what ultimately writes to disk; no data
        is modified in any way prior to this method being called.

    """
    _precheck(node)
    _dump(node, nohistory, simulate)


def _dump(node, nohistory=False, simulate=False):
    if node.haschildren:
        for child in node:
            _dump(child)

    else:
        assert node.path.suffix, bug.suffix_not_resolved()

        dataset = node

        path = dataset.path.as_str

        data = node.dump()

        if not simulate:
            if node.isdirty:
                if not nohistory:
                    _make_history(node)

                service.dump(path, data)

                LOG.info("_dump(): Successfully dumped: %r" % path)
            else:
                LOG.info("_dump(): Nothing dumped, data unchanged.")
        else:
            LOG.info("_dump(): Successfully simulated dump: %r" % path)


def pull(node, lazy=False, depth=1, merge=False, _level=1):
    """
    Main mechanism with which to read data from disk into memory.

    Parameters
        depth   -- How many levels of a hierarchy to pull
                   Example
                        parent           <-- level 0
                        |-- child        <-- level 1
                            |-- dataset  <-- level 2
        lazy    -- Only pull when no data is present
        merge   -- Preserve existing data


    """

    if not service.exists(node.path.as_str):
        node.isdirty = False

        raise error.Exists("%s does not exist" % node.path.as_str)

    if lazy and node.hasdata:
        return node

    if isinstance(node, lib.History):
        """
         . . . .
        .        .
        .         .
        .  12:00  .
        .         .
        . . . . . .

        History nodes contain `imprints`

        """

        dirs, files = service.ls(node.path.as_str)

        if not merge:
            node.clear()

        for imprint in dirs + files:
            lib.Imprint(imprint, parent=node)

    elif isinstance(node, lib.Dataset):
        """
         ______
        |       \
        |        |
        |   om   |
        |        |
        |________|

        Blobs return their data as-is

        """

        data = service.open(node.path.as_str)
        node.load(data)

    elif isinstance(node, lib.Group) or isinstance(node, lib.Location):
        """
         ____
        |    |_______
        |            |
        |     om     |
        |            |
        |____________|

        Containers may contain:
            o Groups
            o Datasets
            o History
            o Versions

        """

        path = node.path.as_str
        if hasattr(node, 'resolved_path'):
            path = node.resolved_path.as_str

        try:
            dirs, files = service.ls(path)
        except ValueError as e:
            raise error.Exists(e)

        if not merge:
            node.clear()

        for dir_ in dirs:
            if dir_ == lib.HISTORY:
                lib.History(dir_, parent=node)

            if dir_ == lib.VERSIONS:
                continue

            if dir_.startswith("."):
                continue

            lib.GroupFactory(dir_, parent=node)

        for file_ in files:
            if file_.startswith("."):
                continue

            lib.DatasetFactory(file_, parent=node)

    elif isinstance(node, lib.Blob):
        raise NotImplementedError("Can't read blobs yet")

    else:
        raise TypeError("Can't pull %r" % node)

    node.isdirty = False

    # Recursively pull until `depth` is reached
    _level += 1
    if not _level > depth:
        if node.haschildren:
            for child in node:
                if isblob(child):
                    continue

                print "Also pulling %r" % child.path
                # print "Also pulling %r" % child
                pull(child, lazy, depth, _level)

    return node


def remove(node, permanent=False):
    """Remove `node` from database, either to trash or permanently"""
    assert isinstance(node, lib.Node), bug.not_a_node(node)

    if not exists(node):
        LOG.warning("remove(): %s did not exist" % node.path.as_str)
        return False

    if permanent:
        service.remove(node.path.as_str)
        LOG.info("remote(): Permanently removed %r" % node.path.as_str)
        return

    trash_path = node.path + lib.TRASH

    # Ensure node.path.name is unique in trash_path, as per RFC14
    if service.exists(trash_path.as_str):
        dirs, files = service.ls(trash_path)
        for trashed in dirs + files:
            trash_name = trashed.split(node.EXT, 1)[0]
            if node.path.name == trash_name:
                # An existing copy of this node is
                # already in the trash_path. Permanently remove it.
                LOG.info("remove(): Removing exisisting "
                         "%r from trash" % node.path.name)
                existing_trashed_path = trash_path + trashed
                service.remove(existing_trashed_path.as_str)

    basename = node.path.basename
    deleted_path = trash_path + basename

    assert not service.exists(deleted_path.as_str), \
        bug.not_deleted(deleted_path.as_str)

    service.move(node.path.as_str, deleted_path.as_str)
    LOG.info("remove(): Successfully removed %r" % node.path.as_str)

    return True


def hasdata(path, metapath):
    """Convenience-method for querying the existance metadata"""
    try:
        read(path, metapath, native=False)
    except error.Exists:
        return False
    return True


def exists(node):
    """Check if `node` exists under any suffix"""
    if not node.hasparent:
        return False

    if isinstance(node, lib.Imprint):
        return service.exists(node.path.as_str)

    existing = []
    path = node.path.parent.as_str

    if not service.exists(path):
        return False

    dirs_, files_ = service.ls(path)

    for entry in dirs_ + files_:
        existing.append(entry.split(lib.Path.EXT)[0])

    # name = node.path.name
    return node.path.name in existing


# ---------------------------------------------------------------------
#
# Object-oriented Metadata, RFC12
# http://rfc.abstractfactory.io/spec/12/
#
# ---------------------------------------------------------------------


def inherit(node):
    raise NotImplementedError


# ---------------------------------------------------------------------
#
# Temporal Metadata, RFC14
# http://rfc.abstractfactory.io/spec/14/
#
# ---------------------------------------------------------------------


def save(node):
    """Save `node` as a new version"""
    return _make_version(node)


def versions(node):
    raise NotImplementedError
    """Return versions of `node`"""
    # raise NotImplementedError

    parent = node.parent

    pull(parent, lazy=True)

    versions_node = parent[lib.VERSIONS]
    if versions_node is None:
        return

    pull(versions_node, lazy=True)

    # TODO: potential bottleneck
    versions = [ver for ver in versions_node]
    versions = sorted(versions, reverse=True)

    for version in versions:
        if version == node:
            yield version


def version(node, number):
    raise NotImplementedError
    """Return `version` of `node`"""
    for version in versions(node):
        if version.number == number:
            return version


def history(node):
    """Return history of `node`"""
    parent = node.parent

    pull(parent, lazy=False)

    try:
        history_node = parent[lib.HISTORY]
    except KeyError:
        LOG.warning("No history found for %r" % node)
        return []

    pull(history_node, lazy=True)

    # TODO: potential bottleneck
    imprints = [imp for imp in history_node]
    imprints = sorted(imprints, reverse=True)

    def generator(imprints):
        for imprint in imprints:
            if imprint == node:
                yield imprint

    return generator(imprints)


def restore(imprint, keephistory=False):
    """Restore `imprint` to target from history"""
    assert isinstance(imprint, lib.Imprint)
    LOG.info("restore(): Restoring %r" % imprint.path)
    pull(imprint, lazy=True)

    target_parent = imprint.parent.parent

    try:
        target = target_parent[imprint.path.name]
    except KeyError:
        # If target doesn't exist, the imprint is
        # being restored into a new dataset.
        name = imprint.path.basename
        target = Dataset(name, parent=target_parent)

    # Update target with historical data
    assert 'value' in imprint, 'There is a bug'

    previous_value = imprint['value']
    current_value = target.data
    target.data = pull(previous_value).data

    dump(target, nohistory=True)

    # Remove history
    if not keephistory:
        for old_imprint in history(target):
            if old_imprint.time >= imprint.time:
                LOG.info("restore(): Removing old history: %r"
                         % old_imprint.path)
                remove(old_imprint, permanent=True)

    LOG.info("restore(): Restoring %r(%r) to %r(%r)" %
             (imprint.path, current_value, target.path, target.data))


def _make_history(node):
    """Create an imprint of `node` as per RFC14"""
    assert isdataset(node)

    if not service.exists(node.path.as_str):
        # Only create history for nodes
        # that are being updated.
        return

    pull(node, lazy=True)

    parent = node.parent
    basename = node.path.basename

    imprint_time = service.currenttime()
    imprint_name = "%s&%s" % (basename, imprint_time)

    # Get previous value
    current_value = node.data
    previous_value = pull(node).data
    node.data = current_value

    # Construct history group
    history = History(lib.HISTORY, parent=parent)
    imprint = Imprint(imprint_name, parent=history)

    print imprint_name
    # Dataset('user', data='marcus', parent=imprint)

    # lib.python_to_string(type(previous_value))
    # Dataset('value', data=previous_value, parent=imprint)

    assert not service.exists(imprint.path.as_str), \
        "%s already exists" % imprint.path

    # dump(history)

    LOG.info("_make_history(): Successfully made history for %s (value=%s)"
             % (node.path.as_str, node.data))


def _make_version(node, padding=3):
    if not exists(node):
        # Only create history for nodes
        # that are being updated.
        return

    pull(node, lazy=True)

    parent = node.parent

    # Construct history group
    versions = Group(lib.VERSIONS, parent=parent)

    # Latest version is n + 1 number of existing versions
    count = 0
    if service.exists(versions.path.as_str):
        count = service.count(versions.path.as_str)

    syntax = 'v%0' + str(padding) + 'd'
    imprint_name = syntax % (count + 1)

    imprint = Imprint(imprint_name, parent=versions)
    Dataset('user', data='marcus', parent=imprint)
    Dataset('value', data=node.data, parent=imprint)
    Dataset('time', data=service.currenttime(), parent=imprint)

    assert not exists(imprint)

    dump(versions)

    LOG.info("_make_history(): Successfully made a version of %s"
             % node.path.as_str)


# ---------------------------------------------------------------------
#
# Convenience functions
#
# ---------------------------------------------------------------------


def dumps(node):
    """Return hierarchy of `node` as a plain dictionary

    TODO: This is meant to simulate dump() but at the moment is
    performing a pull and returns all available data, both in-memory
    and on-disk. This isn't consistent

    """

    root = {}

    if not node.hasdata:
        pull(node)

    if node.haschildren:
        for child in node:
            root[child.name] = dumps(child)
    else:
        root = node.data

    return root


def read(path, metapath=None, native=True):
    """Retrieve Python objects via `path` and `metapath`

    Parameters
        path        -- Absolute path to associated directory
        metapath    -- A concatenated path to metadata
                       e.g. '/parent/child/subchild'
        native      -- Return native python objects
                       False
    """

    location = lib.Location(path)
    if metapath is None:
        return location

    root = location

    parts = metapath.split(lib.Path.METASEP)

    while parts:
        pull(root)

        current = parts.pop(0)
        while current == '':
            current = parts.pop(0)

        # Remove suffix for query
        name, suffix = (current.rsplit(lib.Path.EXT, 1) + [None])[:2]

        try:
            root = root[name]

            # If metapath included a suffix,
            # ensure the child we fetch match this suffix.
            if suffix:
                if not root.suffix == suffix:
                    raise KeyError

        except KeyError:
            raise error.Exists("%s does not exist" % name)

    pull(root)

    if root.haschildren:
        if native:
            children = []
            for child in root:
                children.append(child.path.name)
            return children
        else:
            return root.children

    if native:
        return root.data
    else:
        return root


def write(path, metapath, data=None):
    """
    Convenience-method for quickly writing out `data` to `path`

    Example
        >> om.write(r'c:\users\marcus', 'Hello there', 'introduction')

    """

    location = lib.Location(path)

    parts = metapath.split(METASEP)
    dataset = parts.pop()
    groups = parts
    root = location
    for group in groups:
        group = lib.GroupFactory(group, parent=root)
        root = group

    # Is it a group or a dataset?
    if data is None:
        typ = None
    else:
        typ = type(data)
    item_type = lib.python_to_om(typ)

    dataset = item_type(dataset, data=data, parent=root)
    dump(dataset)


def ls(root, depth=1, _level=0):
    """List contents of `root`

    Example
        >>> group = Group('a group')
        >>> child1 = Dataset('a child', parent=group)
        >>> child2 = Dataset('another child', parent=group)
        >>> ls(group)
        a child
        another child

    """

    if isinstance(root, basestring):
        root = Location(root)

    # current_depth = 0
    if _level > depth:
        return

    if root.haschildren:
        if exists(root):
            pull(root, merge=True)

        for node in root:
            print '\t' * (_level-1) + node.path.name
            ls(node, depth, _level + 1)


def islocation(node):
    return isinstance(node, lib.Location)


def isblob(node):
    return isinstance(node, lib.Blob)


def isdataset(node):
    return isinstance(node, lib.Dataset)


def isgroup(node):
    return isinstance(node, lib.Group)


def isimprint(node):
    return isinstance(node, lib.Imprint)


def ishistory(node):
    return isinstance(node, lib.History)


# Convenience wrappers


# om.listdir() is identical to os.listdir() except for
# returning Open Metadata objects rather than Python strings.
# listdir = lambda path: read(path)


__all__ = [
    # Main objects
    'Node',
    'Location',
    'Group',
    'Dataset',
    'Imprint',
    'History',

    # Main functionality
    'dump',
    # 'dumps',  # On-hold, due to ambivalent functionality
    'read',
    'write',
    'pull',
    'ls',
    'exists',
    'restore',
    'remove',
    'history',

    # Convenience functionality
    # 'listdir',  # On-hold, possibly frivilous
    'hasdata',
    'islocation',
    'isdataset',
    'isgroup',
    'ishistory',
    'isimprint',
    # 'read_as_dict'  # About to be replaced by HDF5-like impl.
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