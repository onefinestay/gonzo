from ConfigParser import ConfigParser
from tempfile import NamedTemporaryFile
from mock import patch, Mock
import pytest

from gonzo.config import GlobalState


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
            with NamedTemporaryFile() as tmp_file:
                a = ConfigParser()
                a.add_section('gonzo')
                a.set('gonzo', 'cloud', 'cloudname')
                a.set('gonzo', 'region', 'regionname')
                a.write(tmp_file)
                tmp_file.flush()

                with patch('gonzo.config.global_state',
                           GlobalState(tmp_file.name)):

                    yield get_config_module
