"""

Test types, generally
Test default values
Test removal

"""

import openmetadata as om
from openmetadata import tests


class TestTypes(tests.DynamicTestCase):
    def test_int(self):
        name = 'integer'
        value = 10

        integer = om.Entry(name, value=value, parent=self.root)
        om.flush(integer)
        om.pull(integer)
        self.assertEquals(integer.value, value)
        self.assertEquals(integer.name, name)
        self.assertEquals(integer.type, 'int')

    def test_dict(self):
        """Write dict"""
        name = 'mydict.dict'

        dic = om.Entry(name, parent=self.root)
        om.flush(dic)
        om.pull(dic)
        self.assertEqual(dic.type, 'dict')
        self.assertEqual(dic.name, 'mydict')
