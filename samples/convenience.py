"""

This module provides examples of Open Metadata convenience methods

Convenience methods are provided as a means of reading and writing
metadata where requirements in functionality and performance are low;
such as in debugging or one-off reading/writing.

"""

import os
import openmetadata as om
om.setup_log('openmetadata')

# Starting-point
path = os.path.expanduser(r'~')

om.write(path, 'status', True)
om.write(path, 'story', 'There once was a boy')
om.write(path, 'age', 27)

data = {
    'firstname': 'Marcus',
    'lastname': 'Ottosson',
    'email': 'konstruktion@gmail.com'
}

for key, value in data.iteritems():
    om.write(path, key, value)

# Write deeply nested data
om.write(path, '/root/group/amazing', True)

# Successfully wrote: c:\users\marcus\om_temp\.meta\status.bool
# Successfully wrote: c:\users\marcus\om_temp\.meta\story.string
# Successfully wrote: c:\users\marcus\om_temp\.meta\age.int
# Successfully wrote: c:\users\marcus\om_temp\.meta\lastname.string
# Successfully wrote: c:\users\marcus\om_temp\.meta\email.string
# Successfully wrote: c:\users\marcus\om_temp\.meta\firstname.string
# Successfully wrote: c:\users\marcus\om_temp\.meta\root\group\amazing.bool

# --------- Read it back in

assert om.read(path, '/root/group/amazing') is True
assert om.read(path, '/status') is True
assert om.read(path, '/age') == 27
