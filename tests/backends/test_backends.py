import types

import pytest
from mock import Mock, patch, call, ANY

from gonzo import exceptions
from gonzo.backends import (
    get_current_cloud, get_next_hostname,
    create_if_not_exist_security_group, launch_instance)
from gonzo.backends.dns_services import get_dns_service
from gonzo.backends.dns_services.dummy import DummyDNS
from gonzo.backends.aws.cloud import Cloud as AWSCloud
from gonzo.backends.aws.stack import Stack as AWSStack
from gonzo.backends.openstack.cloud import Cloud as OpenStackCloud
from gonzo.backends.openstack.stack import Stack as OpenStack


SERVER_ADDRESS = '10.0.0.1'


@pytest.fixture(autouse=True)
def state(openstack_state):
    pass


class TestBackends(object):
    @pytest.mark.parametrize(("cloud_name", "stack_class"), [
        ("amazon", AWSStack),
        ("openstack", OpenStack),
    ])
    def test_get_cloud(
            self, cloud_name, stack_class, config, mock_route53_conn):

        state = {
            'cloud': cloud_name,
            'region': 'regionname',
        }

        with patch('gonzo.config.global_state', state):
            cloud = get_current_cloud()

            assert cloud.stack_class == stack_class

    def test_get_route53_service(self, config, mock_route53_conn):
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

    def test_dns_backend_required(self):
        config = types.ModuleType('Config', 'Dummy gonzo config')
        config.CLOUDS = {
            'openstack': {
                'BACKEND': 'gonzo.backends.openstack',
            }
        }

        with patch('gonzo.config.get_config_module') as get_config_module:
            get_config_module.return_value = config

            with pytest.raises(exceptions.ConfigurationError):
                get_dns_service()

    @patch('gonzo.backends.get_current_cloud')
    def test_route53_get_next_hostname(
            self, get_cloud, config, mock_route53_conn):

        cloud = Mock()
        r53 = Mock()
        cloud.dns = r53
        cloud.dns.get_values_by_name.return_value = ['record']
        get_cloud.return_value = cloud

        name = get_next_hostname('prod')

        # check expected calls
        assert r53.get_values_by_name.called
        assert r53.update_record.called

        assert name == 'prod-001'


class TestDummyDNS(object):
    @pytest.mark.parametrize("cloud", [
        OpenStackCloud(),
        AWSCloud(),
    ])
    def test_openstack_create_dns_entry(self, cloud, openstack_instance):
        with patch.object(cloud, '_get_dns_service') as mock_get_dns:
            dummy_svc = Mock(spec=DummyDNS)
            mock_get_dns.return_value = dummy_svc

            cloud.create_dns_entry(openstack_instance, name='foo')

            assert dummy_svc.add_remove_record.called

            expected_call = call('foo', ANY, SERVER_ADDRESS)
            assert expected_call == dummy_svc.add_remove_record.call_args

    def test_get_next_hostname(self, config, instances):
        with patch('gonzo.backends.base.cloud.get_dns_service') as get_dns:
            dummy_svc = Mock(spec=DummyDNS)
            dummy_svc.get_values_by_name.return_value = ['1']
            get_dns.return_value = dummy_svc

            name = 'foo'
            expected_record_name = "-".join(["_count", name])
            expected_update_call = call(expected_record_name, "TXT", '2')

            get_next_hostname(name)

            assert expected_update_call == dummy_svc.update_record.call_args

    def test_get_next_hostname_with_exception(self, config, instances):
        with patch('gonzo.backends.base.cloud.get_dns_service') as get_dns:
            dummy_svc = Mock(spec=DummyDNS)
            dummy_svc.get_values_by_name.side_effect = \
                exceptions.DNSRecordNotFoundError('test')
            get_dns.return_value = dummy_svc

            name = 'foo'
            expected_record_name = "-".join(["_count", name])
            expected_get_values_call = call(expected_record_name)
            expected_add_remove_call = call(expected_record_name, "TXT", '1')

            get_next_hostname(name)

            assert expected_get_values_call == \
                dummy_svc.get_values_by_name.call_args

            assert expected_add_remove_call == \
                dummy_svc.add_remove_record.call_args


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
