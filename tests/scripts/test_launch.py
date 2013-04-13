from mock import Mock, patch

from gonzo.scripts.launch import launch


@patch('gonzo.scripts.launch.configure_instance')
@patch('gonzo.scripts.launch.wait_for_instance_boot')
@patch('gonzo.scripts.launch.launch_instance')
def test_launch(launch_instance, boot, configure):
    launch_instance.return_value = Mock(name='instance')
    args = Mock(env_type='environment-server')
    launch(args)

    assert launch_instance.called
    assert boot.called
    assert configure.called
