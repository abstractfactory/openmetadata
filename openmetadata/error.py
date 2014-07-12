

class Exists(Exception):
    """Raised upon error with existance; e.g. file does not exist"""


class RelativePath(Exception):
    pass


class Suffix(Exception):
    pass


class Serialisation(Exception):
    pass


class Corrupt(Exception):
    pass
