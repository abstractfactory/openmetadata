"""Run tests against dynamically instantiated data

.. note:: As opposed to test_entry_write.py, this module
    may write metadata and thus alter the given hierarchy.
    The hierarchy is created and removed prior to and after
    each suite of tests have been run.

"""

# Standard library
import os

# Subject
import openmetadata as om
from openmetadata import tests


class TestEntryWrite(tests.ReadWriteTestCase):
    def test_integration(self):
        """Test a combination of features"""
        entry = om.Entry('test.string', value="Hello", parent=self.root)
        child = om.Entry('child.int', value=1, parent=entry)
        self.assertEquals(entry.type, 'dict')
        om.flush(entry)
        self.assertTrue(os.path.exists(entry.path.as_str))
        om.pull(entry)
        self.assertEquals(entry.type, 'dict')
        entry.value = "Hello"
        self.assertEquals(entry.type, 'string')
        self.assertEquals(entry.value, "Hello")
        om.flush(entry)
        om.pull(entry)
        self.assertFalse(os.path.exists(child.path.as_str))

        child = om.Entry('child.int', value=1, parent=entry)
        om.flush(entry)
        self.assertEquals(om.read(self.root_path, 'test/child'), 1)
        om.write(self.root_path, '/test/child', 2)
        self.assertEquals(om.read(self.root_path, 'test/child'), 2)
        om.write(self.root_path, '/root/test/another', 10)
        self.assertEquals(om.read(self.root_path, 'root/test/another'), 10)

    def test_absolutename(self):
        """If entry exists, suffix will be implied by find()"""
        entry = om.Entry('custom.int', value=10, parent=self.root)
        om.flush(entry)

        entry = om.Entry('custom.string', value="Hello", parent=self.root)
        om.pull(entry)

        self.assertEquals(entry.type, 'int')

    def test_convert(self):
        """contert() is a shorthand for creating location and entry sep."""
        entry = om.Entry('custom.int', value=10, parent=self.root)
        om.flush(entry)

        entry = om.convert(entry.path.as_str)
        self.assertEquals(entry.value, 10)

    def test_convert_withmissingsuffix(self):
        entry = om.Entry('custom_missing.int', value=10, parent=self.root)
        om.flush(entry)

        new_path = entry.path.copy(suffix='string')
        entry = om.convert(new_path.as_str)
        self.assertEquals(entry.value, 10)

    def test_noname(self):
        """Not assigning a name to an entry is considered a bug"""
        self.assertRaises(AssertionError, om.Entry, '',
                          value='Hello',
                          parent=self.root)

    def test_flush_existing(self):
        """Overwrite existing entry"""
        # Make it exist
        standard_int = om.Entry('standard_int', value=10, parent=self.root)
        om.flush(standard_int)

        self.assertTrue(os.path.exists(standard_int.path.as_str))

        # Then flush it again
        standard_int = om.Entry('standard_int', value=15, parent=self.root)
        om.flush(standard_int)

        om.pull(standard_int)
        self.assertEquals(standard_int.value, 15)

    def test_new_group(self):
        """Write a new group"""
        entry = om.Entry('a group.dict', parent=self.root)
        om.flush(entry)

        om.pull(entry)
        self.assertEquals(entry.type, 'dict')
        self.assertTrue(os.path.isdir(entry.path.as_str))

    def test_new_group_with_content(self):
        """The alternative is to add other entries to is"""
        entry = om.Entry('a group', parent=self.root)

        for key, value in self.data.iteritems():
            om.Entry(key, value=value, parent=entry)

        om.flush(entry)

        self.assertTrue(entry.type == 'dict')
        self.assertTrue(os.path.exists(entry.path.as_str))

    def test_add_entries_to_nongroup(self):
        """Add entries to nongroup

        Adding entries to an entry that isn't a group will
        cast it to a group.

        """

        nongroup_entry = om.Entry('nongroup',
                                  value='A string',
                                  parent=self.root)

        self.assertTrue(nongroup_entry.type == 'string')
        om.flush(nongroup_entry)

        invalid_child = om.Entry('invalid_child',
                                 value='a string',
                                 parent=nongroup_entry)

        # By adding a child, the nongroup becomes a group.
        # Just like it would in a dynamic programming language:
        # >>> myint = 5
        # >>> myint = list()
        self.assertEquals(nongroup_entry.type, 'dict')

        om.flush(nongroup_entry)

        self.assertTrue(os.path.exists(nongroup_entry.path.as_str))

        om.pull(nongroup_entry)

        self.assertTrue(os.path.exists(invalid_child.path.as_str))
        self.assertTrue(os.path.isdir(nongroup_entry.path.as_str))
        self.assertEquals(nongroup_entry.type, 'dict')

    def test_removal(self):
        removed = om.Entry('removed', value=1, parent=self.root)
        om.flush(removed)

        self.assertTrue(os.path.isfile(removed.path.as_str))
        om.recycle(removed)
        self.assertFalse(os.path.exists(removed.path.as_str))

    def test_removal_group(self):
        removed = om.Entry('removed.dict', parent=self.root)
        om.Entry('child', value=1, parent=removed)
        self.assertEquals(removed.type, 'dict')

        om.flush(removed)

        self.assertTrue(os.path.isdir(removed.path.as_str))
        om.recycle(removed)
        self.assertFalse(os.path.exists(removed.path.as_str))

    def flush_multiple(self):
        parent = om.Entry('parent', parent=self.root)

        for key, value in self.data.iteritems():
            om.Entry(key, value=value, parent=parent)

        om.flush(parent)

        # Read data back from disk and re-build it
        om.pull(parent)

        pulled_data = dict()
        for child in parent:
            om.pull(child)
            pulled_data[child.path.basename] = child.value

        self.assertEquals(self.data, pulled_data)

    def test_change_type_by_overwriting(self):
        """Types in Open Metadata are represented on disk as suffixes.
        However a suffix is an implementation detail and should not
        be modified by hand.

        The equivalence in dynamic programming languages is this:

        >> myint = 5
        >> myint = "I'm a string now"

        On disk, myint would initially be stored as `myint.int` but
        after having been reassigned a string value, it would be stored
        as `myint.string`. The point to take home being that suffixes
        are a serialisation of type and dictates how the file is to be
        read.

        """

        height = om.Entry('height', value=10, parent=self.root)
        om.flush(height)

        self.assertEquals(height.type, 'int')

        height = om.Entry('height', value=11.1, parent=self.root)
        om.flush(height)

        self.assertEquals(height.type, 'float')

    def test_suffix_and_type_mismatch(self):
        height = om.Entry('height.int', value=10.1, parent=self.root)
        self.assertEquals(height.type, 'float')
        om.flush(height)
        om.pull(height)
        self.assertEquals(height.type, 'float')



if __name__ == '__main__':
    import nose
    nose.run()
