"""Test each service individually"""


# Subject
from openmetadata import tests
from openmetadata import error
from openmetadata import service


class TestSevices(tests.ReadOnlyTestCase):
    def test_ls(self):
        dirs, files = service.ls(self.root_path)
        self.assertEquals(dirs, ['empty', 'projects'])
        self.assertEquals(files, ['file.txt'])

    def test_ls_missingpath(self):
        self.assertRaises(error.Exists,
                          service.ls, 'missing path')

    def test_ls_fileaspath(self):
        """Attempting to list a file will result in Exists error"""
        self.assertRaises(error.Exists,
                          service.ls, self.file_path)

    def test_ls_empty(self):
        """Reading an empty folder

        ls will not complain and merely return two
        empty lists.

        """

        dirs, files = service.ls(self.empty_path)
        self.assertEquals(dirs, list())
        self.assertEquals(files, list())

    def test_open(self):
        contents = service.open(self.file_path)
        self.assertEquals(contents, 'contents of file')

    def test_open_missing(self):
        self.assertRaises(error.Exists,
                          service.open, 'missing path')

    def test_open_folder(self):
        """Opening a folder causes a permissions error,
        this is treated as though the path does not exist"""
        self.assertRaises(error.Exists,
                          service.open, self.root_path)
