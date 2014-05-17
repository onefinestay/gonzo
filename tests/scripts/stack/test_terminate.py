from mock import Mock, patch

from gonzo.scripts.stack.terminate import terminate
from gonzo.test_utils import assert_called_with


@patch('gonzo.scripts.stack.terminate.show_delete_progress')
@patch('gonzo.scripts.stack.terminate.get_current_cloud')
def test_terminate(get_current_cloud, show_delete_progress):
    instance = Mock(name="instance")
    stack = Mock(name="stack")
    stack.get_instances.return_value = [instance]

    cloud = Mock(name="cloud")
    cloud.get_stack.return_value = stack
    get_current_cloud.return_value = cloud

    params = Mock(stack_name='stackname')
    terminate(params)

    assert_called_with(cloud.get_stack, 'stackname')
    assert cloud.delete_dns_entries.called
    assert stack.delete.called
    assert show_delete_progress.called
