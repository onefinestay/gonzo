#!/usr/bin/env python
""" Set the account and region for subsequent gonzo commands
"""

from gonzo.config import get_option, set_option, get_cloud, get_clouds
from gonzo.exceptions import CommandError


def set_cloud(cloud):
    if not cloud:
        return

    set_option('cloud', cloud)

    # set the default region
    cloud_config = get_cloud()
    supported_regions = cloud_config['REGIONS']

    try:
        default_region = supported_regions[0]
        set_region(default_region)
    except IndexError:
        raise CommandError('Cloud "{}" has no supported regions'.format(cloud))


def available_regions():
    cloud_config = get_cloud()
    return cloud_config['REGIONS']


def set_region(region):
    if not region:
        return

    set_option('region', region)


def print_config():
    print 'cloud:', get_option('cloud')
    print 'region:', get_option('region')


def main(args):
    try:
        set_cloud(args.cloud)
        set_region(args.region)
    except CommandError as ex:
        print ex
        print

    print_config()


def init_parser(parser):
    parser.add_argument(
        '--cloud', dest='cloud', metavar='CLOUD', choices=get_clouds().keys(),
        help='set the active cloud configuration'
    )
    parser.add_argument(
        '--region', dest='region', metavar='REGION',
        choices=available_regions(), help='set the region'
    )
