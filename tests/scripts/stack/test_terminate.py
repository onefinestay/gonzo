from mock import Mock, patch

from gonzo.scripts.stack.terminate import terminate


@patch('gonzo.scripts.stack.terminate.show_delete_progress')
@patch('gonzo.scripts.stack.terminate.terminate_stack')
def test_terminate(terminate_stack, show_delete_progress):
    terminate_stack.return_value = Mock(name='stackname')
    params = Mock(stack_name='stackname')
    terminate(params)

    assert terminate_stack.called
    assert show_delete_progress.called
