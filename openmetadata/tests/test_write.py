import openmetadata as om
import openmetadata.tests


class TestWrite(openmetadata.tests.DynamicTestCase):
    def test_write_simple(self):
        om.write(self.root_path, 'simple', 'value')
        self.assertEquals(om.read(self.root_path, 'simple'), 'value')

    def test_write_deep(self):
        om.write(self.root_path, '/deep/data/key', 'value')
        self.assertEquals(om.read(self.root_path, '/deep/data/key'), 'value')

    def test_write_invalidgroup(self):
        om.write(self.root_path, '/deep/data.string/key', 'value')
        self.assertEquals(om.read(self.root_path, '/deep/data/key'), 'value')
