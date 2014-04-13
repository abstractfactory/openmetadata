"""

This module provides basic examples for working with Open Metadata

"""

import os
import openmetadata as om

# Starting-point
path = os.path.expanduser(r'~\om_temp')

if not os.path.exists(path):
    os.mkdir(path)

location = om.Location(path)

# Add a regular string
ostring = om.Dataset('simple_data.string', parent=location)
ostring.data = 'my simple string'

# Add a list
olist = om.Group('mylist.list', parent=location)

# Containing three datasets..
l1 = om.Dataset('item1.string', data='a string value', parent=olist)
l2 = om.Dataset('item2.bool', data=True, parent=olist)
l3 = om.Dataset('item3.int', data=5, parent=olist)

# ..and a dictionary..
odict = om.Group('mydict.dict', parent=olist)

# ..with two keys
key1 = om.Dataset('key1.string', data='value', parent=odict)

# One of which, we neglect to specify a data-type.
# The data-type will be determined via the Python data-type <str>
key2 = om.Dataset('key2', data='value', parent=odict)

# Finally, write it to disk.
om.dump(location)


# ----------- Read it back in


# path = r'c:\users\marcus\om2'
print om.read(path)
# --> [List('mylist.list'), String('simple_data.string')]

print om.read(path, 'mylist')
# --> [Bool('item2.bool'), Int('item3.int'), ...]

print om.read(path, 'mylist/item2')
# # --> True

# assert om.read == om.listdir

for item in om.read(path):
    print item
# # --> c:\users\marcus\om2\.meta\mylist.list
# --> c:\users\marcus\om2\.meta\simple_data.string
