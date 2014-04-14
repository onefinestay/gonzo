from contextlib import contextmanager
from StringIO import StringIO
import subprocess
import types

import pytest
from mock import ANY, Mock, patch, sentinel

from gonzo.exceptions import ConfigurationError
from gonzo.config import (
    get_config_module, StateDict, GlobalState, LocalState,
    ConfigProxy)
from gonzo.test_utils import assert_called_once_with


@patch('gonzo.config.imp')
@patch('gonzo.config.os')
class TestGetConfigModule(object):
    def test_get_config_module(self, os, imp):
        os.path.exists.return_value = True
        imp.find_module.return_value = Mock(), Mock(), Mock()
        imp.load_module.return_value = sentinel.config

        assert get_config_module() is sentinel.config

    def test_missing_home(self, os, imp):
        os.path.exists.return_value = False
        imp.find_module.return_value = Mock(), Mock(), Mock()
        get_config_module()
        assert_called_once_with(os.mkdir, ANY)

    def test_import_error(self, os, imp):
        imp.find_module.side_effect = ImportError()
        with pytest.raises(ConfigurationError):
            get_config_module()


class TestStateDict(object):
    def test_get(self):
        class MockStateDict(StateDict):
            def __getitem__(self, key):
                if key == "spam":
                    return "ham"
                else:
                    raise ConfigurationError()

        state = MockStateDict()
        assert state.get("spam") == "ham"
        assert state.get("eggs") is None
        assert state.get("eggs", "eggs") == "eggs"

    def test_raise(self):
        state = StateDict()
        with pytest.raises(ConfigurationError) as ex:
            state._raise("foo")
        assert "foo" in str(ex)


@contextmanager
def patch_open():
    with patch('gonzo.config.open', create=True) as open_manager:
        with patch('ConfigParser.open', create=True) as open_:

            file_ = StringIO()

            def reset(*args, **kwargs):
                file_.seek(0)

            open_.return_value.readline = file_.readline
            open_.return_value.close = reset
            open_manager.return_value.__enter__.return_value = file_
            open_manager.return_value.__exit__.side_effect = reset

            yield file_


class TestGlobalState(object):
    def test_get_set(self):
        with patch_open():
            state = GlobalState('path/to/file')
            state['foo'] = 'bar'
            assert state['foo'] == 'bar'

    def test_overwrite(self):
        with patch_open():
            state = GlobalState('path/to/file')
            state['foo'] = 'bar'
            state['foo'] = 'baz'
            assert state['foo'] == 'baz'

    def test_get_missing_section(self):
        with patch_open():
            state = GlobalState('path/to/file')
            with pytest.raises(ConfigurationError):
                state['foo']

    def test_get_missing_key(self):
        with patch_open() as file_:
            file_.write('[gonzo]')
            file_.seek(0)
            state = GlobalState('path/to/file')
            with pytest.raises(ConfigurationError):
                state['foo']


class TestLocalState(object):
    @patch('gonzo.config.subprocess.check_output')
    def test_get(self, check_output):
        state = LocalState()
        state.git_args = ['cmd']

        check_output.return_value = ""
        state['foo'] = 'bar'
        assert_called_once_with(check_output, ['cmd', 'gonzo.foo', 'bar'])

    @patch('gonzo.config.subprocess.check_output')
    def test_set(self, check_output):
        state = LocalState()
        state.git_args = ['cmd']

        check_output.return_value = "bar"
        assert state['foo'] == 'bar'
        assert_called_once_with(check_output, ['cmd', 'gonzo.foo'])

    @patch('gonzo.config.subprocess.check_output')
    def test_get_error(self, check_output):
        state = LocalState()

        check_output.side_effect = subprocess.CalledProcessError(0, "")
        with pytest.raises(ConfigurationError):
            state['foo']

    @patch('gonzo.config.subprocess.check_output')
    def test_set_error(self, check_output):
        state = LocalState()

        check_output.side_effect = subprocess.CalledProcessError(0, "")
        with pytest.raises(ConfigurationError):
            state['foo'] = 'bar'


class TestConfigProxy(object):
    @patch('gonzo.config.get_config_module')
    def test_clouds(self, config_module):
        config_proxy = ConfigProxy()
        config_module.return_value.CLOUDS = sentinel.clouds
        assert config_proxy.CLOUDS is sentinel.clouds

    @patch('gonzo.config.get_config_module')
    def test_clouds_missing(self, config_module):
        config_proxy = ConfigProxy()
        config_module.return_value = types.ModuleType(name='config')
        with pytest.raises(ConfigurationError):
            config_proxy.CLOUD

    @patch('gonzo.config.get_config_module')
    def test_sizes(self, config_module):
        config_proxy = ConfigProxy()
        config_module.return_value.SIZES = sentinel.sizes
        assert config_proxy.SIZES is sentinel.sizes

    @patch('gonzo.config.get_config_module')
    def test_sizes_missing(self, config_module):
        config_proxy = ConfigProxy()
        config_module.return_value = types.ModuleType(name='config')
        with pytest.raises(ConfigurationError):
            config_proxy.SIZES

    @patch('gonzo.config.global_state', {'cloud': 'foo'})
    @patch('gonzo.config.get_config_module')
    def test_cloud(self, config_module):
        config_proxy = ConfigProxy()
        config_module.return_value.CLOUDS = {
            'foo': sentinel.foo,
            'bar': sentinel.bar,
        }
        assert config_proxy.CLOUD is sentinel.foo

    @patch('gonzo.config.global_state', {'cloud': 'foo'})
    @patch('gonzo.config.get_config_module')
    def test_cloud_missing(self, config_module):
        config_proxy = ConfigProxy()
        config_module.return_value.CLOUDS = {
        }
        with pytest.raises(ConfigurationError):
            config_proxy.CLOUD

    @patch('gonzo.config.global_state', {'region': sentinel.region})
    def test_region(self):
        config_proxy = ConfigProxy()
        assert config_proxy.REGION is sentinel.region
