import os
import shutil
import unittest
import tempfile

import openmetadata as om

data = dict()


class ReadWriteTestCase(unittest.TestCase):
    def setUp(self):
        root_path = tempfile.mkdtemp()
        project_path = os.path.join(root_path,
                                    'projects',
                                    'content',
                                    'jobs',
                                    'spiderman')
        asset_path = os.path.join(project_path, 'assets', 'Peter')

        self.root_path = root_path
        self.project_path = project_path
        self.asset_path = asset_path

        self.root = om.Location(root_path)
        self.project = om.Location(project_path)
        self.asset = om.Location(asset_path)

        self.data = {'hello': 'world',
                     'world': 'hello',
                     'more': '1',
                     'more': '2',
                     'more': '3'}

    def tearDown(self):
        shutil.rmtree(self.root_path)


class ReadOnlyTestCase(unittest.TestCase):
    def setUp(self):
        root_path = os.path.abspath('fixtures/basic')
        project_path = os.path.join(root_path,
                                    'projects',
                                    'content',
                                    'jobs',
                                    'spiderman')
        asset_path = os.path.join(project_path, 'assets', 'Peter')

        self.root_path = root_path
        self.project_path = project_path
        self.asset_path = asset_path

        self.project = om.Location(project_path)
        self.asset = om.Location(asset_path)
