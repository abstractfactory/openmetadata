"""

This module provides answers with solutions to commonly asked questions.

Have a question? Add it here and submit a pull request on github,
someone will include an answer and it will become available to you
and others in an upcoming patch.

https://github.com/abstractfactory/openmetadata

"""

import os

import openmetadata as om

path = os.path.expanduser(r'~\om_temp')

# Set-up
if not os.path.exists(path):
    os.mkdir(path)

"""
Q: Why store simple data in folders?
A: To support the notion of programmable folders. Like with programming,
    metadata changes often and storing it separately from where it is
    consumed often leads to out-of-date information. Open Metadata allows
    for an "eat your own dog-food" methodology.

"""


def why_simple_data():
    """Store data that we might need to change later"""
    location = om.Location(path)
    girlfriend = om.Dataset('girlfriend', parent=location)
    girlfriend.data = 'Sweet Heartsson'
    om.dump(girlfriend)


"""
Q: How do I concatenate paths?
A: With Open Metadata nodes, there should be very little reason to have
    to manually concatenate paths. The reason this is is because Open
    Metadata could run on any platform, and won't necessarily be dealing
    with paths on a file-system, they might be paths in a database.
"""


def no_concatenation():
    location = om.read(path)
    firstchild = location.children.next()

    parent_dir = os.path.dirname(firstchild.path)
    otherchild_path = os.path.join(parent_dir, 'guessed_path')

    # As dataset expects a relative name, this won't work.
    try:
        om.Dataset(name=otherchild_path, parent=location)
    except om.error.RelativePath:
        print "Defeated.."


"""
Q: How do I traverse a hierarchy?
A: 
"""
