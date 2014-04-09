"""

Implementation of object-oriented Metadata as per RFC12
http://rfc.abstractfactory.io/spec/12/

"""

from openmetadata import lib
from openmetadata import api
from openmetadata import error


class Instance(object):
    def __str__(self):
        return self.path.name

    def __repr__(self):
        return u"%s(%r)" % (self.__class__.__name__, self.__str__())

    def __init__(self, path):
        if isinstance(path, basestring):
            path = lib.Path(path)

        self.path = path

    def __getattr__(self, attr):
        """
        Return immediate children of self

        Dataset
            First dataset found in parenthood is returned

        Group
            First group found in parenthood is merged
            with additional groups found up-stream.

            |--location
               |--GROUP
               |  |--dataset1 <-- is overwritten
               |  |--dataset2
               |--sublocation
                  |--GROUP
                     |--dataset1 <-- overwrites

            Here, GROUP of sublocation is merged with GROUP of
            location, resulting in dataset1 from sublocation and
            dataset2 from location.

        """
        found = self._find_in_parenthood(self.path, attr)

        if found:
            api.pull(found)

            if api.isdataset(found):
                return found

            if api.isgroup(found):
                data = found.data

                parenthood = self._parenthood(found.metapath)
                for additional_node in parenthood:
                    if not additional_node in data:
                        data.append(additional_node)

                return data

        message = "%r has no metadata %r" % (self.path.as_str, attr)
        raise AttributeError(message)

    def __setattr__(self, attr, data):
        raise NotImplementedError
        print "Setting %s to %s" % (data, attr)

    @classmethod
    def _find_in_parenthood(cls, root, metapath):
        """Find `metapath` in `root` parent-hood"""
        parent = root
        try:
            return api.metadata(parent.as_str, metapath)
        except error.Exists:
            parent = parent.parent

            if not parent:
                return None

            return cls._find_in_parenthood(parent, metapath)

    def _parenthood(self, metapath):
        """Add contents of groups with identical metapath of `group`"""

        data = []

        parent = self.parent
        while parent:
            try:
                additional_group = api.metadata(parent.path.as_str, metapath)
                api.pull(additional_group)
                data.extend(additional_group.data)

            except error.Exists:
                pass

            parent = parent.parent

        return data

    @property
    def parent(self):
        parent_path = self.path.parent
        if not parent_path:
            return None
        return self.__class__(parent_path)


if __name__ == '__main__':
    from pprint import pprint
    inst = Instance(r'c:\users\marcus\om2\subom2')
    # print api.dumps(inst.location)
    inst.testing = 5
    # print inst.notexist
    # print inst.parent.age
