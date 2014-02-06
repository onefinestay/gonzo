from mock import Mock, patch

from gonzo.config import config_proxy as config
from gonzo.scripts.stack.launch import launch
from gonzo.test_utils import assert_called_with


@patch('gonzo.scripts.stack.launch.print_stack')
@patch('gonzo.scripts.stack.launch.wait_for_stack_complete')
@patch('gonzo.backends.insert_stack_owner_output')
@patch('gonzo.backends.get_parsed_document')
def test_launch(get_parsed_doc, stack_ownership, wait_for_stack_complete,
                print_stack, cloud_fixture, minimum_config_fixture):
    (get_cloud, get_hostname, create_security_group) = cloud_fixture
    cloud = get_cloud.return_value
    unique_name = get_hostname.return_value

    instance = Mock(name='instance')
    stack = Mock(name='stack')
    stack.get_instances.return_value = [instance]
    cloud.launch_stack.return_value = stack

    params = Mock(stack_name='stackname', template_uri=None,
                  template_params=None)

    desired_template_uri = 'do-want-this'
    config.CLOUD.update({
        'ORCHESTRATION_TEMPLATE_URIS': {
            'default': 'dont-want-this',
            'stackname': desired_template_uri,
        }
    })
    launch(params)

    assert get_hostname.called
    assert_called_with(get_parsed_doc, unique_name, desired_template_uri,
                       'ORCHESTRATION_TEMPLATE_PARAMS', None)
    assert cloud.launch_stack.called
    assert instance.create_dns_entries_from_tag.called
    assert wait_for_stack_complete.called
    assert print_stack.called
