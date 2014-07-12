import openmetadata as om
import openmetadata.tests


class TestRead(openmetadata.tests.ReadOnlyTestCase):
    def test_existing(self):
        """Read from existing metadata"""
        value = om.read(self.project_path, 'height')
        self.assertEquals(value, 10)

    def test_existing_known_type(self):
        value = om.read(self.project_path, 'height.int')
        self.assertEquals(value, 10)

    def test_existing_unknown_type(self):
        """unknown.abc contains nothing and isn't a recognised type.

        As a result, nothing will get successfully read from disk, and
        no default will be assigned, resultuing in None.

        """

        value = om.read(self.project_path, 'unknown.abc')
        self.assertEquals(value, None)

    def test_corrupt(self):
        """corrupt.string conatins a value that isn't JSON formatted.

        Reading it will result in an exception being raised within lib.Resource
        which will in turn set its value to None.

        When querying the value of the entry, the .value property will
        encounter None and assume no value has been set or attempted to be
        set. As a result, it will assign a default value, which in the case of
        string is an empty string.

        """

        value = om.read(self.project_path, 'corrupt.string')
        self.assertEquals(value, '')

    def test_nested(self):
        value = om.read(self.project_path, 'deep/subdeep/value')
        self.assertEquals(value, 'Value')

    def test_nested_absolute(self):
        """Specifying suffixes make no difference"""
        value = om.read(self.project_path, 'deep.dict/subdeep/value.string')
        self.assertEquals(value, 'Value')

    def test_nested_wrongsuffix(self):
        """Suffixes are ignored

        Although you specify a suffix, if the name exists a correct suffix
        will be derived during lookup.

        """

        value = om.read(self.project_path, 'deep/subdeep.list/value.string')
        self.assertEquals(value, 'Value')


if __name__ == '__main__':
    import nose
    nose.run()
