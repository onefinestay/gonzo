from functools import wraps
import imp
import os
from ConfigParser import NoSectionError, NoOptionError

import git

from gonzo.exceptions import ConfigurationError

PROJECT_ROOT = '/srv'


def get_config_module():
    """ returns the global configuration module """

    gonzo_home = os.path.join(os.path.expanduser("~"), '.gonzo/')
    gonzo_conf = 'config'

    if not os.path.exists(gonzo_home):
        os.mkdir(gonzo_home)

    try:
        fp, pathname, description = imp.find_module(gonzo_conf, [gonzo_home])
    except ImportError:
        raise ConfigurationError(
            "gonzo config does not exist. Please see README")

    config_module = imp.load_module(gonzo_conf, fp, pathname, description)
    return config_module


def get_clouds():
    """ returns a configuration dict """
    config_module = get_config_module()
    return config_module.CLOUDS


def get_sizes():
    """ returns the host group instance size map """
    config_module = get_config_module()
    return config_module.SIZES


def get_option(key, default=None):
    cwd = os.getcwd()

    repo = git.Repo(cwd)
    config_reader = repo.config_reader()
    try:
        return config_reader.get_value('gonzo', key, default)
    except (NoSectionError, NoOptionError):
        return None


def set_option(key, value, config_level='global'):
    cwd = os.getcwd()

    repo = git.Repo(cwd)
    config_writer = repo.config_writer(config_level=config_level)
    config_writer.set_value('gonzo', key, value)


def get_cloud():
    cloud = get_option('cloud')
    clouds = get_clouds()
    try:
        return clouds[cloud]
    except KeyError:
        raise ConfigurationError('Invalid cloud: {}'.format(cloud))


def lazy(func):
    @wraps(func)
    def wrapper(self):
        if not hasattr(func, 'value'):
            func.value = func(self)
        return func.value
    return wrapper


class ConfigProxy(object):
    """ Proxy that can be imported without causing `get_config` to be
        imported at import time
    """

    @property
    @lazy
    def CLOUD(self):
        return get_cloud()

    @property
    @lazy
    def REGION(self):
        return get_option('region')

    @property
    @lazy
    def SIZES(self):
        return get_sizes()


config_proxy = ConfigProxy()
