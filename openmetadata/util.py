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

        # Suffixes are excluded
        >>> path = r'c:\users\marcus\.meta\group.list\special.string'
        >>> split(path)
        ('c:/users/marcus', '/group/special')

    """

    assert isinstance(path, basestring)
    path = lib.Path(path)
    return path.location.as_str, path.meta


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

        Ignore suffix

        >> find(path, 'entry3.int')
        'entry3.bool'

    """

    if not service.exists(path):
        return

    # Ignore suffix
    if not name.startswith('.'):
        name = name.split(lib.Path.EXT, 1)[0]

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
            entry_no_suffix = entry
        else:
            try:
                entry_no_suffix, _ = entry.rsplit(lib.Path.EXT, 1)
            except ValueError:
                entry_no_suffix = entry

        if ignore_case:
            name = name.lower()
            entry_no_suffix = entry_no_suffix.lower()

        if entry_no_suffix == name:
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
    home = os.path.expanduser('~/om/.trash')
    print find(home, '.meta')
