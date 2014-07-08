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
    def test_flush_existing(self):
        # Make it exist
        standard_int = om.Entry('standard_int', value=10, parent=self.root)
        om.flush(standard_int)

        # Then flush it again
        standard_int = om.Entry('standard_int', value=15, parent=self.root)
        om.flush(standard_int)

        om.pull(standard_int)
        self.assertEquals(standard_int.value, 15)

    def test_new_group(self):
        """Writing an empty group is a matter of indicating
        that it is a group"""

        entry = om.Entry('a group', parent=self.root)
        entry.isgroup = True
        om.flush(entry)

        om.pull(entry)
        self.assertTrue(entry.isgroup)
        self.assertIsNone(entry.path.suffix)
        self.assertTrue(os.path.isdir(entry.path.as_str))

    def test_new_group_with_content(self):
        """The alternative is to add other entries to is"""
        entry = om.Entry('a group', parent=self.root)

        for key, value in self.data.iteritems():
            om.Entry(key, value=value, parent=entry)

        om.flush(entry)

        self.assertTrue(entry.isgroup)
        self.assertTrue(os.path.exists(entry.path.as_str))

    # def test_add_entries_to_nongroup(self):
    #     """Adding entries to an entry that isn't a group will
    #     cast it to a group"""

    #     nongroup_entry = om.Entry('nongroup',
    #                               value='A string',
    #                               parent=self.root)

    #     self.assertTrue(nongroup_entry.path.suffix == 'string')
    #     om.flush(nongroup_entry)

    #     invalid_child = om.Entry('invalid_child',
    #                              value='a string',
    #                              parent=nongroup_entry)

    #     # By adding a child, the nongroup becomes a group.
    #     # Just like it would in a dynamic programming language:
    #     # >>> myint = 5
    #     # >>> myint = list()
    #     self.assertTrue(nongroup_entry.isgroup)

    #     om.flush(nongroup_entry)
    #     om.pull(nongroup_entry)

    #     self.assertTrue(os.path.isdir(nongroup_entry.path.as_str))
    #     self.assertTrue(nongroup_entry.isgroup)

    def test_removal(self):
        pass

    def test_removal_group(self):
        pass

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
        # Make it exist
        height = om.Entry('height', value=10, parent=self.root)
        om.flush(height)

        self.assertEquals(height.path.suffix, 'int')

        height = om.Entry('height', value=11.1, parent=self.root)
        om.flush(height)

        self.assertEquals(height.path.suffix, 'float')

    def test_suffix_and_type_mismatch(self):
        height = om.Entry('height.int', value=10.1, parent=self.root)
        self.assertEquals(height.path.suffix, 'float')
        om.flush(height)
        om.pull(height)
        self.assertEquals(height.path.suffix, 'float')

    def test_int(self):
        name = 'integer'
        value = 10

        integer = om.Entry(name, value=value, parent=self.root)
        om.flush(integer)
        om.pull(integer)
        self.assertEquals(integer.value, value)
        self.assertEquals(integer.path.name, name)


if __name__ == '__main__':
    import nose
    nose.run()
