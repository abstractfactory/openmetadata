"""

This module provides examples for working with versions

"""

raise NotImplementedError

import os
import openmetadata as om

# Starting-point
path = os.path.expanduser(r'~/om')

location = om.Location(path)

# Add a regular string
password = om.Dataset('password.string', parent=location)
password.data = 'abcdef'

# Write first occurence of dataset
om.flush(password)

# Save version and update dataset
om.save(password)
password.data = 'Sandra Bullock'
om.flush(password)

assert om.read(path, 'password') == 'Sandra Bullock'

# Restore previous value from history
# *note: om.history() returns a Python generator.
imprint = om.history(password).next()
om.restore(imprint)

assert om.read(path, 'password') == 'Lucy Lui'
