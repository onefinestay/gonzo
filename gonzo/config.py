from ConfigParser import ConfigParser, NoSectionError, NoOptionError
import imp
import os
import subprocess

from gonzo.exceptions import ConfigurationError

PROJECT_ROOT = '/srv'
GONZO_HOME = os.path.join(os.path.expanduser("~"), '.gonzo/')
STATE_FILE = os.path.join(GONZO_HOME, '.state')


def get_config_module(gonzo_home=GONZO_HOME):
    """ returns the global configuration module """
    if not os.path.exists(gonzo_home):
        os.mkdir(gonzo_home)

    try:
        fp, pathname, description = imp.find_module('config', [gonzo_home])
    except ImportError:
        raise ConfigurationError(
            "gonzo config does not exist. Please see README")

    config_module = imp.load_module('config', fp, pathname, description)
    return config_module


class StateDict(object):
    """ methods common to global and local state dicts """
    def get(self, key, default=None):
        try:
            return self[key]
        except ConfigurationError:
            return default

    def _raise(self, key):
        raise ConfigurationError('{} not specified'.format(key))


class GlobalState(StateDict):
    """ global state, kept in state_file, defaulting to
        ~/.gonzo/.state """

    def __init__(self, state_file):
        self.state_file = state_file

    def __getitem__(self, key):
        state = ConfigParser()
        state.read(self.state_file)
        try:
            return state.get('gonzo', key)
        except (NoSectionError, NoOptionError):
            self._raise(key)

    def __setitem__(self, key, value):
        state = ConfigParser()
        state.read(self.state_file)
        if not state.has_section('gonzo'):
            state.add_section('gonzo')
        state.set('gonzo', key, value)

        with open(self.state_file, 'wb') as state_file:
            state.write(state_file)


class LocalState(StateDict):
    """ local state, kept in local git config """
    git_args = ['git', 'config', '--local']

    def __getitem__(self, key):
        git_key = 'gonzo.{}'.format(key)
        try:
            output = subprocess.check_output(self.git_args + [git_key])
            value = output.strip()
        except subprocess.CalledProcessError:
            self._raise(key)

        return value

    def __setitem__(self, key, value):
        git_key = 'gonzo.{}'.format(key)
        try:
            subprocess.check_output(self.git_args + [git_key, value])
        except subprocess.CalledProcessError:
            self._raise(key)


class ConfigProxy(object):
    """ Proxy that can be imported without causing `get_config` to be
        imported at import time
    """

    ###
    # Compltete list, user provided

    @property
    def CLOUDS(self):
        """ returns a configuration dict """
        config_module = get_config_module()
        try:
            return config_module.CLOUDS
        except AttributeError as ex:
            raise ConfigurationError(ex)

    @property
    def SIZES(self):
        """ returns the host group instance size map """
        config_module = get_config_module()
        try:
            return config_module.SIZES
        except AttributeError as ex:
            raise ConfigurationError(ex)

    ###
    # Subset of the above, depending on current state

    @property
    def CLOUD(self):
        cloud = global_state['cloud']
        clouds = self.CLOUDS
        try:
            return clouds[cloud]
        except KeyError:
            raise ConfigurationError('Invalid cloud: {}'.format(cloud))

    @property
    def REGION(self):
        return global_state['region']

    @property
    def DNS(self):
        cloud = self.CLOUD
        dns_service_name = cloud.get('DNS_SERVICE', 'dummy')
        return dns_service_name

    def get_cloud_config_value(self, config_key, override=None):
        if override is None:
            return self.CLOUD.get(config_key)
        return override

    def get_namespaced_cloud_config_value(self,
                                          config_key, namespace,
                                          override=None):
        """ Fetch a value from config nested in a namespaced dictionary.
        Override is returned first, then namespace lookup, then 'default'
        value.
        """
        if override is not None:
            return override

        # No override supplied, so check config.
        namespaced_dict = self.CLOUD[config_key]
        if not namespaced_dict:
            return None

        default_value = namespaced_dict.get('default')
        return namespaced_dict.get(namespace, default_value)


config_proxy = ConfigProxy()
global_state = GlobalState(STATE_FILE)
local_state = LocalState()
