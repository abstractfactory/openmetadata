from openmetadata import lib
from openmetadata import service


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
            yield root

        root = root.parent


def parse_metapath(metapath):
    if metapath:
        parts = metapath.split(lib.Path.METASEP)
    else:
        parts = []
    return parts
