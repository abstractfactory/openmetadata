
def suffix_not_resolved():
    print """# BUG01 - Suffix Not Resolved
\tA suffix was not properly resolved. Have a look at the Path object,
\tit should've been copying the current relative path along with a
\tresolved suffix that it got from api.python_to_string()
"""
    return 'bug'


def not_a_node(obj):
    print """# BUG02 - Not a Node
\t%r must be inherited from lib.Node""" % obj

    return 'bug'


def not_deleted(path):
    print """# BUG03 - Not Deleted
\t%r didn't get deleted as expected. This may be due to Dropbox or a
\tsimilar service running in the background, preventing OM from
\tperforming its duties.
"""
    return 'bug'
