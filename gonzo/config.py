from functools import wraps
import imp
import os
from ConfigParser import NoSectionError, NoOptionError

import git

from gonzo.exceptions import ConfigurationError

PROJECT_ROOT = '/srv'
DEFAULT_HOME = os.path.join(os.path.expanduser("~"), '.gonzo/')


def get_config_module(gonzo_home=DEFAULT_HOME):
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


def get_clouds():
    """ returns a configuration dict """
    config_module = get_config_module()
    return config_module.CLOUDS


def get_sizes():
    """ returns the host group instance size map """
    config_module = get_config_module()
    return config_module.SIZES


def get_reader():
    """ returns a git config reader """
    cwd = os.getcwd()

    try:
        reader = git.Repo(cwd).config_reader()
    except git.exc.InvalidGitRepositoryError:
        # we're not in a git directory so check the global config
        user_config = os.path.normpath(os.path.expanduser("~/.gitconfig"))
        reader = git.config.GitConfigParser([user_config], read_only=True)

    return reader


def get_option(key, default=None):
    reader = get_reader()
    try:
        return reader.get_value('gonzo', key, default)
    except (NoSectionError, NoOptionError):
        return None


def get_writer(config_level):
    """ returns a git config writer """
    cwd = os.getcwd()

    try:
        writer = git.Repo(cwd).config_writer(config_level=config_level)
    except git.exc.InvalidGitRepositoryError:
        # we're not in a git directory so check the global config
        if config_level == 'repository':
            raise Exception(
                'Tried to write local config outside a git repository: '
                '{}'.format(cwd))
        else:
            user_config = os.path.normpath(os.path.expanduser("~/.gitconfig"))
            writer = git.config.GitConfigParser(user_config, read_only=False)

    return writer


def set_option(key, value, config_level='global'):
    writer = get_writer(config_level)
    writer.set_value('gonzo', key, value)


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
