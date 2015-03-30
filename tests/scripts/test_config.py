import argparse
import pytest
from mock import patch, call, sentinel, Mock, PropertyMock

from gonzo.scripts.config import (set_cloud, available_regions,
                                  available_clouds, set_region, set_project,
                                  print_config, main, init_parser)
from gonzo.exceptions import ConfigurationError
from gonzo.test_utils import assert_has_calls, assert_called_once_with


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
        config_proxy.CLOUD = {
            'REGIONS': 0,
        }
        state = {
            'cloud': 'foo',
        }
        global_state.__getitem__ = state.__getitem__
        with pytest.raises(ConfigurationError):
            set_cloud('foo')


@patch('gonzo.config.ConfigProxy.CLOUDS', new_callable=PropertyMock)
class TestAvailableClouds(object):
    def test_ok(self, clouds):
        clouds.return_value = {
            'foo': {},
            'bar': {},
        }
        assert available_clouds() == ['foo', 'bar']

    def test_missing(self, clouds):
        clouds.side_effect = ConfigurationError()
        assert available_clouds() is None

    def test_non_dict(self, clouds):
        clouds.return_value = "str"
        assert available_clouds() is None


@patch('gonzo.scripts.config.config_proxy')
class TestAvailableRegions(object):
    def test_ok(self, config_proxy):
        config_proxy.CLOUD = {
            'REGIONS': sentinel.regions,
        }
        assert available_regions() == sentinel.regions

    def test_missing(self, config_proxy):
        config_proxy.CLOUD = {}
        assert available_regions() is None


@patch('gonzo.scripts.config.global_state')
class TestSetRegion(object):
    def test_noop(self, global_state):
        set_region(None)
        assert global_state.__setitem__.call_count == 0

    def test_set(self, global_state):
        set_region('foo')
        assert_called_once_with(global_state.__setitem__, 'region', 'foo')


@patch('gonzo.scripts.config.local_state')
class TestSetProject(object):
    def test_noop(self, local_state):
        set_project(None)
        assert local_state.__setitem__.call_count == 0

    def test_set(self, local_state):
        set_project('foo')
        assert_called_once_with(local_state.__setitem__, 'project', 'foo')


@patch('gonzo.scripts.config.print', create=True)
@patch('gonzo.scripts.config.global_state')
@patch('gonzo.scripts.config.local_state')
def test_print_config(local_state, global_state, print_):
    local_state.get.return_value = 'bar'
    data = ['foo', None]
    global_state.get = lambda x: data.pop(0)
    print_config()
    calls = [
        call('cloud: foo'),
        call('region: None'),
        call('project: bar'),
    ]
    assert_has_calls(print_, calls)


@patch('gonzo.scripts.config.set_cloud')
@patch('gonzo.scripts.config.set_region')
@patch('gonzo.scripts.config.set_project')
class TestMain():
    def test_ok(self, project, region, cloud):
        args = Mock()
        main(args)

    def test_error(self, project, region, cloud):
        project.side_effect = ConfigurationError()
        args = Mock()
        main(args)


def test_parser():
    # just make sure it parses ok
    parser = argparse.ArgumentParser()
    init_parser(parser)
