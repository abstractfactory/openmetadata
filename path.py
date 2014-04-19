import re
import logging


class Path(object):
    """
    Generic path object.

    Path objects are, like PurePath of pathlib, not performing
    any actual I/O, but merely manipulating the string value
    of passed string.

    Based on PEP-428 a.k.a. pathlib
    http://www.python.org/dev/peps/pep-0428

     ___________       _________
    |           |     |         |
    |   Input   |---->|  parse  |
    |___________|     |_________|
                           |
                           |
                     ______v_____
                    |            |
                    | processing |
                    |____________|
                           |
                           |
     __________        ____v____
    |          |      |         |
    |  output  |<-----| deparse |
    |__________|      |_________|


    Path Structure

        [path]&[option]

        /root/child&options_here

    """

    log = logging.getLogger('openmetadata.path.Path')

    EXT = '.'
    PARENT_DIR = '..'
    CURRENT_DIR = '.'
    CONTAINER = '.meta'
    OPTIONDIV = '&'
    SEPARATOR = '/'
    METASEP = '/'  # Separator of metapaths
    PROCSEP = '/'  # Separator of `processing` (see above)
    FAMILY = None

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

        path = self.parse(path)
        path, option = self.splitoption(path)

        self._path = path
        self.__suffix = None
        self.__option = option

        # Memoized attributes
        self.__as_raw = None
        self.__as_str = None

    def copy(self, path=None, basename=None, suffix=None):
        """
        Example
            >>> path = Path('/home/marcus/file.exe')
            >>> path.copy()
            Path('/home/marcus/file.exe')

            >>> path.copy(path='/new/path.bat')
            Path('/new/path.bat')

            >>> path.copy(suffix='bat')
            Path('/home/marcus/file.bat')

            >>> path = Path('/home/no/suffix')
            >>> path.copy(suffix='exe')
            Path('/home/no/suffix.exe')

            >>> path = Path('/home/marcus')
            >>> path.copy(basename='lucas')
            Path('/home/lucas')

            >>> path = Path('/')
            >>> path.copy(basename='lucas')
            Path('')

        """

        path = path or self._path

        if basename:
            try:
                path, _ = path.rsplit(self.PROCSEP, 1)
                path = self.PROCSEP.join([path, basename])
            except ValueError:
                self.log.warning("Skipping: Could not replace "
                                 "basename of: %r" % path)
                pass

        if suffix:
            # Add or replace suffix
            current_suffix = self.suffix
            if current_suffix:
                path = path[:-(len(current_suffix) + 1)]
            path = path + self.EXT + suffix

        return self.__class__(path)

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
            if part == cls.PARENT_DIR:
                index = parts.index(part)
                parts.pop(index)
                parts.pop(index - 1)

            # Resolve "current" dir
            #
            # Example
            #   /my/absolute/path/.         --> /my/absolute/path
            #
            if part == cls.CURRENT_DIR:
                index = parts.index(part)
                parts.pop(index)

        path_ = '/'.join(parts)

        return path_

    @classmethod
    def splitoption(cls, path):
        """
        Example
            >>> path = Path('/home/marcus&options')
            >>> path.option
            'options'
            >>> path = Path('test&options')
            >>> path.option
            'options'
        """

        parts = path.split(cls.PROCSEP)
        basename = parts.pop()

        try:
            basename, option = basename.split(cls.OPTIONDIV)
        except:
            option = None

        parts.append(basename)
        path = cls.PROCSEP.join(parts)

        return path, option

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
        """Return name excluding suffix

        Example
            >>> path = Path(r'c:\users\marcus.test')
            >>> path.name
            'marcus'
            >>> path.basename
            'marcus.test'
            >>> path.suffix
            'test'
            >>> path = Path('/home/.meta')
            >>> path.name
            '.meta'

        """

        name = self._path.split('/')[-1] or self._path

        if name.startswith("."):
            return name

        if self.EXT in name:
            name = name.split('.', 1)[0]

        return name

    @property
    def basename(self):
        """Return name including suffix"""
        path = self._path
        basename = path.rsplit(self.PROCSEP, 1)[-1]
        return basename or path

    @property
    def meta(self):
        """Return meta-path of `self`

        A metapath is the full path to a particular
        set of metadata within a location, excluding suffixes.

        Example
            >>> path = Path('/home/marcus/.meta/group.list/dataset.int')
            >>> path.meta
            '/group/dataset'

        """

        try:
            _, metapath_wsuffix = self._path.rsplit(self.CONTAINER, 1)
        except ValueError:
            return None

        metapath = ''
        for part in metapath_wsuffix.split(self.PROCSEP):
            if not part:
                continue

            metapath += '/' + part.split(self.EXT, 1)[0]

        return metapath

    @property
    def option(self):
        """Return part of path following `OPTIONDIV`

        Example
            >>> path = Path('/root/child&2013-04')
            >>> path.option
            '2013-04'

        """

        return self.__option

    @property
    def location(self):
        """
        Example
            >>> path = Path('/home/user/.meta/address/street')
            >>> path.location
            Path('/home/user')
            >>> path = Path('/home/user/.meta')
            >>> path.location
            Path('/home/user')
            >>> path = Path('/home/user')
            >>> path.location
            Path('/home/user')

        """

        path = self._path.split(self.CONTAINER, 1)[0]
        return self.__class__(path)

    @property
    def parent(self):
        r"""Return the pure parent of a path.

        The pure parent is that which can be derived simply by
        parsing the string value of the path.

        Example
            >>> path = Path('/home/marcus')
            >>> path.parent
            Path('/home')
            >>> path = WindowsPath(r'c:\users')
            >>> path.parent
            WindowsPath('c:\\')
            >>> path.parent.parent
            >>> path = Path('/')
            >>> path.parent
        """

        path = self._path

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
    def parts(self):
        r"""Return each component of a `path`

        Example
            >>> path = Path('/home/marcus/file.exe')
            >>> path.parts
            ['', 'home', 'marcus', 'file.exe']

            >>> path = Path('relative/path/file.exe')
            >>> path.parts
            ['relative', 'path', 'file.exe']

            >>> path = WindowsPath(r'c:\users\marcus\file.exe')
            >>> path.parts
            ['', 'c', 'users', 'marcus', 'file.exe']

            >>> path = WindowsPath(r'relative\path\file.exe')
            >>> path.parts
            ['relative', 'path', 'file.exe']

        """

        return self.as_raw.split(self.PROCSEP)

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
        """
        Example
            >>> path = Path('/root/child.ext')
            >>> path.suffix
            'ext'

            >>> path = Path('/root/child.ext&with_options')
            >>> path.suffix
            'ext'

            >>> path = Path('/root/.meta/child.ext&opt/name')
            >>> path.suffix

            >>> path = Path('/root/.meta/child.ext&opt/name.ext')
            >>> path.suffix
            'ext'

        """

        if not self.__suffix:
            basename = self.basename
            match = self.SuffixPattern.search(basename)
            if match:
                # Disregard the "."
                self.__suffix = match.group(0)[1:]
        return self.__suffix

    def startswith(self, predicate):
        return self.as_str.startswith(predicate)

    def endswith(self, predicate):
        return self.as_str.endswith(predicate)

    @property
    def as_raw(self):
        """Return string without deparsing"""
        if not self.__as_raw:
            self.__as_raw = self._path
            if self.hasoption:
                self.__as_raw += self.OPTIONDIV + self.__option
        return self.__as_raw

    @property
    def as_str(self):
        """Return the composed version of `path`

        Example
            >>> input_value = '/root/child&options_here'
            >>> path = Path(input_value)
            >>> return_value = input_value
            >>> path.as_str == return_value
            True
            >>> path._path
            '/root/child'
        """

        if not self.__as_str:
            self.__as_str = self.deparse()
            if self.hasoption:
                self.__as_str += self.OPTIONDIV + self.__option
        return self.__as_str

    @property
    def isabsolute(self):
        return True if self.root else False

    @property
    def isrelative(self):
        return False if self.root else True

    @property
    def isroot(self):
        return True if self._path == '/' else False

    @property
    def hasoption(self):
        return self.__option is not None


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

        Example
            c:\windows\system32 == \c\windows32\system32

    """

    SEPARATOR = '\\'

    DrivePattern = re.compile(r'^\w:')

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
            drive = self._path[1] + ":"
            return drive
        return None


class PosixPath(DirPath):
    SEPARATOR = '/'

    def __init__(self, *args, **kwargs):
        super(PosixPath, self).__init__(*args, **kwargs)


class MetaPath(DirPath):
    SEPARATOR = '/'


if __name__ == '__main__':
    import openmetadata as om
    om.setup_log()

    import os
    import doctest
    doctest.testmod()

    # path = Path('/root/.meta/child.ext&opt')
    path = WindowsPath(r'c:\users')
    # path = WindowsPath('/c')
    # print path.as_raw
    # print path._path
    print os.path.join(path.parent.as_str, 'test')
    # print path.parent.parent._path
    # print path.parent.parent + 'local'
    # print os.path.join(path.parent.parent.as_str, 'local')
    # print path.parent.parent.parent
    # path = Path('/root/.meta/child')
    # print Path.OPTIONDIV
    # print '/test/some&folder'.rsplit(Path.OPTIONDIV)
    # print Path.splitoption('/test/some&folder')
    
    # print path.basename
    # print path.suffix
    # print path.option

    # p = WindowsPath(r's:\absolute\path.ast\onemore\..')
    # print p.suffix
    # print p + '..'
    # print p + '../..'
    # print p + '../.'
    # print p + './published'
