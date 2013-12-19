from mock import Mock, patch
from gonzo.backends.base import launch_instance


@patch('gonzo.backends.base.create_if_not_exist_security_group')
@patch('gonzo.backends.base.config')
@patch('gonzo.backends.base.get_next_hostname')
@patch('gonzo.backends.base.get_current_cloud')
def test_default_type(get_cloud,
                      get_hostname,
                      config,
                      create_security_group):
    cloud = Mock(name='cloud')
    get_cloud.return_value = cloud
    get_hostname.return_value = 'prod-100'

    config.SIZES = {
        'default': 'instance_type.default',
        'role-specific': 'instance_type.role_specific',
        'role-extra': 'instance_type.role_specific',
    }

    launch_instance('environment-server')

    assert cloud.launch.called

    args, kwargs = cloud.launch.call_args
    (name, image_name, instance_type,
     zone, key_name, tags) = args

    assert instance_type == 'instance_type.default'


@patch('gonzo.backends.base.create_if_not_exist_security_group')
@patch('gonzo.backends.base.config')
@patch('gonzo.backends.base.get_next_hostname')
@patch('gonzo.backends.base.get_current_cloud')
def test_instance_specific_type(get_cloud,
                                get_hostname,
                                config,
                                create_security_group):
    cloud = Mock(name='cloud')
    get_cloud.return_value = cloud
    get_hostname.return_value = 'prod-100'

    config.SIZES = {
        'default': 'instance_type.default',
        'role-specific': 'instance_type.role_specific',
        'role-extra': 'instance_type.role_specific',
    }

    launch_instance('environment-role-specific')

    assert cloud.launch.called

    args, kwargs = cloud.launch.call_args
    (name, image_name, instance_type,
     zone, key_name, tags) = args

    assert instance_type == 'instance_type.role_specific'


@patch('gonzo.backends.base.create_if_not_exist_security_group')
@patch('gonzo.backends.base.config')
@patch('gonzo.backends.base.get_next_hostname')
@patch('gonzo.backends.base.get_current_cloud')
def test_cli_specified_type(get_cloud,
                            get_hostname,
                            config,
                            create_security_group):
    cloud = Mock(name='cloud')
    get_cloud.return_value = cloud
    get_hostname.return_value = 'prod-100'

    config.SIZES = {
        'default': 'instance_type.default',
        'role-specific': 'instance_type.role_specific',
        'role-extra': 'instance_type.role_specific',
    }

    launch_instance('environment-role-specific',
                    instance_type="instance_type.overwritten")

    assert cloud.launch.called

    args, kwargs = cloud.launch.call_args
    (name, image_name, instance_type,
     zone, key_name, tags) = args

    assert instance_type == 'instance_type.overwritten'
