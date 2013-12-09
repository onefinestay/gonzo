import datetime

from mock import Mock, patch

from gonzo.scripts.instance.list_ import print_instance


@patch('gonzo.scripts.list_.colorize')
def test_print_instance(colorize):
    colorize.return_value = 'fancy-cloud'

    # as name is an argument in the Mock constructor
    # we have to set it on an instance
    group1 = Mock()
    group1.name = 'group1'
    group2 = Mock()
    group2.name = 'group2'
    groups = [group1, group2]

    instance = Mock(
        name='cloud',
        instance_type='fancy',
        status='happy',
        tags={'owner': 'ofs'},
        launch_time=datetime.datetime(2000, 01, 01),
        groups=groups,
        availability_zone='cloud-zone'
    )

    expected = [
        'fancy-cloud',
        'fancy',
        'fancy-cloud',
        'ofs',
        'fancy-cloud',
        'group1,group2',
        'cloud-zone',
    ]
    result = print_instance(instance)

    assert result == expected
