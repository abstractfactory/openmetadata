"""

This module provides examples for working with versions

"""

import os
import openmetadata as om

# Starting-point
path = os.path.expanduser(r'~\om_temp')

if not os.path.exists(path):
    os.mkdir(path)

location = om.Location(path)

# Add a regular string
password = om.Dataset('password.string', parent=location)
password.data = 'abcdef'

# Write first occurence of dataset
om.dump(password)

# Save version and update dataset
om.save(password)
password.data = 'Sandra Bullock'
om.dump(password)

assert om.read(path, 'password') == 'Sandra Bullock'

# Restore previous value from history
# *note: om.history() returns a Python generator.
imprint = om.history(password).next()
om.restore(imprint)

assert om.read(path, 'password') == 'Lucy Lui'
