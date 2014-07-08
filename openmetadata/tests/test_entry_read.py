"""Run tests against a pre-set fixture

.. note:: It's important that none of these tests modify
    the fixture, as it would result in side-effects betweeen
    tests.

"""

# Subject
import openmetadata as om
from openmetadata import tests


class TestEntryRead(tests.ReadOnlyTestCase):

    def test_pull_existing(self):
        """Read from existing metadata"""
        entry = om.Entry("standard_int.int", parent=self.project)
        om.pull(entry)
        self.assertEquals(entry.value, 10)
        self.assertEquals(entry.path.basename, "standard_int.int")
        self.assertEquals(entry.path.suffix, "int")

    def test_modify_existing(self):
        """Modifying an existing value with a value of the same
        type should leave the original suffix intact"""
        entry = om.Entry('standard_int.int', parent=self.project)
        entry.value = 15
        self.assertEquals(entry.value, 15)
        self.assertEquals(entry.path.basename, "standard_int.int")
        self.assertEquals(entry.path.suffix, "int")

    def test_pull_nonexisting(self):
        entry = om.Entry('nonexisting', parent=self.project)
        self.assertRaises(om.error.Exists, om.pull, entry)

    def test_no_suffix_string(self):
        """Entries without suffixes and value are mis-named. They are
        still valid entries however and their type is inferred by their
        value. Assuming their value is a valid JSON-formatted string.

        When pulling, the value will determine its type and he suffix
        will then be indirectly determined to string"""

        entry = om.Entry('nosuffix_string', parent=self.project)
        self.assertEquals(entry.path.suffix, None)

        om.pull(entry)
        self.assertEquals(entry.path.suffix, 'string')

    def test_pull_unknown_string(self):
        entry = om.Entry('unknown_string.abc', parent=self.project)
        om.pull(entry)
        self.assertEquals(entry.value, u'this is of type string')
        self.assertEquals(entry.path.suffix, 'string')

    def test_pull_unknown(self):
        """Pull from unknown extension without value"""
        entry = om.Entry('unknown.abc', parent=self.project)
        om.pull(entry)
        self.assertEquals(entry.value, None)

    def test_pull_unknown_corrupt(self):
        """Pull from unknown extension and corrupt value

        Entries are all JSON-formatted. This one however is
        mis-formatted and will not be successfully parsed.

        """

        entry = om.Entry('unknown_corrupt.abc', parent=self.project)
        om.pull(entry)
        self.assertEquals(entry.value, None)

    # def test_existing_known_type():
    #     value = om.read(project_path, 'standard_int.int')
    #     # .assertEquals(value, 25)

    # def test_existing_unknown_type():
    #     value = om.read(project_path, 'unknown.abc')
    #     # .assertEquals(value, None)

    # def test_corrupt():
    #     value = om.read(project_path, 'corrupt.string')
    #     # .assertEquals(value, None)


if __name__ == '__main__':
    import nose
    nose.run()
