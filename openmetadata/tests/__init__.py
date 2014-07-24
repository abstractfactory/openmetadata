
# standard library
import os
import shutil
import unittest
import tempfile

# subject
import openmetadata as om

# vendor
from openmetadata.vendor.click.testing import CliRunner
from openmetadata.vendor import yaml


class CliTestCase(unittest.TestCase):
    def setUp(self):
        self.root_path = tempfile.mkdtemp()

        self.old_chdir = os.getcwd()
        os.chdir(self.root_path)

        self.runner = CliRunner()

    def tearDown(self):
        os.chdir(self.old_chdir)


class BaseTestCase(unittest.TestCase):
    """Dynamically set-up a hierarchy that will be modified during tests"""

    def make_hierarchy(self, root, hierarchy):
        """Create hierarchy from dictionary of items at absolute path `root`

        Supports directories, files and strings as content to files.

        Arguments:
            root (string): Absolute path at which to create hierarchy
            hierarchy (dict): Hierarchy formatted as a dict
                e.g. {
                    'parent': {
                        'child': {
                            'file': '"contents here"'
                            }
                        }
                    }

        """

        for key, value in hierarchy.iteritems():
            path = os.path.join(root, str(key))
            if value is not None and not isinstance(value, dict):
                with open(path, 'w') as f:
                    if not value == "_":
                        # Content is JSON-encoded, thus strings must
                        # be pre- and suffixed with citation marks.
                        if isinstance(value, basestring):
                            if value.startswith("_") and value.endswith("_"):
                                value = value
                            else:
                                value = '"%s"' % value

                        f.write(str(value))
                continue

            else:
                os.makedirs(path)

            if isinstance(value, dict):
                self.make_hierarchy(root=path, hierarchy=value)

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

    def assert_counts(self, *kwargs):
        types = self.counts()
        for typ, count in kwargs.iteritems():
            self.assertEquals(types.get(typ, 0), count)


class InteractiveTestCase(BaseTestCase):
    def setUp(self):
        hierarchy = """
        0.5.2:
            .meta:
                client.dict:
                    address:
                        street.string: "Blackwall way"
                        phone.string: "112"
                        city.string: "London"
                    production.dict:
                camera.dict:
                resolution:
                    delivery.dict:
                    inhouse:
                    another:
            spiderman:
                .meta:
                    range.dict:
                        start.int: 1000
                        end.int: 2000
                    world.matrix:
                        x.float: 0.1
                        y.float: 0.15
                        z.float: 0.1

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


class FixtureTestCase(BaseTestCase):
    def setUp(self):
        """Write fixture

        Hierarchy syntax; JSON, plus a few additional concepts.
        - Underscore (_) means an empty file
        - Prefix and suffix underscore means write as-is, not string

        """

        hierarchy = """
        .meta:
            deep.dict:
                data.dict:
                    key.string: "value"
            duplicate.int: 5
            duplicate.string: "five"
            simple.string: "value"

        CaseSensitive:
            .meta:
                data.string: "value here"

        empty:

        root:
            content:
                jobs:
                    spiderman:
                        .meta:
                            apps.dict:
                                houdini.dict:
                                maya.dict:
                                    name.string: "Maya 2015 Base"
                            deep.dict:
                                subdeep.dict:
                                    value.string: "Value"
                            corrupt.string: True
                            height.int: 10
                            nosuffix_novalue: _
                            nosuffix.string: "string value"
                            standard_int.int: 10
                            unknown.abc: _
                            unknown_corrupt.abc: _corrupt_
                            unknown_string.abc: "this is of type string"
                        1000:
                            .meta:
                                apps.dict:
                                    houdini.dict:
                                    maya.dict:
                                        name.string: "Maya 2015 Shot 1000"

        """

        root_path = tempfile.mkdtemp()
        project_path = os.path.join(root_path,
                                    'root',
                                    'content',
                                    'jobs',
                                    'spiderman')
        asset_path = os.path.join(project_path, 'Peter')
        case_path = os.path.join(root_path, 'CaseSensitive')

        hierarchy = yaml.load(hierarchy)

        self.make_hierarchy(root_path, hierarchy)

        self.root_path = root_path
        self.project_path = project_path
        self.asset_path = asset_path
        self.empty_path = os.path.join(root_path, 'empty')
        self.case_path = case_path
        self.file_path = os.path.join(root_path, 'file.txt')

        self.root = om.Location(root_path)
        self.project = om.Location(project_path)
        self.asset = om.Location(asset_path)
