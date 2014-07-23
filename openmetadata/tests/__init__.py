# standard library
import os
import shutil
import unittest
import tempfile

# subject
import openmetadata as om

# dependencies
from openmetadata.vendor import yaml


class InteractiveTestCase(unittest.TestCase):
    """Dynamically set-up a hierarchy that will be modified during tests"""
    def setUp(self):
        hierarchy = """
        projects:
            .meta:
                client.dict:
                    address:
                        street.string
                        phone.string
                        city
                    executives:
                        paul
                        john
                    production.dict:
                        ally
                        sean
                camera.dict:
                    front
                resolution:
                    delivery.dict:
                        client
                        production
                    inhouse:
                        client
                        production
            spiderman:
                .meta:
                    range.dict:
                        start.int
                        end.int
                    world.matrix:
                        x.float
                        y.float
                        z.float

        """

        root_path = tempfile.mkdtemp()

        hierarchy = yaml.load(hierarchy)

        self.make_hierarchy(root_path, hierarchy)

        self.root_path = root_path

        types = self.counts()
        self.assertEquals(types['total'], 15)
        self.assertEquals(types['dict'], 5)
        self.assertEquals(types['matrix'], 1)

    def tearDown(self):
        shutil.rmtree(self.root_path)

    def make_hierarchy(self, root, hierarchy):
        for key, value in hierarchy.iteritems():
            inner_root = os.path.join(root, key)
            os.makedirs(inner_root)
            if isinstance(value, dict):
                self.make_hierarchy(root=inner_root, hierarchy=value)

    def counts(self, root=None):
        root = root or self.root_path

        types = dict()
        for base, _, _ in os.walk(root):
            if not 'total' in types:
                types['total'] = 0
            types['total'] += 1

            try:
                basename = os.path.basename(base)
                _, suffix = basename.rsplit(".")
                if not suffix in types:
                    types[suffix] = 0
                types[suffix] += 1
            except:
                pass

        return types

    def assert_counts(*kwargs):
        pass


class DynamicTestCase(unittest.TestCase):
    def setUp(self):
        root_path = tempfile.mkdtemp()

        file_path = os.path.join(root_path, 'file.txt')
        f = open(file_path, 'w')
        f.close()

        self.root_path = root_path
        self.file_path = file_path

        self.root = om.Location(root_path)

        self.data = {'hello': 'world',
                     'world': 'hello',
                     'more': '1',
                     'more': '2',
                     'more': '3'}

    def tearDown(self):
        shutil.rmtree(self.root_path)


class FixtureTestCase(unittest.TestCase):
    def setUp(self):
        module_path = os.path.dirname(__file__)
        root_path = os.path.join(module_path, 'fixtures', 'basic')
        project_path = os.path.join(root_path,
                                    'projects',
                                    'content',
                                    'jobs',
                                    'spiderman')
        asset_path = os.path.join(project_path, 'Peter')
        case_path = os.path.join(root_path, 'CaseSensitive')

        self.root_path = root_path
        self.project_path = project_path
        self.asset_path = asset_path
        self.empty_path = os.path.join(root_path, 'empty')
        self.case_path = case_path
        self.file_path = os.path.join(root_path, 'file.txt')

        self.root = om.Location(root_path)
        self.project = om.Location(project_path)
        self.asset = om.Location(asset_path)
