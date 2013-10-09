from mock import Mock, patch

from gonzo.backends.base import (get_next_hostname,
    create_if_not_exist_security_group, launch_instance)


@patch('gonzo.backends.base.create_if_not_exist_security_group')
@patch('gonzo.backends.base.config')
@patch('gonzo.backends.base.get_next_hostname')
@patch('gonzo.backends.base.get_current_cloud')
def test_launch_instance(get_cloud,
                         get_hostname,
                         config,
                         create_security_group):
    cloud = Mock(name='cloud')
    get_cloud.return_value = cloud
    get_hostname.return_value = 'prod-100'

    security_groups = ['gonzo', 'test']
    launch_instance('environment-server', security_groups)

    assert cloud.launch.called

    args, kwargs = cloud.launch.call_args
    (name, image_name, instance_type,
     zone, security_groups, key_name, tags) = args
    assert 'test' in security_groups
    assert security_groups.count('gonzo') == 1
    assert 'environment' in security_groups
    assert 'gonzo' in security_groups


@patch('gonzo.backends.base.Route53')
def test_get_next_hostname(Route53):
    r53 = Route53()
    r53.get_values_by_name.return_value = ['9']
    name = get_next_hostname('prod')

    # check expected calls
    assert r53.get_values_by_name.called
    assert r53.update_record.called
    assert not r53.add_remove_record.called

    assert name == 'prod-010'


@patch('gonzo.backends.base.get_current_cloud')
def create_if_not_exist_security_group_creates(cloud):
    cloud().security_group_exists.return_value = False

    create_if_not_exist_security_group('env')

    assert cloud().create_security_group.called


@patch('gonzo.backends.base.get_current_cloud')
def create_if_not_exist_security_group_skips(cloud):
    cloud().security_group_exists.return_value = True

    create_if_not_exist_security_group('env')

    assert not cloud().create_security_group.called
