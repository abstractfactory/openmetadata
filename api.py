"""
-----------------------------------------------------------------------

Open Metadata API

-----------------------------------------------------------------------

Description
    pass

Functionality
    dump            -- Main mechanism with which to write to database
    pull            -- Main mechanism with which to read from database
    remove          -- Main mechanism with which to remove from database
    read            -- Convenience method for reading metadata
    read_as_dict    -- Convenience method of `read`, returns dict
    write           -- Convenience method for writing metadata
    exists          -- Does a node exist?
    dumps           -- Simulates `dump` and returns dict
    isdataset       -- Self-explanatory convenience method
    isgroup         -- Self-explanatory convenience method

Note
    This module isn't to be used directly, all funcionality is
    imported by the main 'openmetadata' module.

"""

import time
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
            if not nohistory:
                _make_history(node)

            service.dump(path, node.dump())

            LOG.info("_dump(): Successfully dumped: %r" % path)
        else:
            LOG.info("_dump(): Successfully simulated dump: %r" % path)


def _make_history(node):
    """Create an imprint of `node` as per RFC14"""

    if not exists(node):
        # Only create history for nodes
        # that are being updated.
        return

    parent = node.parent
    basename = node.basename
    repository_path = SEP.join([parent.path, lib.HISTORY])

    history_time = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    history_basename = "%s&%s" % (basename, history_time)
    history_path = SEP.join([repository_path, history_basename])

    service.copy(node.path, history_path)


def _make_version(node):
    pass


def dumps(node):
    """Return hierarchy of `node` as a plain dictionary"""
    root = {}

    if hasattr(node, 'children'):
        for child in node:
            root[child.name] = dumps(child)
    else:
        root = node.data

    return root


def read(path, *metapaths):
    """Parse information from database into Python data-types"""
    location = lib.Location(path)

    root = location

    for metapath in metapaths:
        parts = metapath.split(SEP)
        while parts:
            pull(root)
            root = root._children.get(parts.pop(0))

            if not root:
                return None

    pull(root)
    return root.data

    # nodes = []
    # for node in root:

    #     # Skip instances of History
    #     if isinstance(node, lib.History):
    #         continue

    #     nodes.append(node)

    # return nodes


def read_as_dict(path, *metapaths):
    result = {}
    for node in read(path, *metapaths):
        result[node.name] = node

    return result


def write(path, data, *metapaths):
    """
    Convenience-method for quickly writing out `data` to `path`

    Example
        >> om.write(r'c:\users\marcus', 'Hello there', 'introduction')

    """

    location = lib.Location(path)

    metapaths = list(metapaths)
    dataset = metapaths.pop()
    groups = metapaths
    root = location
    for group in groups:
        group = lib.GroupFactory(group, parent=root)
        root = group

    # Is it a group or a dataset?
    item_type = lib.python_to_om(type(data))

    dataset = item_type(dataset, data=data, parent=root)
    service.dump(dataset)


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

    elif isinstance(node, lib.Dataset) or isinstance(node, lib.Imprint):
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


def restore(imprint):
    """Restore `imprint` from history"""
    assert isinstance(imprint, lib.Imprint)

    LOG.info("restore(): Restoring %r" % imprint.path)

    pull(imprint)

    original_parent = imprint.parent.parent

    # Is the original being updated or created?
    original = original_parent.children_as_dict.get(imprint.original_name)
    if not original:
        original = Dataset(imprint.original_basename, parent=original_parent)

    # Update original with historical data
    original.data = imprint.data

    dump(original, nohistory=True)

    # Remove history
    for old_imprint in history(original):
        if imprint.time >= old_imprint.time:
            LOG.info("restore(): Removing old history: %r" % old_imprint.path)
            remove(old_imprint, permanent=True)

    LOG.info("restore(): Restoring %r to %r" % (imprint.path, original.path))


def history(node):
    """Return history of `node`"""
    history_node = node.parent.children_as_dict.get('.history')

    if not node.hasdata:
        pull(history_node)

    history = []
    for imprint in history_node.children:
        if imprint == node:
            history.append(imprint)
    return history


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


def isdataset(node):
    return True if isinstance(node, lib.Dataset) else False


def isgroup(node):
    return True if isinstance(node, lib.Group) else False


def isimprint(node):
    return True if isinstance(node, lib.Imprint) else False


def ishistory(node):
    return True if isinstance(node, lib.History) else False


# Convenience wrappers


listdir = read


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
    'dumps',
    'read',
    'write',
    'pull',
    'exists',
    'restore',
    'remove',

    # Convenience functionality
    'listdir',
    'isdataset',
    'isgroup',
    'ishistory',
    'isimprint',
    'read_as_dict'
]


if __name__ == '__main__':
    from pprint import pprint
    import openmetadata as om
    path = r'c:\users\marcus\om2'
    location = om.Location(path)
    om.pull(location)
    pprint(om.dumps(location))
    # group = om.read_as_dict(path, 'root').get('group')
    # print group
    # om.remove(group)

    # print age
    # print history(age)
    # om.pull(location)

    # history_ = om.read_as_dict(path).get('.history')
    # om.pull(history_)
    # imprint = history_.children[0]
    # # print om.exists(imprint)
    # print repr(imprint)
    # om.restore(imprint)
    # # print history.path
    # print history.name
