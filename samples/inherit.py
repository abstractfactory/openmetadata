import os

import openmetadata as om
# import openmetadata.api as api
# om.setup_log()

level1 = os.path.expanduser('~')
level2 = os.path.join(level1, 'level2')
level3 = os.path.join(level2, 'level3')

om.write(level1, '/address/street', 'Code Street 5')
om.write(level1, '/address/postcode', 'Level 1 postcode')

om.write(level2, '/address/city', 'Code City')
om.write(level2, '/address/postcode', 'Level 2 postcode')

# Let's try and 
location = om.Location(level2)
om.pull(location)

address = location['address']
om.pull(address)

try:
    postcode = address['street']
except KeyError:
    print "This is supposed to happen"
