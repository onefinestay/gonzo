import os
import os
import imp
from ConfigParser import NoSectionError

import git

from gonzo.exceptions import ConfigurationError


def get_global_config():
    """ returns a configuration dict """
    gonzo_home = os.path.join(os.path.expanduser("~"), '.gonzo/')
    gonzo_conf = 'config'

    if not os.path.exists(gonzo_home):
        os.mkdir(gonzo_home)

    try:
        fp, pathname, description = imp.find_module(gonzo_conf, [gonzo_home])
    except ImportError:
        raise ConfigurationError("gonzo config does not exist. Please see README")

    config_module =  imp.load_module(gonzo_conf, fp, pathname, description)

    return config_module.CONFIG


def get_option(key, default=None):
    cwd = os.getcwd()

    repo = git.Repo(cwd)
    config_reader = repo.config_reader()
    try:
        return config_reader.get_value('gonzo', key, default)
    except NoSectionError:
        return None


def set_option(key, value):
    cwd = os.getcwd()

    repo = git.Repo(cwd)
    config_writer = repo.config_writer()
    config_writer.set_value('gonzo', key, value)


def get_config():
    mode = get_option('mode')
    config = get_global_config()
    try:
        return config[mode]
    except KeyError:
        raise ConfigurationError('Invalid mode: {}'.format(mode))

