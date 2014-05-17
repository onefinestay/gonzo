from mock import Mock, patch

from gonzo.scripts.instance.launch import launch


@patch('gonzo.scripts.instance.launch.wait_for_instance_boot')
@patch('gonzo.scripts.instance.launch.launch_instance')
@patch('gonzo.scripts.instance.launch.get_current_cloud')
def test_launch(
        mock_get_cloud, mock_launch_instance, mock_boot, instances):

    cloud = Mock()

    for count, instance in enumerate(instances, start=1):
        mock_get_cloud.return_value = cloud
        mock_launch_instance.return_value = instance
        params = Mock(env_type='environment-server')
        launch(params)

        assert mock_launch_instance.call_count == count
        assert mock_boot.call_count == count
        assert cloud.create_dns_entries_from_tag.call_count == count
        assert cloud.configure_instance.call_count == count
