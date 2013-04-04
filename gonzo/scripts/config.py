#!/usr/bin/env python
""" Set the account and region for subsequent gonzo commands
"""


from gonzo.config import get_option, set_option, get_config, get_global_config
from gonzo.exceptions import CommandError


def set_mode(mode):
    if not mode:
        return

    set_option('mode', mode)

    # set the default region
    mode_config = get_config()
    supported_regions = mode_config['REGIONS']

    try:
        default_region = supported_regions[0]
        set_region(default_region)
    except IndexError:
        raise CommandError('Mode "{}" has no supported regions'.format(mode))


def set_region(region):
    if not region:
        return

    mode = get_option('mode')

    mode_config = get_config()
    supported_regions = mode_config['REGIONS']

    if region not in supported_regions:
        raise CommandError(
            'Region "{}" not supported for mode "{}"'.format(region, mode))

    set_option('region', region)


def print_config():
    print 'mode:', get_option('mode')
    print 'region:', get_option('region')


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
        choices=get_global_config().keys(), help='set the mode')
    parser.add_argument(
        '--region', dest='region', metavar='REGION', nargs='?',
        help='set the region')

