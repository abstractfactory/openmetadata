"""

This module provides examples for working with history

"""

import os
import openmetadata as om

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

# Alter and update dataset, producing history
girlfriend.data = 'Sandra Bullock'
om.dump(girlfriend)

# Restore previous value from history
# *note: om.history() returns a Python generator.
imprint = om.history(girlfriend).next()
om.restore(imprint)

assert om.read(path, 'girlfriend') == 'Lucy Lui'
