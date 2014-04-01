import types

import pytest
from mock import Mock, patch

from gonzo.backends import (
    get_current_cloud, get_dns_service, get_next_hostname,
    create_if_not_exist_security_group, launch_instance
)


@pytest.yield_fixture(autouse=True)
def state():
    state = {
        'cloud': 'openstack',
        'region': 'regionname',
    }
    with patch('gonzo.config.global_state', state):
        yield


class TestBackends(object):
    @pytest.mark.parametrize("cloud_name", [
        "amazon",
        "openstack",
    ])
    def test_get_cloud(self, cloud_name):
        config = types.ModuleType('Config', 'Dummy gonzo config')
        config.CLOUDS = {
            'amazon': {
                'BACKEND': 'gonzo.backends.aws',
            },
            'openstack': {
                'BACKEND': 'gonzo.backends.openstack',
            }
        }

        state = {
            'cloud': cloud_name,
            'region': 'regionname',
        }

        with patch('gonzo.config.get_config_module') as get_config_module, \
             patch('gonzo.config.global_state', state):

            get_config_module.return_value = config


            with patch('gonzo.config.global_state', state):
                cloud = get_current_cloud()

                assert cloud.name == cloud_name

    @patch('boto.route53.connection.Route53Connection')
    def test_get_route53_service(self, connection):
        config = types.ModuleType('Config', 'Dummy gonzo config')
        config.CLOUDS = {
            'openstack': {
                'BACKEND': 'gonzo.backends.openstack',
                'DNS_SERVICE': 'route53',
                'DNS_ZONE': 'example.com',
                'AWS_ACCESS_KEY_ID': 'ABC',
                'AWS_SECRET_ACCESS_KEY': 'ABC',
            }
        }

        with patch('gonzo.config.get_config_module') as get_config_module:
            get_config_module.return_value = config
            dns_service = get_dns_service()

            assert dns_service.name == 'route53'

    def test_get_dummy_service(self):
        config = types.ModuleType('Config', 'Dummy gonzo config')
        config.CLOUDS = {
            'openstack': {
                'BACKEND': 'gonzo.backends.openstack',
                'DNS_SERVICE': 'dummy',
            }
        }

        with patch('gonzo.config.get_config_module') as get_config_module:
            get_config_module.return_value = config
            dns_service = get_dns_service()

            assert dns_service.name == 'dummy'

    def test_dummy_is_default(self):
        config = types.ModuleType('Config', 'Dummy gonzo config')
        config.CLOUDS = {
            'openstack': {
                'BACKEND': 'gonzo.backends.openstack',
            }
        }

        with patch('gonzo.config.get_config_module') as get_config_module:
            get_config_module.return_value = config
            dns_service = get_dns_service()

            assert dns_service.name == 'dummy'

    @patch('boto.route53.connection.Route53Connection')
    @patch('gonzo.backends.get_current_cloud')
    def test_route53_get_next_hostname(self, get_cloud, connection):
        cloud = Mock()
        r53 = Mock()
        cloud.dns = r53
        cloud.dns.get_values_by_name.return_value = ['record']
        get_cloud.return_value = cloud

        config = types.ModuleType('Config', 'Dummy gonzo config')
        config.CLOUDS = {
            'openstack': {
                'BACKEND': 'gonzo.backends.openstack',
                'DNS_SERVICE': 'route53',
                'DNS_ZONE': 'example.com',
                'AWS_ACCESS_KEY_ID': 'ABC',
                'AWS_SECRET_ACCESS_KEY': 'ABC',
            }
        }

        with patch('gonzo.config.get_config_module') as get_config_module:
            get_config_module.return_value = config

            name = get_next_hostname('prod')

            # check expected calls
            assert r53.get_values_by_name.called
            assert r53.update_record.called

            assert name == 'prod-001'


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
