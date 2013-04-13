import pytest
from mock import patch, call

from gonzo.scripts.config import set_cloud
from gonzo.exceptions import ConfigurationError
from gonzo.test_utils import assert_has_calls


@patch('gonzo.scripts.config.global_state')
@patch('gonzo.scripts.config.config_proxy')
class TestSetCloud(object):
    def test_noop(self, config_proxy, global_state):
        set_cloud(None)
        assert global_state.__getitem__.call_count == 0

    def test_set(self, config_proxy, global_state):
        config_proxy.CLOUD = {
            'REGIONS': ['region1', 'region2'],
        }
        state = {
            'cloud': 'foo',
        }
        global_state.__getitem__ = state.__getitem__
        set_cloud('foo')

        calls = [
            call('cloud', 'foo'),
            call('region', 'region1'),
        ]
        assert_has_calls(global_state.__setitem__, calls)

    def test_set_no_regions(self, config_proxy, global_state):
        config_proxy.CLOUD = {}
        state = {
            'cloud': 'foo',
        }
        global_state.__getitem__ = state.__getitem__
        with pytest.raises(ConfigurationError):
            set_cloud('foo')

    def test_set_empty_regions(self, config_proxy, global_state):
        config_proxy.CLOUD = {
            'REGIONS': [],
        }
        state = {
            'cloud': 'foo',
        }
        global_state.__getitem__ = state.__getitem__
        with pytest.raises(ConfigurationError):
            set_cloud('foo')

    def test_set_regions_not_iterable(self, config_proxy, global_state):
        pytest.skip("TODO: catch TypeErrors. Move to tests for gonzo.config?")
        config_proxy.CLOUD = {
            'REGIONS': 0,
        }
        state = {
            'cloud': 'foo',
        }
        global_state.__getitem__ = state.__getitem__
        with pytest.raises(ConfigurationError):
            set_cloud('foo')


class TestAvailableRegions(object):
    pass
