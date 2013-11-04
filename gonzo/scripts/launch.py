#!/usr/bin/env python
""" Launch instances
"""

from functools import partial
import os
import sys
from time import sleep

from gonzo.backends.base import launch_instance, configure_instance
from gonzo.exceptions import CommandError
from gonzo.scripts.utils import colorize


def wait_for_instance_boot(instance, use_color='auto'):
    colorize_ = partial(colorize, use_color=use_color)
    stdout = sys.stdout

    print colorize_('Created instance', 'yellow'), instance.id
    n = 0
    sleep(1)
    while not instance.is_running():
        stdout.write("\r{}... {}s".format(instance.update(), n))
        stdout.flush()
        n += 1
        sleep(1)
    stdout.write("\r{} after {}s\n".format(instance.update(), n))
    stdout.flush()


def launch(args):
    """ Launch instances """

    username = os.environ.get('USER')
    instance = launch_instance(args.env_type, user_data=args.user_data,
                               user_data_params=args.user_data_params,
                               username=username)
    wait_for_instance_boot(instance, args.color)
    configure_instance(instance)
    print "Created instance {}".format(instance.name)


def main(args):
    try:
        launch(args)
    except CommandError as ex:
        print ex
        print


env_type_pair_help = """
e.g. production-platform-app, which is interpreted as
    environment: production, server_type: ecommerce-web"""


def init_parser(parser):
    parser.add_argument(
        'env_type', metavar='environment-server_type', help=env_type_pair_help)
    parser.add_argument(
        '--size', dest='size',  # choices=config.CLOUD['SIZES'],
        help="Override instance size")
    parser.add_argument(
        '--user-data', dest='user_data',
        help="File or URL containing user-data to be passed to new instances "
             "and run by cloud-init. Can utilize parameters. See "
             "template/userdata_template.")
    parser.add_argument(
        '--user-data-params', dest='user_data_params',
        metavar='key=val[,key=val..]',
        help='Additional parameters to be used when rendering user data.')
    parser.add_argument(
        '--availability-zone', dest='az',
        help="Override availability zone. (defaults to balancing)")
    parser.add_argument(
        '--color', dest='color', nargs='?', default='auto',
        choices=['never', 'auto', 'always'],
        help='display coloured output. (default: auto)')
