
import os
import subprocess

import openmetadata as om
# from nose.tools import assert_true

examples = os.path.dirname(om.__file__)
examples = os.path.join(examples, 'examples')


def test_example_basic():
    path = os.path.join(examples, 'basic.py')
    subprocess.call(['python', path])


def test_example_convenience():
    path = os.path.join(examples, 'convenience.py')
    subprocess.call(['python', path])


if __name__ == '__main__':
    import nose
    nose.run(defaultTest=__name__)
