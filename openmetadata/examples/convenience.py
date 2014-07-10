"""

This module provides examples of Open Metadata convenience methods

Convenience methods are provided as a means of reading and writing
metadata where requirements in functionality and performance are low;
such as in debugging or one-off reading/writing.

"""

import shutil
import tempfile
import openmetadata as om

om.setup_log('openmetadata')

# Starting-point
root = tempfile.mkdtemp()

try:
    om.write(root, 'status', True)
    om.write(root, 'story', 'There once was a boy')
    om.write(root, 'age', 27)

    data = {
        'firstname': 'Marcus',
        'lastname': 'Ottosson',
        'email': 'konstruktion@gmail.com'
    }

    for key, value in data.iteritems():
        om.write(root, key, value)

    # Write deeply nested data
    om.write(root, '/root/group/amazing', True)

    # Successfully wrote: c:\users\marcus\om_temp\.meta\status.bool
    # Successfully wrote: c:\users\marcus\om_temp\.meta\story.string
    # Successfully wrote: c:\users\marcus\om_temp\.meta\age.int
    # Successfully wrote: c:\users\marcus\om_temp\.meta\lastname.string
    # Successfully wrote: c:\users\marcus\om_temp\.meta\email.string
    # Successfully wrote: c:\users\marcus\om_temp\.meta\firstname.string
    # Successfully wrote: c:\users\marcus\om_temp\.meta\root.dict\group.dict\amazing.bool

    # --------- Read it back in

    assert om.read(root, '/age') == 27
    assert om.read(root, '/status') is True
    assert om.read(root, '/root/group/amazing') is True

finally:
    shutil.rmtree(root)
