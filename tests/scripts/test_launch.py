import pytest
from mock import Mock, patch

from gonzo.scripts.launch import get_next_hostname, \
    find_or_create_security_groups, launch

@patch('gonzo.scripts.launch.Route53')
def test_get_next_hostname(Route53):
    r53 = Route53()
    r53.get_values_by_name.return_value = ['9']
    name = get_next_hostname('prod')

    # check expected calls
    assert r53.get_values_by_name.called
    assert r53.update_record.called
    assert not r53.add_remove_record.called

    assert name == 'prod-010'


@patch('gonzo.scripts.launch.get_current_cloud')
def test_find_or_create_security_groups_creates(cloud):
    cloud().security_group_exists.return_value = False
    groups = find_or_create_security_groups('env')

    assert cloud().create_security_group.called
    assert groups == ['gonzo', 'env']


@patch('gonzo.scripts.launch.get_current_cloud')
def test_find_or_create_security_groups_skips(cloud):
    cloud().security_group_exists.return_value = True
    groups = find_or_create_security_groups('env')

    assert not cloud().create_security_group.called
    assert groups == ['gonzo', 'env']


@patch('gonzo.scripts.launch.config')
@patch('gonzo.scripts.launch.get_next_hostname')
@patch('gonzo.scripts.launch.get_current_cloud')
def test_launch(get_cloud, get_hostname, config):
    cloud = Mock(name='cloud')
    get_cloud.return_value = cloud
    get_hostname.return_value = 'prod-100'
    args = Mock(env_type='environment-server')
    launch(args)

    assert cloud.launch.called


