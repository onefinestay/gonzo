from mock import Mock, patch

from gonzo.backends import (get_next_hostname,
                            create_if_not_exist_security_group,
                            launch_instance)


@patch('gonzo.backends.create_if_not_exist_security_group')
@patch('gonzo.backends.get_next_hostname')
@patch('gonzo.backends.get_current_cloud')
def test_launch_instance(get_cloud,
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



@patch('gonzo.backends.dns.route53.DNS')
def test_route53_get_next_hostname(Route53):
    r53 = Route53()
    r53.get_values_by_name.return_value = ['9']
    name = get_next_hostname('prod')

    # check expected calls
    assert r53.get_values_by_name.called
    assert r53.update_record.called
    assert not r53.add_remove_record.called

    assert name == 'prod-010'


@patch('gonzo.backends.get_current_cloud')
def create_if_not_exist_security_group_creates(cloud):
    cloud().security_group_exists.return_value = False

    create_if_not_exist_security_group('env')

    assert cloud().create_security_group.called


@patch('gonzo.backends.get_current_cloud')
def create_if_not_exist_security_group_skips(cloud):
    cloud().security_group_exists.return_value = True

    create_if_not_exist_security_group('env')

    assert not cloud().create_security_group.called
