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
