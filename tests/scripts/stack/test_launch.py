import pytest
from mock import DEFAULT, Mock, patch

from gonzo.backends.aws.cloud import Cloud as AWSCloud
from gonzo.backends.dns_services.dummy import DummyDNS
from gonzo.backends.openstack.cloud import Cloud as OpenStackCloud
from gonzo.scripts.stack.launch import launch


@pytest.mark.parametrize("cloud", [
    OpenStackCloud(),
    AWSCloud(),
])
@patch('gonzo.scripts.stack.launch.print_stack')
@patch('gonzo.scripts.stack.launch.wait_for_stack_complete')
@patch('gonzo.scripts.stack.launch.launch_stack')
@patch('gonzo.scripts.stack.launch.get_current_cloud')
def test_launch(
        mock_get_current_cloud, mock_launch_stack,
        mock_wait_for_stack_complete, mock_print_stack,
        cloud, config, openstack_state):

    with patch.multiple(
            cloud, _get_dns_service=DEFAULT, launch_stack=DEFAULT
            ) as mock_methods:

        mock_get_current_cloud.return_value = cloud

        instance = Mock(name='instance')
        stack = Mock(name='stack')
        stack.get_instances.return_value = [instance]

        mock_methods['_get_dns_service'].return_value = DummyDNS()
        mock_methods['launch_stack'].return_value = stack

        params = Mock(stack_name='stackname', template_uri=None,
                      template_params=None, create_images=False,
                      delete_after_complete=False, quiet=False)

        launch(params)

        assert mock_launch_stack.called
        assert mock_wait_for_stack_complete.called
        assert mock_print_stack.called
