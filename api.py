"""
-----------------------------------------------------------------------

Open Metadata API

-----------------------------------------------------------------------

Description
    pass

Functionality

    Main
    ----

    dump            -- Main mechanism with which to write to database
    pull            -- Main mechanism with which to read from database
    remove          -- Main mechanism with which to remove from database

    Temporal
    --------

    history         -- Returns generator of available history
    restore         -- Restores node from history
    save            -- Saves node as new version
    version         -- Retrieves saved version
    versions        -- Returns generator of available versions

    Convenience
    -----------

    metadata        -- Convenience method for retrieving metadata objects
    read            -- Convenience method for reading metadata
    write           -- Convenience method for writing metadata
    exists          -- Does a node exist?
    dumps           -- Simulates `dump` and returns dict
    lazy_pull       -- Pulls only if not previously pulled

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
from openmetadata import error
from openmetadata import service

SEP = service.SEP
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
    if hasattr(node, 'children'):
        for child in node:
            _precheck(child)
    else:
        if not node.isvalid:
            raise ValueError("%s was not valid" % node.path)


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
    if hasattr(node, 'children'):
        for child in node:
            _dump(child)

    else:
        dataset = node

        path = dataset.path

        if not simulate:
            if node.isdirty:
                if not nohistory:
                    _make_history(node)

                service.dump(path, node.dump())

                LOG.info("_dump(): Successfully dumped: %r" % path)
            else:
                LOG.info("_dump(): Nothing dumped, data unchanged.")
        else:
            LOG.info("_dump(): Successfully simulated dump: %r" % path)


def pull(node):
    """
    Main mechanism with which to read data from disk into memory.

    Features
        '.'  -- Names starting with a dot (.) are invisible
                to regular operation and may be used by other
                mechanisms for other purposes; such as meta-
                metadata and history.

    """

    if not service.exists(node.path):
        node.isdirty = False

        raise error.Exists("%s does not exist" % node.path)

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

        dirs, files = service.readdir(node.path)

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

        node.data = service.readfile(node.path)

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

        dirs, files = service.readdir(node.path)

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

    return node


def lazy_pull(node):
    """Only pull if `node` doesn't already have data

    This is the direct equivalent to
        >> if not node.hasdata:
        >>     pull(node)

    """

    if not node.hasdata:
        pull(node)

    return node


def remove(node, permanent=False):
    """Remove `node` from database, either to trash or permanently"""
    assert isinstance(node, lib.Node)

    if not exists(node):
        LOG.warning("remove(): %s did not exist" % node.path)
        return False

    if permanent:
        service.remove(node.path)
        LOG.info("remote(): Permanently removed %r" % node.path)
        return

    dirname = node.parent.path
    basename = node.basename
    trash = service.SEP.join([dirname, lib.TRASH])

    # Ensure node.name is unique in trash, as per RFC14
    if service.exists(trash):
        dirs, files = service.readdir(trash)
        for trashed in dirs + files:
            trash_name = trashed.split(node.EXT, 1)[0]
            if node.name == trash_name:
                # An existing copy of this node is
                # already in the trash. Permanently remove it.
                LOG.info("remove(): Removing exisisting "
                         "%r from trash" % node.name)
                existing_trashed_path = service.SEP.join([trash, trashed])
                service.remove(existing_trashed_path)

    deleted_path = service.SEP.join([trash, basename])

    assert not service.exists(deleted_path), \
        "This should have been taken care of above"

    service.move(node.path, deleted_path)
    LOG.info("remove(): Successfully removed %r" % node.path)

    return True


def exists(node):
    """Check if `node` exists under any suffix"""
    if isinstance(node, lib.Imprint):
        return service.exists(node.path)

    if not service.exists(node.parent.path):
        return False

    existing = []
    dirs_, files_ = service.readdir(node.parent.path)
    for entry in dirs_ + files_:
        existing.append(entry.split(".")[0])

    return node.name in existing


# ---------------------------------------------------------------------
#
# Temporal Metadata, RFC14
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

    lazy_pull(parent)

    versions_node = parent.children_as_dict.get(lib.VERSIONS)
    if versions_node is None:
        return

    lazy_pull(versions_node)

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

    lazy_pull(parent)

    history_node = parent.children_as_dict.get(lib.HISTORY)
    if history_node is None:
        return

    lazy_pull(history_node)

    # TODO: potential bottleneck
    imprints = [imp for imp in history_node]
    imprints = sorted(imprints, reverse=True)

    for imprint in imprints:
        if imprint == node:
            yield imprint


def restore(imprint, keephistory=False):
    """Restore `imprint` to target from history"""
    assert isinstance(imprint, lib.Imprint)
    LOG.info("restore(): Restoring %r" % imprint.path)
    lazy_pull(imprint)

    target_parent = imprint.parent.parent

    neighbours = target_parent.children_as_dict
    target = neighbours.get(imprint.target_name)
    if not target:
        # If target doesn't exist, the imprint is
        # being restored into a new dataset.
        name = imprint.target_basename
        target = Dataset(name, parent=target_parent)

    # Update target with historical data
    previous_value = imprint.children_as_dict.get('value')
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

    if not exists(node):
        # Only create history for nodes
        # that are being updated.
        return

    lazy_pull(node)

    parent = node.parent
    basename = node.basename

    imprint_time = service.currenttime()
    imprint_name = "%s&%s" % (basename, imprint_time)

    # Get previous value
    current_value = node.data
    previous_value = pull(node).data
    node.data = current_value

    # Construct history group
    history = Group(lib.HISTORY, parent=parent)
    imprint = Imprint(imprint_name, parent=history)
    Dataset('user', data='marcus', parent=imprint)
    Dataset('value', data=previous_value, parent=imprint)

    assert not service.exists(imprint.path), "%s already exists" % imprint.path

    dump(history)

    LOG.info("_make_history(): Successfully made history for %s (value=%s)"
             % (node.path, node.data))


def _make_version(node):
    if not exists(node):
        # Only create history for nodes
        # that are being updated.
        return

    lazy_pull(node)

    parent = node.parent

    # Construct history group
    versions = Group(lib.VERSIONS, parent=parent)

    # Latest version is n + 1 number of existing versions
    count = 0
    if service.exists(versions.path):
        count = service.count(versions.path)

    imprint_name = 'v%03d' % (count + 1)

    imprint = Imprint(imprint_name, parent=versions)
    Dataset('user', data='marcus', parent=imprint)
    Dataset('value', data=node.data, parent=imprint)
    Dataset('time', data=service.currenttime(), parent=imprint)

    assert not exists(imprint)

    dump(versions)

    LOG.info("_make_history(): Successfully made a version of %s" % node.path)


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

    if hasattr(node, 'children'):
        for child in node:
            root[child.name] = dumps(child)
    else:
        root = node.data

    return root


def metadata(path, metapath):
    """Retrieve Open Metadata objects via `path` and `metapath`

    Description
        `metapath` MUST be specified as a concatenated path
        >> metapath = '/parent/child/subchild'

    """

    location = lib.Location(path)

    root = location

    parts = metapath.split(Node.SEP)

    while parts:
        pull(root)

        current = parts.pop(0)
        while current == '':
            current = parts.pop(0)

        try:
            root = root.children_as_dict[current]
        except KeyError:
            raise error.Exists("%s does not exist" % current)

    return root


def read(path, metapath):
    """Retrieve Python objects via `path` and `metapath`"""
    root = metadata(path, metapath)

    if isgroup(root):
        return dumps(root)

    return pull(root).data


# def read_as_dict(path, metapath):
#     result = {}
#     for node in read(path, metapath):
#         result[node.name] = node

#     return result


def write(path, metapath, data):
    """
    Convenience-method for quickly writing out `data` to `path`

    Example
        >> om.write(r'c:\users\marcus', 'Hello there', 'introduction')

    """

    location = lib.Location(path)

    # metapaths = list(metapaths)
    parts = metapath.split(Node.SEP)
    dataset = parts.pop()
    groups = parts
    root = location
    for group in groups:
        group = lib.GroupFactory(group, parent=root)
        root = group

    # Is it a group or a dataset?
    item_type = lib.python_to_om(type(data))

    dataset = item_type(dataset, data=data, parent=root)
    dump(dataset)


def isdataset(node):
    return True if isinstance(node, lib.Dataset) else False


def isgroup(node):
    return True if isinstance(node, lib.Group) else False


def isimprint(node):
    return True if isinstance(node, lib.Imprint) else False


def ishistory(node):
    return True if isinstance(node, lib.History) else False


# Convenience wrappers


# om.listdir() is identical to os.listdir() except for
# returning Open Metadata objects rather than Python strings.
listdir = lambda path: read(path)


__all__ = [
    # Main objects
    'Node',
    'Location',
    'Group',
    'Dataset',
    'Imprint',
    'History',

    # Main functionality
    'metadata',
    'dump',
    'dumps',
    'read',
    'write',
    'pull',
    'exists',
    'restore',
    'remove',
    'history',

    # Convenience functionality
    'listdir',
    'isdataset',
    'isgroup',
    'ishistory',
    'isimprint',
    # 'read_as_dict'
]


if __name__ == '__main__':
    # from pprint import pprint
    import openmetadata as om
    om.setup_log('openmetadata')

    path = r'c:\users\marcus\om2'
    age = om.metadata(path, '/age')
    print repr(age)
    age = om.metadata(path, 'age')
    print repr(age)
    # om.pull(age)

    # previous = age.data

    # age.data = age.data + 1
    # om.dump(age)

    # _make_version(age)

    # print new_imprint.time > old_imprint.time
    # print older_imprint.time > older_imprint.time
    # print imprint.time
    # imprint = om.history(age).next()
    # print "Previous: %s" % previous
    # print "Current: %s" % om.dumps(imprint)

    # om.restore(new_imprint)
    # om.pull(imprint)
    # print om.dumps(imprint)
    
    # print dumps(Location(path))