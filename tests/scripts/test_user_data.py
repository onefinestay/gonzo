from mock import Mock, patch
from tempfile import NamedTemporaryFile

from gonzo.backends.base import get_user_data
from gonzo.scripts.launch import csv_dict
from gonzo.test_utils import assert_called_with


@patch('gonzo.backends.base.config')
def test_no_user_data_specified_ok(config):
    hostname = 'staging-test-host-001'

    config.CLOUD = {'DNS_ZONE': 'example.com'}

    user_data = get_user_data(hostname)

    assert user_data is None


@patch('gonzo.backends.base.config')
def test_config_specified_file_source(config):
    """ Test that a user data file can be specified from cloud configuration
    and then rendered with config based parameters """

    desired_subs = {
        'key_1': 'config_value_1',
        'key_2': 'config_value_2'
    }

    hostname = 'staging-test-host-001'

    with NamedTemporaryFile() as tmp_file:
        for key in desired_subs.keys():
            tmp_file.write("{{%s}} " % key)
        tmp_file.flush()

        config.CLOUD = {
            'DNS_ZONE': 'example.com',
            'DEFAULT_USER_DATA': tmp_file.name,
            'USER_DATA_PARAMS': desired_subs
        }

        user_data = get_user_data(hostname)

    for value in desired_subs.values():
        assert value in user_data


@patch('gonzo.backends.base.requests.get')
@patch('gonzo.backends.base.config')
def test_arg_specified_url_source(config, req):
    """ Test that a user data file can be specified from cloud configuration
    and then rendered with config and argument based parameters"""

    hostname = 'staging-test-host-001'

    desired_subs = {
        'key_1': 'config_value_1',
        'key_2': 'argument_value_2',
        'hostname': hostname
    }

    config_params = {
        'key_1': 'config_value_1',
        'key_2': 'config_value_2'
    }
    config_ud_url = 'http://this.should.not.be.requested.com/user-data.txt'
    config.CLOUD = {
        'DNS_ZONE': 'example.com',
        'DEFAULT_USER_DATA': config_ud_url,
        'USER_DATA_PARAMS': config_params
    }

    params = csv_dict('key_2=argument_value_2')
    uri = 'http://this.should.be.requested.com/user-data.txt'

    ud_contents = ""
    for key in desired_subs.keys():
        ud_contents += "{{%s}} " % key
    req.return_value = Mock(text=ud_contents, status_code=200)

    user_data = get_user_data(hostname, uri, params)

    assert assert_called_with(req, uri)
    assert all(values in user_data for values in desired_subs.values())
