from openmetadata import lib
from openmetadata import service
from openmetadata import error


__all__ = [
    'split',
    'find_all',
    'find',
    'default',
]


def default(suffix):
    return lib.defaults.get(suffix)


def split(path):
    r"""Separate location from metapath

    Example
        >>> path = r'c:\users\marcus\.meta\key'
        >>> split(path)
        ('c:/users/marcus', '/key')

        >>> path = r'c:\users\marcus'
        >>> split(path)
        ('c:/users/marcus', None)

        >>> path = r'c:\users\marcus\.meta\group.list\special.string'
        >>> split(path)
        ('c:/users/marcus', '/group.list/special.string')

    """

    assert isinstance(path, basestring)
    path = lib.Path(path)

    try:
        path, meta = path.as_raw.split(lib.Path.CONTAINER, 1)
        path = path[:-1]  # Trailing slash
    except ValueError:
        path, meta = path.as_raw, None

    return path, meta


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


def find_all(path, name, **kwargs):
    """Find `name` in `path`

    Suffix:
        If no suffix is supplied with `name`, suffixes are
        ignored. E.g. this will return `myname.bool` if such
        an entry exists.
            >> find(path, 'myname')

        However, this will not
            >> find(path, 'myname.int')

    Returns:
        Relative path to found entry

    Example
        Given the directory:

        parent
        |-- entry1.list
        |-- entry2.int
        |-- entry3.bool

        >> find(path, 'entry3')
        'entry3.bool'

        Respect suffix

        >> find(path, 'entry3.int')
        None

    """

    if not service.exists(path):
        return

    # Ignore suffix
    suffix = None
    if not name.startswith('.'):
        try:
            name, suffix = name.split(lib.Path.EXT, 1)
        except ValueError:
            pass

    # Hidden arguments
    ignore_case = kwargs.get('ignore_case', True)

    if isinstance(path, basestring):
        path = lib.Path(path)

    container = lib.Path.CONTAINER
    if not container in path.as_str:
        path = path + container

    try:
        dirs_, files_ = service.ls(path.as_str)
    except error.Exists:
        return

    for entry in dirs_ + files_:

        if entry.startswith('.'):
            search_name = entry
            search_suffix = None
        else:
            try:
                search_name, search_suffix = entry.rsplit(lib.Path.EXT, 1)
            except ValueError:
                search_name, search_suffix = entry, None

        if ignore_case:
            name = name.lower()
            search_name = search_name.lower()

        if search_name == name:
            # If there was a suffix supplied, ensure they match
            if suffix:
                if search_suffix == suffix:
                    yield entry
            else:
                yield entry


def find(path, name):
    try:
        found = find_all(path, name)
        return next(found)
    except StopIteration:
        return None


def search(path, name):
    """Recursuvely find `name` within directory tree of `path`"""
    raise NotImplementedError


if __name__ == '__main__':
    import doctest
    doctest.testmod()

    import os
    home = os.path.expanduser('~/om')
    print find(home, 'address')
