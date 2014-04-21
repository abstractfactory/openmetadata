from openmetadata import lib
from openmetadata import service
from openmetadata import error


def locations(path):
    """Return available locations, starting from path

    Look for existing metadata in path, parent of path, and so forth,
    returning each location containing a metadata container.

    """

    if isinstance(path, basestring):
        path = lib.Path(path)

    root = path
    while root:
        location_path = root + lib.Path.CONTAINER

        if service.exists(location_path.as_str):
            yield lib.Location(root)

        root = root.parent


def parse_metapath(metapath):
    if metapath:
        parts = metapath.split(lib.Path.METASEP)
    else:
        parts = []
    return parts


def find_all(path, name):
    """Find `name` in `path`, regardless of suffix

    Return relative path to found entry

    Example
        Given the directory:

        parent
        |-- entry1.list
        |-- entry2.int
        |-- entry3.bool

        >> find(path, 'entry3')
        'entry3.bool'

    """

    try:
        dirs_, files_ = service.ls(path)
    except error.Exists:
        return

    for entry in dirs_ + files_:

        if entry.startswith('.'):
            entry_no_suffix = entry
        else:
            try:
                entry_no_suffix, _ = entry.rsplit(lib.Path.EXT, 1)
            except ValueError:
                entry_no_suffix = entry

        if entry_no_suffix == name:
            yield entry


def find(path, name):
    try:
        found = find_all(path, name)
        return next(found)
    except StopIteration:
        return None
