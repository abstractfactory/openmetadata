import re

PARENT_DIR = '..'
CURRENT_DIR = '.'


class Path(object):
    """
    Generic path object.

    Path objects are, like PurePath of pathlib, not performing
    any actual I/O, but merely manipulating the string value
    of passed string.

    Based on PEP-428 a.k.a. pathlib
    http://www.python.org/dev/peps/pep-0428

     ___________
    |           |
    |   Input   |
    |___________|
          |
          |
       ___v___
      |       |
      | Parse |
      |_______|
          |
          |
     _____v______
    |            |
    | Processing |
    |____________|
          |
          |
      ____v____
     |         |
     | Deparse |
     |_________|
          |
          |
     _____v____
    |          |
    |  Output  |
    |__________|

    """

    FAMILY = None
    SEPARATOR = '/'

    SuffixPattern = re.compile(r'\..*$')
    EscapePattern = re.compile(r'\\')
    MultipleSlashPattern = re.compile(r'(/)\1+')

    def __str__(self):
        return self.as_str or ''

    def __repr__(self):
        return u"%s(%r)" % (self.__class__.__name__, self.__str__())

    def __hash__(self):
        return hash(self.as_str)

    def __nonzero__(self):
        return True if self._path else False

    def __eq__(self, other):
        return str(other) == self.as_str

    def __ne__(self, other):
        return str(other) != self.as_str

    def __add__(self, other):
        sep = self.SEPARATOR
        new_path = sep.join([self.as_str, str(other)])
        return self.copy(path=new_path)

    def __init__(self, path):
        """
        Path is immediately parsed and thus
        never stored as-is.

        This is important to remember when accessing path
        via the protected instance attribute `_path` which
        is meant for subclasses only.

        """

        assert isinstance(path, basestring), path

        self._path = self.parse(path)
        self.__suffix = None

        # Memoized attributes
        self.__as_str = None

    def copy(self, path=None):
        return self.__class__(path or self._path)

    @classmethod
    def parse(cls, path):
        """Conform incoming `path` to using only single forward slashes"""
        path_ = re.sub(Path.EscapePattern, '/', path)
        path_ = re.sub(Path.MultipleSlashPattern, r'\1', path_)
        path_ = path_.replace(cls.SEPARATOR, '/')
        path_ = path_.rstrip('/')

        parts = path_.split("/")
        for part in list(parts):
            # Resolve "parent" dir
            #
            # Example
            #   /absolute/path/with/../..   --> /absolute
            #   /absolute/../absolute       --> /absolute
            #   /absolute/.                 --> /absolute
            #
            if part == PARENT_DIR:
                index = parts.index(part)
                parts.pop(index)
                parts.pop(index - 1)

            # Resolve "current" dir
            #
            # Example
            #   /my/absolute/path/.         --> /my/absolute/path
            #
            if part == CURRENT_DIR:
                index = parts.index(part)
                parts.pop(index)

        path_ = '/'.join(parts)

        return path_

    def deparse(self):
        """
        De-conform `path` to match original

        Parsing can happen without an instance of the class, deparsing
        however relies on details about the instance and can only
        be used with instances.

        """

        path = self._path.replace('/', self.SEPARATOR)
        return path

    @property
    def name(self):
        """Return name excluding suffix"""
        name = self._path.split('/')[-1] or self._path

        suffix = self.suffix
        if suffix:
            name = name[:-len(suffix)]

        return name

    @property
    def basename(self):
        """Return name including suffix"""
        path = self.as_str
        basename = path.rsplit(self.SEPARATOR, 1)[-1]
        return basename or path

    @property
    def parent(self):
        """Return the pure parent of a path.

        The pure parent is that which can be derived simply by
        parsing the string value of the path.

        """

        path = self._path

        # if path == '/':
        #     return None

        parent = path.rsplit('/', 1)[0]

        if not parent or parent == path:
            # parent is '' when path == SEPARATOR
            # parent == _path when _path is root
            # parent = '/'
            return None

        return self.__class__(parent)

    @property
    def parents(self):
        r"""Return each parent as absolute paths

        Example
            >> path = WindowsPath(r'c:\windows\system32')
            >> assert (path.parents == ['c:\\', 'c:\\windows'])

        """

        parent = self.parent
        parents = []
        while parent:
            parents.insert(0, parent)
            parent = parent.parent

        return parents

    @property
    def body(self):
        """Return path without root"""
        if self.root:
            return self._path[1:]
        return self._path

    @property
    def root(self):
        """Retun only root, if one exists"""
        if self._path.startswith('/'):
            return '/'
        return None

    @property
    def suffix(self):
        if not self.__suffix:
            basename = self.basename
            match = self.SuffixPattern.search(basename)
            if match:
                self.__suffix = match.group(0)
        return self.__suffix

    def startswith(self, predicate):
        return self.as_str.startswith(predicate)

    @property
    def as_raw(self):
        """Return string without deparsing"""
        return self._path

    @property
    def as_str(self):
        """Return the composed version of `path`"""
        if not self.__as_str:
            self.__as_str = self.deparse()
        return self.__as_str

    def to_str(self):
        """Convenience method for when you would rather call a method"""
        return self.as_str

    @property
    def isabsolute(self):
        return True if self.root else False

    @property
    def isrelative(self):
        return False if self.root else True

    @property
    def isroot(self):
        return True if self._path == '/' else False


class UnknownPath(Path):
    """Used where type of path couldn't be determined"""


class VirtualPath(Path):
    """Non-existant paths"""


class DirPath(Path):
    """This superclass exists purely for reasons of being able to
    refer to the two subclasses, WindowsPath and PosixPath, via a
    isinstance and issubclass"""

    FAMILY = 'dir'


class WindowsPath(DirPath):
    r"""
    Specialisation of Path with features for Windows

    Internally
        As opposed to conventional windows paths which makes
        use of the concept of 'drives', WindowPath treats each
        drive as just another folder, the root being one level
        above the drive.

        E.g.
            c:\windows\system32 == \c\windows32\system32

    """

    SEPARATOR = '\\'

    DrivePattern = re.compile(r'^\w:')

    def __init__(self, *args, **kwargs):
        super(WindowsPath, self).__init__(*args, **kwargs)

    @classmethod
    def parse(cls, path):
        _path = super(WindowsPath, cls).parse(path)

        match = cls.DrivePattern.search(_path)
        if match:
            drive = match.group(0)
            parsed_drive = '/' + drive.rstrip(":")
            _path = _path.replace(drive, parsed_drive)

        return _path

    def deparse(self):
        path = super(WindowsPath, self).deparse()

        if self.root:
            # Special case, '/' represents c-drive.
            # In the future, expand on the concept
            # to make '/' represent a logical folder
            # _above_ all drives.
            #
            # Example
            #   WindowsNode('/').children
            #       -> returns available drives.
            if self.root == path:
                return 'c:\\'

            path = self.drive + self.SEPARATOR + path[3:]

        return path

    @property
    def drive(self):
        if self.root:
            drive = self._path[1:2] + ":"
            return drive
        return None


class PosixPath(DirPath):
    SEPARATOR = '/'

    def __init__(self, *args, **kwargs):
        super(PosixPath, self).__init__(*args, **kwargs)


class MetaPath(DirPath):
    SEPARATOR = '/'


if __name__ == '__main__':
    p = WindowsPath(r's:\absolute\path.ast\onemore\..')
    print p.suffix
    # print p + '..'
    # print p + '../..'
    # print p + '../.'
    # print p + './published'