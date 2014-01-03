from mock import Mock, patch

from gonzo.scripts.stack.launch import launch


@patch('gonzo.scripts.stack.launch.print_stack')
@patch('gonzo.scripts.stack.launch.wait_for_stack_complete')
@patch('gonzo.scripts.stack.launch.launch_stack')
def test_launch(launch_stack, wait_for_stack_complete, print_stack):
    launch_stack.return_value = Mock(name='stackname')
    params = Mock(stack_name='stackname', template='template')
    launch(params)

    assert launch_stack.called
    assert wait_for_stack_complete.called
    assert print_stack.called
