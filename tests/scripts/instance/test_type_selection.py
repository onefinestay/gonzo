from mock import Mock, patch
from gonzo.backends import launch_instance


@patch('gonzo.backends.create_if_not_exist_security_group')
@patch('gonzo.backends.get_next_hostname')
@patch('gonzo.backends.get_current_cloud')
def test_default_type(get_cloud,
                      get_hostname,
                      create_security_group, minimum_config_fixture):
    cloud = Mock(name='cloud')
    get_cloud.return_value = cloud
    get_hostname.return_value = 'prod-100'

    launch_instance('environment-server')

    assert cloud.launch_instance.called

    args, kwargs = cloud.launch_instance.call_args
    (name, image_name, instance_type,
     zone, key_name, tags) = args

    assert instance_type == 'instance_type.default'


@patch('gonzo.backends.create_if_not_exist_security_group')
@patch('gonzo.backends.get_next_hostname')
@patch('gonzo.backends.get_current_cloud')
def test_instance_specific_type(get_cloud,
                                get_hostname,
                                create_security_group, minimum_config_fixture):
    cloud = Mock(name='cloud')
    get_cloud.return_value = cloud
    get_hostname.return_value = 'prod-100'

    launch_instance('environment-role-specific')

    assert cloud.launch_instance.called

    args, kwargs = cloud.launch_instance.call_args
    (name, image_name, instance_type,
     zone, key_name, tags) = args

    assert instance_type == 'instance_type.role_specific'


@patch('gonzo.backends.create_if_not_exist_security_group')
@patch('gonzo.backends.get_next_hostname')
@patch('gonzo.backends.get_current_cloud')
def test_cli_specified_type(get_cloud,
                            get_hostname,
                            create_security_group, minimum_config_fixture):
    cloud = Mock(name='cloud')
    get_cloud.return_value = cloud
    get_hostname.return_value = 'prod-100'

    launch_instance('environment-role-specific',
                    size="instance_type.overwritten")

    assert cloud.launch_instance.called

    args, kwargs = cloud.launch_instance.call_args
    (name, image_name, instance_type,
     zone, key_name, tags) = args

    assert instance_type == 'instance_type.overwritten'
