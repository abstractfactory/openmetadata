"""

This module provides answers with solutions to commonly asked questions.

Have a question? Add it here and submit a pull request on github,
someone will include an answer and it will become available to you
and others in an upcoming patch.

https://github.com/abstractfactory/openmetadata

"""

import os

import openmetadata as om

path = os.path.expanduser(r'~/examples')

"""
Q: Why associate metadata with content?

A: To support the notion of programmable content. Like with documentation
    and the code it documents, metadata changes often and storing it
    separately from where it is consumed often leads to out-of-date
    information. Open Metadata allows for an "eat your own dog-food"-
    methodology in that metadata is not only stored but used as well.

"""


def why_simple_data():
    """Store data that we might need to change later"""
    location = om.Location(path)
    girlfriend = om.Dataset('girlfriend', parent=location)
    girlfriend.value = 'Sweet Heartsson'
    om.dump(girlfriend)
    om.clear(path)


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
    myvalue = om.Variable('myvalue', parent=location)
    myvalue.value = '/path/to/myvalue.json'
    myvalue.isblob = True
    om.dump(myvalue)

    # Retreiving stored blob
    myvalue = om.read(path, 'myvalue')
    myvalue.path
    # --> '/project/asset/.meta/myvalue.json'

    assert myvalue.value == myvalue.path


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
    | ['entry1', 'entry2' ] |---->| /location/.meta/myvalue.list/0.string     |
    |_______________________| |   |___________________________________________|
                              |
                              |    ___________________________________________
                              |   |                                           |
                              \-->| /location/.meta/myvalue.list/1.string     |
                                  |___________________________________________|

    The advantage of each ultimately depends on your use-case, but in short:

    - If control > performance, use Open Metadata-types
    - If control < performance, use Blobs

    """
    raise NotImplementedError

    location = om.Location(path)
    myvalue = om.Variable('myvalue', parent=location)
    myvalue.value = ['entry1', 'entry2']
    om.dump(myvalue)

    # Retreiving stored blob
    myvalue = om.read(path, 'myvalue')
    myvalue == ['entry1', 'entry2']

    assert myvalue.value != myvalue.path


"""
Q: How do I traverse a hierarchy?

"""
