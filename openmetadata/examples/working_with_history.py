"""

This module provides examples for working with history

"""

raise NotImplementedError

import os
import time
import openmetadata as om
om.setup_log()

# Starting-point
path = os.path.expanduser(r'~/om')

# Add and modify data, with 1.2 seconds inbetween changes.
# *note: History is stored in seconds. Any changes occuring within
# 1 second will be overwritten. Not what you want? Let us know.
# https://groups.google.com/forum/#!forum/open-metadata

om.write(path, 'girlfriend', 'Lucy Lui')
print "Sleeping for 1.2 seconds.."
time.sleep(1.2)
om.write(path, 'girlfriend', 'Sandra Bullock')

assert om.read(path, 'girlfriend') == 'Sandra Bullock'

# To get the history, we must first get an
# instance of the Dataset 'girlfriend'
dataset = om.read(path, 'girlfriend', convert=False)
imprint = next(om.history(dataset))
om.restore(imprint, removehistory=False)

assert om.read(path, 'girlfriend') == 'Lucy Lui'
