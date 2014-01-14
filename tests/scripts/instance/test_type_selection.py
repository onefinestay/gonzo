from gonzo.backends import launch_instance


def test_default_type(cloud_fixture, minimum_config_fixture):
    (get_cloud, get_hostname, create_security_group) = cloud_fixture
    cloud = get_cloud.return_value

    launch_instance('environment-server')

    assert cloud.launch_instance.called

    args, kwargs = get_cloud.return_value.launch_instance.call_args
    (name, image_name, instance_type,
     zone, key_name, tags) = args

    assert instance_type == 'instance_type.default'


def test_instance_specific_type(cloud_fixture, minimum_config_fixture):
    (get_cloud, get_hostname, create_security_group) = cloud_fixture
    cloud = get_cloud.return_value

    launch_instance('environment-role-specific')

    assert cloud.launch_instance.called

    args, kwargs = cloud.launch_instance.call_args
    (name, image_name, instance_type,
     zone, key_name, tags) = args

    assert instance_type == 'instance_type.role_specific'


def test_cli_specified_type(cloud_fixture, minimum_config_fixture):
    (get_cloud, get_hostname, create_security_group) = cloud_fixture
    cloud = get_cloud.return_value

    launch_instance('environment-role-specific',
                    size="instance_type.overwritten")

    assert cloud.launch_instance.called

    args, kwargs = cloud.launch_instance.call_args
    (name, image_name, instance_type,
     zone, key_name, tags) = args

    assert instance_type == 'instance_type.overwritten'
