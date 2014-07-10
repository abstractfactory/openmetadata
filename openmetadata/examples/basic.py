"""

This module provides basic examples for working with Open Metadata

"""

import os
import openmetadata as om
om.setup_log()

# Starting-point
path = os.path.expanduser(r'~/om')
om.clear(path)

location = om.Location(path)

# Add a regular string
ostring = om.Entry('simple_data', parent=location)
ostring.value = 'my simple string'

# Add a list
olist = om.Entry('mylist.list', parent=location)

# Containing three datasets..
l1 = om.Entry('item1', value='a string value', parent=olist)
l2 = om.Entry('item2', value=True, parent=olist)
l3 = om.Entry('item3', value=5, parent=olist)

# Add an entry with default value of type `bool`
l4 = om.Entry('item4.bool', parent=olist)

# ..and a dictionary..
odict = om.Entry('mydict.dict', parent=olist)

# ..with two keys
key1 = om.Entry('key1.string', value='value', parent=odict)

# One of which, we neglect to specify a value-type.
# The value-type will be determined via the Python value-type <str>
key2 = om.Entry('key2', value='value', parent=odict)

# Finally, write it to disk.
om.flush(location)

# ----------- Read it back in

print om.read(path, 'mylist.list')
# assert om.read(path) == ['mylist', 'simple_data']

# assert om.read(path, 'mylist') == ['item2', 'item3', 'item1', 'mydict']

# assert om.read(path, 'mylist/item2') is True


# ------------ Remove additions


# om.clear(path)
