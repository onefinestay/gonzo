import pytest
from mock import Mock, patch

from gonzo.scripts.config import set_cloud, get_cloud, available_regions
from gonzo.exceptions import CommandError, ConfigurationError


@patch('gonzo.scripts.config.set_region')
@patch('gonzo.scripts.config.get_cloud')
@patch('gonzo.config.set_option')
def test_set_cloud(set_option, get_cloud, set_region):
    get_cloud.return_value = {'REGIONS': ['supported01', 'supported02', 'supported03']}

    assert set_cloud('') == None
    set_cloud('some-cloud-service')
    # this isn't quite right... don't want to have to call str
    assert 'supported01' in str(set_region.call_args_list[0])


@patch('gonzo.scripts.config.set_region')
@patch('gonzo.scripts.config.get_cloud')
@patch('gonzo.config.set_option')
def test_set_cloud_raises(set_option, get_cloud, set_region):
    get_cloud.return_value = {'REGIONS': []}

    with pytest.raises(CommandError):
        set_cloud('some-cloud-service') == 'supported01'


@patch('gonzo.scripts.config.get_cloud')
def test_available_regions(get_cloud):
    regions = [1, 2, 3, 4]
    get_cloud.return_value = {'REGIONS': regions}

    assert available_regions() == regions
