import os
import shutil
import tempfile

import openmetadata as om
# om.setup_log()  # <-- Uncomment this line to get debug information

try:
    root = tempfile.mkdtemp()

    level1 = root
    level2 = os.path.join(level1, 'level2')
    level3 = os.path.join(level2, 'level3')

    om.write(level1, '/address/street', value='Code Street 5')
    om.write(level1, '/address/postcode', value='Level 1 postcode')

    om.write(level2, '/address/city', value='Code City')
    om.write(level2, '/address/postcode', value='Level 2 postcode')

    assert os.path.exists(os.path.join(level1, '.meta'))
    assert os.path.exists(os.path.join(level2, '.meta'))

    # Now that we have written a hierarchy of values,
    # let's try and reach `street` from level2, even
    # though `street` resides in level1
    location = om.Location(level2)
    om.pull(location)

    address = location['address']
    om.pull(address)

    try:
        postcode = address['street']
    except KeyError:
        print "This is supposed to happen"

    # That won't work, since `street` isn't in level2,
    # but in level1. Let's try doing that again, but
    # this time, we will inherit data from parents of
    # level2.

    location = om.Location(level2)
    om.pull(location)

    address = location['address']
    om.inherit(address)  # <-- We will inherit, rather than pull

    try:
        postcode = address['street']
        print "Success"
    except KeyError:
        print "This is NOT supposed to happen"

except:
    raise

finally:
    shutil.rmtree(root)
