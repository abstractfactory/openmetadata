"""

This module provides examples for working with history

"""

import os
import time
import openmetadata as om
om.setup_log('openmetadata')

# Starting-point
path = os.path.expanduser(r'~\om_temp')

if not os.path.exists(path):
    os.mkdir(path)

location = om.Location(path)

# Add a regular string
girlfriend = om.Dataset('girlfriend.string', parent=location)
girlfriend.data = 'Lucy Lui'

# Write first occurence of dataset
om.dump(girlfriend)

# History-resolution is in seconds; i.e. only
# one imprint per second may be stored.
print "Sleeping for 1.2 seconds.."
time.sleep(1.2)

# Alter and update dataset, producing history
girlfriend.data = 'Sandra Bullock'
om.dump(girlfriend)

assert om.read(path, 'girlfriend') == 'Sandra Bullock'

# Restore previous value from history
# *note: om.history() returns a Python generator.
imprint = om.history(girlfriend).next()
om.restore(imprint, keephistory=True)

assert om.read(path, 'girlfriend') == 'Lucy Lui'
