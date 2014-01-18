from mock import patch, Mock
import pytest


@pytest.yield_fixture
def minimum_config_fixture():
    cloud = {
        'IMAGE_NAME': 'ofo',
        'PUBLIC_KEY_NAME': 'keyname',
        'DNS_ZONE': 'test_dns',
    }
    sizes = {
        'default': 'instance_type.default',
        'role-specific': 'instance_type.role_specific',
    }

    with patch('gonzo.config.get_config_module') as get_config_module:
            get_config_module.return_value = Mock(SIZES=sizes,
                                                  CLOUDS={'cloudname': cloud})
            with patch('gonzo.config.global_state', {
                'cloud': 'cloudname',
                'region': 'regionname',
            }):
                    yield get_config_module


@pytest.yield_fixture
def cloud_fixture():
    create_sg_target = 'gonzo.backends.create_if_not_exist_security_group'
    get_host_target = 'gonzo.backends.get_next_hostname'
    get_cloud_target = 'gonzo.backends.get_current_cloud'

    with patch(create_sg_target) as create_security_group:
        with patch(get_host_target) as get_next_hostname:
            get_next_hostname.return_value = 'prod-100'
            with patch(get_cloud_target) as get_current_cloud:
                get_current_cloud.return_value = Mock(name='cloud')
                yield (get_current_cloud,
                       get_next_hostname,
                       create_security_group)
