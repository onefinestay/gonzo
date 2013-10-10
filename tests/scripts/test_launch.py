from mock import Mock, patch

from gonzo.scripts.launch import launch


@patch('gonzo.scripts.launch.configure_instance')
@patch('gonzo.scripts.launch.wait_for_instance_boot')
@patch('gonzo.scripts.launch.launch_instance')
def test_launch_with_groups(launch_instance, boot, configure):
    launch_instance.return_value = Mock(name='instance')
    params = Mock(env_type='environment-server', security_groups='test,gonzo')
    launch(params)

    assert launch_instance.called
    assert boot.called
    assert configure.called

     # Test for default groups and no duplicates
    args, kwargs = launch_instance.call_args
    security_groups = args[1]
    assert security_groups.count('gonzo') == 1
    assert sorted(security_groups) == ['environment', 'gonzo', 'test']
