
# Subject
import openmetadata as om
from openmetadata import tests


class TestEntryRead(tests.ReadWriteTestCase):

    def test_attributes(self):
        entry = om.Entry('test_string', value='Hello', parent=self.root)
        self.assertTrue(entry.type, 'string')

    def test_no_suffix(self):
        entry = om.Entry('test_nosuffix', parent=self.root)
        self.assertEquals(entry.type, None)

    def test_imply_suffix_via_value(self):
        entry = om.Entry('nosuffix', parent=self.root)
        entry.value = "Hello"
        self.assertEquals(entry.type, 'string')
