
import openmetadata_mk2 as om
from nose.tools import assert_true


def test_location_path():
    location = om.Location(r'c:\users')
    assert_true(location.path == r'c:\users\.meta')


if __name__ == '__main__':
    import nose
    nose.run(defaultTest=__name__)
