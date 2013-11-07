from mock import Mock, patch
import os

from gonzo.backends.base import (build_user_data_params, get_user_data,
                                 load_user_data)
from gonzo.scripts.launch import csv_dict


@patch('gonzo.backends.base.config')
def test_no_user_data_specified_ok(config):
    hostname = 'staging-test-host-001'

    config.CLOUD = {'DNS_ZONE': 'example.com'}

    arg_ud_params = None
    arg_ud_uri = None

    user_data = get_user_data(hostname, arg_ud_uri, arg_ud_params)

    assert user_data is None


@patch('gonzo.backends.base.config')
def test_config_specified_file_source(config):
    """ Test that a user data file can be specified from cloud configuration
    and then rendered with config based parameters """

    desired_subs = {'key_1': 'config_value_1',
                    'key_2': 'config_value_2'}
    ud_file_path = '/tmp/test-user-data'

    with open(ud_file_path, 'w') as ud_file:
        for key in desired_subs.keys():
            ud_file.write("{{%s}} " % key)

    hostname = 'staging-test-host-001'

    config.CLOUD = {
        'DNS_ZONE': 'example.com',
        'DEFAULT_USER_DATA': ud_file_path,
        'USER_DATA_PARAMS': desired_subs
    }

    arg_ud_params = None
    arg_ud_uri = None

    params = build_user_data_params(hostname, arg_ud_params)
    user_data = load_user_data(params, arg_ud_uri)

    os.unlink(ud_file_path)
    assert all(values in user_data for values in desired_subs.values())


@patch('gonzo.backends.base.requests.get')
@patch('gonzo.backends.base.config')
def test_arg_specified_url_source(config, req):
    """ Test that a user data file can be specified from cloud configuration
    and then rendered with config and argument based parameters"""

    hostname = 'staging-test-host-001'

    desired_subs = {'key_1': 'config_value_1',
                    'key_2': 'argument_value_2',
                    'hostname': hostname}

    config_params = {'key_1': 'config_value_1',
                     'key_2': 'config_value_2'}
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

    params = build_user_data_params(hostname, params)
    user_data = load_user_data(params, uri)

    assert req.called_with(uri)
    assert all(values in user_data for values in desired_subs.values())
