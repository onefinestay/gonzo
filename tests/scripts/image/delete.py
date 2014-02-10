from mock import Mock
from gonzo.exceptions import NoSuchResourceError, MultipleResourcesError
from gonzo.scripts.image.delete import image_delete
from gonzo.test_utils import assert_called_with


def test_no_image_to_delete(cloud_fixture):

    cloud_fixture.get_image_by_name = Mock(side_effect=NoSuchResourceError)

    params = Mock(image_name='image_name')
    try:
        image_delete(params)
    except:
        pass

    assert not cloud_fixture.delete_image.called


def test_no_unique_image_to_delete(cloud_fixture):

    cloud_fixture.get_image_by_name = Mock(side_effect=MultipleResourcesError)

    params = Mock(image_name='image_name')
    try:
        image_delete(params)
    except:
        pass

    assert not cloud_fixture.delete_image.called


def test_delete_ok(cloud_fixture):

    image = Mock(image_name='image_name')
    cloud_fixture.get_image_by_name.return_value = image

    params = Mock(image_name='image_name')
    image_delete(params)

    assert_called_with(cloud_fixture.delete_image, image)
