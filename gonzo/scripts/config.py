#!/usr/bin/env python
""" Set the account and region for subsequent gonzo commands
"""

from __future__ import print_function

from gonzo.config import local_state, global_state, config_proxy
from gonzo.exceptions import ConfigurationError


def set_cloud(cloud):
    if not cloud:
        return

    global_state['cloud'] = cloud

    # set the default region
    cloud_config = config_proxy.get_cloud()
    try:
        supported_regions = cloud_config['REGIONS']
    except KeyError:
        raise ConfigurationError(
            'Cloud "{}" has no REGIONS setting'.format(cloud))

    try:
        default_region = supported_regions[0]
        set_region(default_region)
    except (TypeError, IndexError):
        raise ConfigurationError(
            'Cloud "{}" has no supported regions'.format(cloud))


def available_clouds():
    """ list of regions configured for the current cloud
        for argparse suggestions """
    try:
        clouds = config_proxy.CLOUDS
        return clouds.keys()
    except (ConfigurationError, AttributeError):
        return None  # so argparse shows metavar, not empty list


def available_regions():
    """ list of configured clouds for argparse suggestions """
    try:
        cloud_config = config_proxy.get_cloud()
        return cloud_config['REGIONS']
    except (ConfigurationError, KeyError):
        return None  # so argparse shows metavar, not empty list


def set_region(region):
    if not region:
        return

    global_state['region'] = region


def set_project(project):
    """ Sets the project name for the local git repository. This will not write
        to the global / system git environments.
    """

    if not project:
        return

    local_state['project'] = project


def print_config():
    print('cloud: {}'.format(global_state.get('cloud')))
    print('region: {}'.format(global_state.get('region')))
    print('project: {}'.format(local_state.get('project')))


def main(args):
    try:
        set_cloud(args.cloud)
        set_region(args.region)
        set_project(args.project)
    except ConfigurationError as ex:
        print(ex)
        print()

    print_config()


def init_parser(parser):
    parser.add_argument(
        '--cloud', dest='cloud', choices=available_clouds(),
        help='set the active cloud configuration'
    )
    parser.add_argument(
        '--region', dest='region',
        choices=available_regions(), help='set the region'
    )
    parser.add_argument(
        '--project', dest='project',
        help='set the project name to the local git config'
    )
