
import os

# Subject
import openmetadata as om
from openmetadata import tests


class TestInheritWrite(tests.DynamicTestCase):
    def test_inherit_existing(self):
        """Inherit from existing entry

        /root (height=50)
            /group (height=100)
                /subgroup <-- Inherits above

        """

        group = os.path.join(self.root_path, 'group')
        subgroup = os.path.join(group, 'subgroup')
        os.makedirs(subgroup)

        base_location = self.root
        group_location = om.Location(group)
        subgroup_location = om.Location(subgroup)

        base_value = om.Entry('height', value=50, parent=base_location)
        group_value = om.Entry('height', value=100, parent=group_location)
        om.flush(base_value)
        om.flush(group_value)

        # Get metadata from location where metadata doesn't exist
        height = om.Entry('height', parent=subgroup_location)
        om.inherit(height)

        self.assertEquals(height.value, 100)


class TestInheritRead(tests.FixtureTestCase):
    def test_inherit(self):
        """Inherit property from parenthood

        /projects
            /spiderman      (apps/maya/name)
                /1000       (apps/maya/name)
                    /cache  (no metadata)

        """

        shot_path = os.path.join(self.project_path, '1000', 'cache')
        shot_entry = om.entry(shot_path, 'apps/maya/name')
        om.inherit(shot_entry)
        self.assertEquals(shot_entry.value, 'Maya 2015 Shot 1000')
