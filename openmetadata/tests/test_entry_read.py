"""Run tests against a pre-set fixture

.. note:: It's important that none of these tests modify
    the fixture, as it would result in side-effects betweeen
    tests.

"""

import os
import sys

# Subject
import openmetadata as om
import openmetadata.tests


class TestEntryRead(openmetadata.tests.FixtureTestCase):

    def test_pull_existing(self):
        """Read from existing metadata"""
        entry = om.Entry("standard_int.int", parent=self.project)
        om.pull(entry)
        self.assertEquals(entry.value, 10)
        self.assertEquals(entry.path.basename, "standard_int.int")
        self.assertEquals(entry.path.suffix, "int")

    def test_case_sensitivity(self):
        case_sensitive_location = om.Location(self.case_path)
        data = om.Entry('data', parent=case_sensitive_location)
        om.pull(data)
        self.assertEquals(data.value, 'value here')

        wrong_case = om.Location(self.case_path.lower())
        data = om.Entry('data', parent=wrong_case)

        if sys.platform == 'win32':
            om.pull(data)
            self.assertEquals(data.value, 'value here')
        else:
            self.assertRaises(om.error.Exists, om.pull, data)

    # def test_chaining_pull(self):
    #     """pull() supports chaining"""

    # def test_read_misnamed_directory(self):
    #     """A directory is without suffix:

    #     /home/.meta/mygroup/somedata.string

    #     """

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

    # def test_no_suffix_string(self):
    #     """Entries without suffixes and value are considered corrupt"""
    #     entry = om.Entry('nosuffix_string', parent=self.project)
    #     self.assertEquals(entry.path.suffix, None)
    #     self.assertRaises(om.error.Corrupt, om.pull, entry)

    def test_pull_unknown_string(self):
        """Pull from entry whose value is string but suffix is misnamed"""
        entry = om.Entry('unknown_string.abc', parent=self.project)
        self.assertTrue(os.path.exists(entry.path.as_str))
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


if __name__ == '__main__':
    import nose
    nose.run()
