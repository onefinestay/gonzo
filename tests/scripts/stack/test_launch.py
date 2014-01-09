from mock import Mock, patch

from gonzo.scripts.stack.launch import launch


@patch('gonzo.scripts.stack.launch.print_stack')
@patch('gonzo.scripts.stack.launch.wait_for_stack_complete')
@patch('gonzo.scripts.stack.launch.launch_stack')
def test_launch(launch_stack, wait_for_stack_complete, print_stack):
    instance = Mock(name="instance")
    stack = Mock(name='stack')
    stack.get_instances.return_value = [instance]

    launch_stack.return_value = stack

    params = Mock(stack_name='stack', template='template')
    launch(params)

    assert launch_stack.called
    assert instance.create_dns_entries_from_tag.called
    assert wait_for_stack_complete.called
    assert print_stack.called
