from mock import Mock, patch

from gonzo.scripts.instance.launch import launch


@patch('gonzo.scripts.instance.launch.configure_instance')
@patch('gonzo.scripts.instance.launch.wait_for_instance_boot')
@patch('gonzo.scripts.instance.launch.launch_instance')
def test_launch(launch_instance, boot, configure):
    launch_instance.return_value = Mock(name='instance')
    params = Mock(env_type='environment-server')
    launch(params)

    assert launch_instance.called
    assert boot.called
    assert configure.called
