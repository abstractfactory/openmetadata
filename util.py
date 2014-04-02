

class Process(object):
    def __str__(self):
        return str(self._processes)

    def __repr__(self):
        return u"%s(%r)" % (self.__class__.__name__, self.__str__())

    def __iter__(self):
        for process in self._processes:
            yield process

    def __nonzero__(self):
        return False if self._processes else True

    def __init__(self, processes=None):
        self._processes = processes or list()
        self.ignore = False

    def process(self, element):
        if not self.ignore:
            for process in self._processes:
                # print "\tPROCESSING: %s" % process
                element = process(element)
                if not element:
                    # In case preprocess filters out element
                    # such as when a junction target does
                    # not exist.
                    break

        return element

    def add(self, process, index=None):
        self._processes.insert(index or 0, process)

    def clear(self):
        while self._processes:
            self._processes.pop()
        return True

    def copy(self):
        processes = []
        for process in self._processes:
            if getattr(process, 'cascading', False):
                processes.append(process)
        return self.__class__(processes)

    # ------------------------ Decorators ---------------------------#

    @staticmethod
    def cascading(func):
        """Make `func` apply to outgoing objects too"""
        func.cascading = True
        return func

    @staticmethod
    def preprocess(func):
        """Make `func` a pre-process"""
        func.preprocess = True
        return func

    @staticmethod
    def postprocess(func):
        """Make `func` a post-process"""
        func.postprocess = True
        return func
