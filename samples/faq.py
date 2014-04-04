import os

import openmetadata as om

userpath = os.path.expanduser('~')

"""
Q: Why store simple data in folders?
A: To support the notion of programmable folders. Like with programming,
    metadata changes often and storing it separately from where it is
    consumed often leads to out-of-date information. Open Metadata allows
    for an "eat your own dog-food" methodology.

"""


def why_simple_data():
    """Store data that we might need to change later"""
    location = om.Location(userpath)
    girlfriend = om.Dataset('girlfriend', parent=location)
    girlfriend.data = 'Some Girlsson'
    om.dump(girlfriend)


"""
Q: How do I concatenate paths?
A: With Open Metadata nodes, there should be very little reason to have
    to manually concatenate paths. The reason this is is because Open
    Metadata could run on any platform, and won't necessarily be dealing
    with paths on a file-system, they might be paths in a database.
"""


def no_concatenation():
    location = om.read(userpath)
    firstchild = location.children.next()

    parent_dir = os.path.dirname(firstchild.path)
    otherchild_path = os.path.join(parent_dir, 'guessed_path')

    # As dataset expects a relative name, this won't work.
    try:
        otherchild_node = om.Dataset(name=otherchild_path, parent=location)
    except:
        print "Defeated.."


"""
Q: How do I traverse a hierarchy?
A: 
"""
