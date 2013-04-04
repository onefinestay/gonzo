#!/usr/bin/env python
""" Set the account and region for subsequent gonzo commands
"""


import os
from ConfigParser import NoSectionError

import git

from gonzo.settings import CONFIG


class CommandError(Exception):
    pass


def get_git_config(key, default=None):
    cwd = os.getcwd()

    repo = git.Repo(cwd)
    config_reader = repo.config_reader()
    try:
        return config_reader.get_value('gonzo', key, default)
    except NoSectionError:
        return None


def set_git_config(key, value):
    cwd = os.getcwd()

    repo = git.Repo(cwd)
    config_writer = repo.config_writer()
    config_writer.set_value('gonzo', key, value)


def get_mode_config():
    mode = get_git_config('mode')
    try:
        return CONFIG[mode]
    except KeyError:
        raise CommandError('Invalid mode: {}'.format(mode))


def set_mode(mode):
    if not mode:
        return

    set_git_config('mode', mode)

    # set the default region
    mode_config = get_mode_config()
    supported_regions = mode_config['REGIONS']

    try:
        default_region = supported_regions[0]
        set_region(default_region)
    except IndexError:
        raise CommandError('Mode "{}" has no supported regions'.format(mode))


def set_region(region):
    if not region:
        return

    mode = get_git_config('mode')

    mode_config = get_mode_config()
    supported_regions = mode_config['REGIONS']

    if region not in supported_regions:
        raise CommandError(
            'Region "{}" not supported for mode "{}"'.format(region, mode))

    set_git_config('region', region)


def print_config():
    print 'mode:', get_git_config('mode')
    print 'region:', get_git_config('region')


def main(args):
    try:
        set_mode(args.mode)
        set_region(args.region)
    except CommandError as e:
        print e
        print

    print_config()


def init_parser(parser):
    parser.add_argument(
        '--mode', dest='mode', metavar='MODE', nargs='?',
        choices=CONFIG.keys(), help='set the mode')
    parser.add_argument(
        '--region', dest='region', metavar='REGION', nargs='?',
        help='set the region')

