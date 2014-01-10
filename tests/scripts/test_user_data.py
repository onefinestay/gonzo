from tempfile import NamedTemporaryFile

from mock import Mock, patch
from gonzo.config import config_proxy as config

from gonzo.backends import get_data
from gonzo.scripts.instance.launch import csv_dict
from gonzo.test_utils import assert_called_with


def test_config_specified_file_source(minimum_config_fixture):
    """ Test that a user data file can be specified from cloud configuration
    and then rendered with config based parameters """

    desired_subs = {
        'key_1': 'config_value_1',
        'key_2': 'config_value_2',
    }

    hostname = 'staging-test-host-001'

    with NamedTemporaryFile() as tmp_file:
        for key in desired_subs.keys():
            tmp_file.write("{{%s}} " % key)
        tmp_file.flush()

        minimum_config_fixture
        config.CLOUD.update({
            'DEFAULT_USER_DATA': tmp_file.name,
            'USER_DATA_PARAMS': desired_subs
        })

        uri = config.get_cloud_config('DEFAULT_USER_DATA', override=None)
        user_data = get_data(entity_name=hostname, uri=uri,
                             config_params_key='USER_DATA_PARAMS',
                             additional_params=None)

    for value in desired_subs.values():
        assert value in user_data


@patch('gonzo.backends.requests.get')
def test_arg_specified_url_source(req, minimum_config_fixture):
    """ Test that a user data file can be specified from cloud configuration
    and then rendered with config and argument based parameters"""

    hostname = 'staging-test-host-001'

    desired_subs = {
        'key_1': 'config_value_1',
        'key_2': 'argument_value_2',
        'hostname': hostname,
    }

    config_params = {
        'key_1': 'config_value_1',
        'key_2': 'config_value_2',
    }
    config_ud_url = 'http://this.should.not.be.requested.com/user-data.txt'
    config.CLOUD.update({
        'DEFAULT_USER_DATA': config_ud_url,
        'USER_DATA_PARAMS': config_params,
    })

    cli_params = csv_dict('key_2=argument_value_2')
    cli_uri = 'http://this.should.be.requested.com/user-data.txt'
    uri = config.get_cloud_config('DEFAULT_USER_DATA', override=cli_uri)

    ud_contents = ""
    for key in desired_subs.keys():
        ud_contents += "{{%s}} " % key
    req.return_value = Mock(text=ud_contents, status_code=200)

    user_data = get_data(entity_name=hostname, uri=uri,
                         config_params_key='USER_DATA_PARAMS',
                         additional_params=cli_params)

    assert_called_with(req, uri)
    for value in desired_subs.values():
        assert value in user_data
