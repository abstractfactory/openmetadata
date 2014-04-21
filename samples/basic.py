"""

This module provides basic examples for working with Open Metadata

"""

import os
import openmetadata as om
om.setup_log()

# Starting-point
path = os.path.expanduser(r'~')
om.clear(path)

location = om.Location(path)


# Add a regular string
ostring = om.Entry('simple_data', parent=location)
ostring.value = 'my simple string'

# Add a list
olist = om.Entry('mylist.list', parent=location)

# Containing three datasets..
l1 = om.Entry('item1.string', value='a string value', parent=olist)
l2 = om.Entry('item2.bool', value=True, parent=olist)
l3 = om.Entry('item3.int', value=5, parent=olist)

# ..and a dictionary..
odict = om.Entry('mydict.dict', parent=olist)

# ..with two keys
key1 = om.Entry('key1.string', value='value', parent=odict)

# One of which, we neglect to specify a value-type.
# The value-type will be determined via the Python value-type <str>
key2 = om.Entry('key2', value='value', parent=odict)

# Finally, write it to disk.
om.dump(location)

# ----------- Read it back in


assert om.read(path) == ['mylist', 'simple_data']

assert om.read(path, 'mylist') == ['item2', 'item3', 'item1', 'mydict']

assert om.read(path, 'mylist/item2') is True


# ------------ Remove additions


om.clear(path)
