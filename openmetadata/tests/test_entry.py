
# Subject
import openmetadata as om
from openmetadata import tests


class TestEntryRead(tests.ReadWriteTestCase):

    def test_attributes(self):
        entry = om.Entry('test_string', value='Hello', parent=self.root)
        self.assertTrue(entry.type, 'string')

        entry = om.Entry('test_nosuffix', parent=self.root)
        self.assertTrue(entry.type, None)
