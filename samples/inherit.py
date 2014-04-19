import os

import openmetadata as om
import openmetadata.api as api
om.setup_log()

level1 = os.path.expanduser('~')
level2 = os.path.join(level1, 'level2')
level3 = os.path.join(level2, 'level3')

if not os.path.exists(level3):
    os.makedirs(level3)

# om.write(level1, '/address/street', 'Code Street 5')
# om.write(level1, '/address/postcode', 'XOXO XO')

# om.write(level2, '/address/city', 'Code City')
# om.write(level2, '/address/postcode', 'ZOZO ZO')

# print om.read(level2, native=False)
location = om.Location(level2)
# om.pull(location)
# print location['address']._children
# address = om.Group('address', parent=location)
# street = om.Dataset('street', parent=address)
api.inherit(location)
print location._children
# print location._children
# api.pull(street)
# print street.data
# print address._children
