from mock import Mock

from gonzo.scripts.image.create import image_create
from gonzo.test_utils import assert_called_with


def test_image_creation(cloud_fixture):
    (get_cloud, get_hostname, create_security_group) = cloud_fixture
    cloud = get_cloud.return_value

    instance = Mock(name='instance')
    cloud.get_instance_by_name.return_value = instance

    params = Mock(instance_name='instancename', image_name='imagename')
    image_create(params)

    assert_called_with(
        cloud.get_instance_by_name, 'instancename', 'imagename')
