"""Test parent/child relationships"""

# Subject
import openmetadata as om
import openmetadata.tests


class TestEntryRead(openmetadata.tests.FixtureTestCase):
    def test_childpath(self):
        """The path of a child is derived from its basename and parent"""
        parent = om.Location(self.root_path)
        entry = om.Entry('test', parent=parent)
        self.assertEquals(entry.path, parent.path + entry.path.basename)
