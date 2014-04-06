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
Q: Why store data in relation to folders?

A: To support the notion of programmable folders. Like with documentation
    and the code it documents, metadata changes often and storing it
    separately from where it is consumed often leads to out-of-date
    information. Open Metadata allows for an "eat your own dog-food"-
    methodology in that metadata is not only stored but used as well.

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
    with paths on a file-system; e.g. they might be paths in a database or
    any arbitrary storage-model.
"""


def no_concatenation():
    location = om.Location(path)
    firstchild = location.children.next()

    parent_dir = os.path.dirname(firstchild.path)
    otherchild_path = os.path.join(parent_dir, 'guessed_path')

    # As dataset expects a relative name, this won't work.
    try:
        om.Dataset(name=otherchild_path, parent=location)
    except om.error.RelativePath:
        print "Defeated.."


"""
Q: How do I store my lists and dicts (i.e. collection data-types)?

A: There are exactly two methods of storing any data:
    1. Blobs
    2. Open Metadata-types

"""


def storing_collection_as_blobs():
    """
    Open Metadata can store any arbitrary data as blobs. Blobs are stored
    together with its parent; i.e. in the simples of situation, blobs are
    copied from their source into the Open Metadata hierarchy.

     __________________       ____________________________
    |                  |     |                            |
    | /root/source.bin |---->| /location/.meta/source.bin |
    |__________________|     |____________________________|

    """

    raise NotImplementedError

    path = '/project/asset'
    location = om.Location(path)
    mydata = om.Blob('mydata', parent=location)
    mydata.data = '/path/to/mydata.json'
    om.dump(mydata)

    # Retreiving stored blob
    mydata = om.read(path, 'mydata')
    mydata.path
    # --> '/project/asset/.meta/mydata.json'

    assert mydata.data == mydata.path


def storing_collection_as_open_metadata():
    """
    While blobs facilitate storage of any arbitrary data, Open Metadata also
    has the notion of Open Metadata-types.

    Open Metadata-types offer extended features for plain-data, such as text,
    numbers, dates and matrices in that they may be added, subtracted, version-
    controlled and eventually end up in user interfaces as views and editors
    relevant to their specific type.

     _______________________       ___________________________________________
    |                       |     |                                           |
    | ['entry1', 'entry2' ] |---->| /location/.meta/mydata.list/entry1.string |
    |_______________________|     |___________________________________________|
                             .
                             .     ___________________________________________
                             .    |                                           |
                             .--->| /location/.meta/mydata.list/entry2.string |
                                  |___________________________________________|

    The advantage of each ultimately depends on your use-case, but in short:

    - If control > performance, use Open Metadata-types
    - If control < performance, use Blobs

    """

    raise NotImplementedError

    path = '/project/asset'
    location = om.Location(path)
    mydata = om.Group('mydata.list', parent=location)
    mydata = ['entry1', 'entry2']
    om.dump(mydata)

    # Retreiving stored blob
    mydata = om.read(path, 'mydata')
    mydata.path
    # --> '/project/asset/.meta/mydata.list'

    mydata.data
    # --> [String('entry1'), String('entry2')]

    assert mydata.data != mydata.path


"""
Q: How do I traverse a hierarchy?

A: Hierarchies are 
"""
