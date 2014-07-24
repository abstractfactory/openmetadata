
# Subject
from openmetadata import cli
from openmetadata import tests


# class TestCli(tests.CliTestCase):
#     def test_readwrite(self):
#         """Writing a value and reading it back in"""
#         self.runner.invoke(cli.write, ['test1', '--value', 'Hello'])
#         result = self.runner.invoke(cli.read, ['test1'])
#         self.assertEquals(result.output, 'Hello')

#         self.runner.invoke(cli.write, ['test2', '--value', 'Hello world'])
#         result = self.runner.invoke(cli.read, ['test2'])
#         self.assertEquals(result.output, 'Hello world')

#     def test_write(self):
#         """Writing doesn't output any value, unless there was an error"""
#         result = self.runner.invoke(cli.write, ['test3', '--value', 'Hello'])
#         self.assertEquals(result.output, "")

#     def test_write_nested(self):
#         """Write a nested entry"""
#         result = self.runner.invoke(cli.write, ['group/test4',
#                                                 '--value',
#                                                 'Hello'])
#         result = self.runner.invoke(cli.read, ['group/test4'])
#         self.assertEquals(result.output, 'Hello')
