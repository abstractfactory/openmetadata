import openmetadata as om
import openmetadata.tests


# class TestRead(openmetadata.tests.BasicTestCase):
#     def test_existing(self):
#         """Read from existing metadata"""
#         value = om.read(self.project_path, 'frameRate')
#         self.assertEquals(value, 10)

    # def test_existing_known_type(self):
    #     value = om.read(self.project_path, 'frameRate.int')
    #     self.assertEquals(value, 25)

    # def test_existing_unknown_type(self):
    #     value = om.read(self.project_path, 'unknown.abc')
    #     self.assertEquals(value, None)

    # def test_corrupt(self):
    #     value = om.read(self.project_path, 'corrupt.string')
    #     self.assertEquals(value, None)


if __name__ == '__main__':
    import nose
    nose.run()
