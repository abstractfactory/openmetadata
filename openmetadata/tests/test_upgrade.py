
import os

# Subject
from openmetadata import tests
from openmetadata import upgrade
from openmetadata.vendor import yaml


class UpgradeModuleTests(tests.InteractiveTestCase):
    def test_upgrade1(self):
        """Upgrade 0.5.2 -> 0.5.4"""

        types = self.counts()

        self.assertEquals(types.get('total', 0), 15)
        self.assertEquals(types.get('dict', 0), 5)

        upgrade.walk(self.root_path)

        types = self.counts()

        self.assertEquals(types.get('total', 0), 15)
        self.assertEquals(types.get('dict', 0), 9)

    def test_restore(self):
        """Make new 0.5.2 hierarchy, upgrade, and restore"""

        hierarchy = """
        loc1:
            .meta:
                group1:
                group2.dict:
                group3.dict:
                    group4:
                    group5.dict:
            loc2:
                .meta:
                    group6:

        """

        hierarchy = yaml.load(hierarchy)

        root = os.path.join(self.root_path, 'root0')
        self.make_hierarchy(root, hierarchy)

        types = self.counts(root)
        self.assertEquals(types.get('total', 0), 11)
        self.assertEquals(types.get('dict', 0), 3)

        upgrade.walk(root)

        types = self.counts(root)
        self.assertEquals(types.get('total', 0), 11)
        self.assertEquals(types.get('dict', 0), 6)

        upgrade.restore(root)

        types = self.counts(root)
        self.assertEquals(types.get('total', 0), 11)
        self.assertEquals(types.get('dict', 0), 3)

    def test_restore_invalid(self):
        """Make invalid 0.5.2 hierarchy, upgrade, and restore"""

        hierarchy = """
        loc1:
            .meta:
                group1.matrix:
                .group2:
                group3.list:
                    group4:
                    group5.wrongdict:
            loc2:
                .meta:
                    group6.dict:

        """

        hierarchy = yaml.load(hierarchy)

        root = os.path.join(self.root_path, 'root1')
        self.make_hierarchy(root, hierarchy)

        types = self.counts(root)
        self.assertEquals(types.get('total', 0), 11)
        self.assertEquals(types.get('dict', 0), 1)

        upgrade.walk(root)

        types = self.counts(root)
        self.assertEquals(types.get('total', 0), 11)
        self.assertEquals(types.get('dict', 0), 2)

        upgrade.restore(root)

        types = self.counts(root)
        self.assertEquals(types.get('total', 0), 11)
        self.assertEquals(types.get('dict', 0), 1)

        # Once restored, there shouldn't be a history left
        self.assertFalse(
            os.path.exists(
                os.path.join(root, upgrade.HISTORY_FILE)))

    def test_already_restored(self):
        """Make invalid 0.5.2 hierarchy, upgrade, and restore"""

        hierarchy = """
        loc1:
            .meta:
                group1.dict:
                group2.dict:
                group3.list:
                    group4.matrix:
                    group5.dict:
            loc2:
                .meta:
                    group6.dict:

        """

        hierarchy = yaml.load(hierarchy)

        root = os.path.join(self.root_path, 'root2')
        self.make_hierarchy(root, hierarchy)

        types = self.counts(root)
        self.assertEquals(types.get('total', 0), 11)
        self.assertEquals(types.get('dict', 0), 4)

        history = upgrade.walk(root)
        self.assertEquals(history, list())

        types = self.counts(root)
        self.assertEquals(types.get('total', 0), 11)
        self.assertEquals(types.get('dict', 0), 4)

        # No history was captured
        self.assertRaises(ValueError, upgrade.restore, root)

    def test_restorable(self):
        """Make invalid 0.5.2 hierarchy, upgrade, and restore"""

        hierarchy = """
        loc1:
            .meta:
                group1:

        """

        hierarchy = yaml.load(hierarchy)

        root = os.path.join(self.root_path, 'root3')
        self.make_hierarchy(root, hierarchy)

        types = self.counts(root)
        self.assertEquals(types.get('total', 0), 4)
        self.assertEquals(types.get('dict', 0), 0)

        upgrade.walk(root)

        self.assertTrue(upgrade.restorable(root))

    def test_rename(self):
        """Test protected _rename function"""
        old_path = os.path.join(self.root_path, 'temp_old')
        new_path = os.path.join(self.root_path, 'temp_new')

        with open(old_path, 'w') as f:
            f.write("")

        self.assertTrue(os.path.isfile(old_path))
        self.assertFalse(os.path.isfile(new_path))

        upgrade._rename(src=old_path, dest=new_path)

        self.assertFalse(os.path.isfile(old_path))
        self.assertTrue(os.path.isfile(new_path))

    def test_rename_nonexisting(self):
        self.assertRaises(upgrade.UpgradeError,
                          upgrade._rename,
                          src='not/exist', dest='not/exist_')

    def test_upgrade_nonexisting(self):
        """Upgrade non-existing root"""

        root = os.path.join(self.root_path, 'root4')

        # root doesn't exist

        self.assertRaises(upgrade.UpgradeError, upgrade.walk, root)


if __name__ == '__main__':
    import nose
    nose.run()
