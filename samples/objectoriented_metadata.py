
"""

Working with Object-oriented metadata as per RFC12
http://rfc.abstractfactory.io/spec/12/

Three stages
    1. Create some metadata
    2. Override metadata via child
    3. Read child, witnessing inherited and overridden metadata.

"""

import os
import openmetadata as om
from openmetadata import instance

om.setup_log('openmetadata', 'CRITICAL')

parent_path = os.path.expanduser(r'~\om_temp')
child_path = os.path.join(parent_path, 'child')


def setup():
    # Starting-point

    if not os.path.exists(parent_path):
        os.mkdir(parent_path)

    parent_location = om.Location(parent_path)

    # Make two nodes, a Group and Dataset, that will eventually
    # become "inherited" by locations up the hierarchy via the
    # use of the Instance object.

    # For this example, we'll mimic the behaviour of CSS
    # http://en.wikipedia.org/wiki/Cascading_Style_Sheets
    om.Dataset('background', data='red', parent=parent_location)
    om.Dataset('style', data='outset', parent=parent_location)
    om.Dataset('width', data='1px', parent=parent_location)

    # Double-check we got what we expect..
    assert om.dumps(parent_location) == {
        'background': 'red',
        'width': '1px',
        'style': 'outset'
    }

    # ..aaand write to disk.
    om.dump(parent_location)


def override_inherited():
    """Override 'style' in child_path, inherited from parent_location"""
    if not os.path.exists(child_path):
        os.mkdir(child_path)

    child_location = om.Location(child_path)
    om.Dataset('style', 'solid', parent=child_location)
    om.Dataset('new', 'new data!', parent=child_location)
    om.dump(child_location)


def read():
    # Read inherited metadata from child location
    child_instance = instance.Instance(child_path)

    # Metadata is accessed as though it were instance variables.
    # And metadata acts as though child_path were inherited from
    # parent_path, where 'background' was originally written.
    assert child_instance.background.data == 'red'

    # Better yet, data in children with the same name as in
    # parents effectively "override" the "inherited" data.
    assert child_instance.style.data == 'solid'

    # Finally, original data preseverd, as we would expect
    assert child_instance.new.data == 'new data!'


# Create the initial hierarchy on disk
setup()

# Override 'style'
override_inherited()

# Read from it, via Instance
read()

print "Success!"
