from mock import Mock, patch

from gonzo.config import config_proxy as config
from gonzo.scripts.stack.launch import launch
from gonzo.test_utils import assert_called_with


@patch('gonzo.scripts.stack.launch.print_stack')
@patch('gonzo.scripts.stack.launch.wait_for_stack_complete')
@patch('gonzo.backends.get_parsed_document')
@patch('gonzo.backends.get_current_cloud')
@patch('gonzo.backends.get_next_hostname')
def test_launch(next_hostname, get_current_cloud, get_parsed_doc,
                wait_for_stack_complete, print_stack, minimum_config_fixture):
    cloud = Mock()
    get_current_cloud.return_value = cloud

    params = Mock(stack_name='stackname', template_uri=None,
                  template_params=None)

    unique_name = 'stackname-001'
    next_hostname.return_value = unique_name

    desired_template_uri = 'do-want-this'
    config.CLOUD.update({
        'ORCHESTRATION_TEMPLATE_URIS': {
            'default': 'dont-want-this',
            'stackname': desired_template_uri,
        }
    })
    launch(params)

    assert next_hostname.called
    assert_called_with(get_parsed_doc, unique_name, desired_template_uri,
                       'ORCHESTRATION_TEMPLATE_PARAMS', None)
    assert cloud.launch_stack.called
    assert wait_for_stack_complete.called
    assert print_stack.called
