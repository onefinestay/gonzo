#!/usr/bin/env python
""" Launch instances
"""

from functools import partial
import os
import sys
from time import sleep

from gonzo.backends import launch_instance, configure_instance
from gonzo.exceptions import CommandError, DataError
from gonzo.scripts.utils import colorize
from gonzo.utils import abort, csv_dict, csv_list


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

    instance = launch_instance(args.env_type,
                               security_groups=args.security_groups,
                               size=args.size,
                               user_data_uri=args.user_data_uri,
                               user_data_params=args.user_data_params,
                               print_user_data=args.print_user_data,
                               owner=username)
    wait_for_instance_boot(instance, args.color)
    configure_instance(instance)
    print "Created instance {}".format(instance.name)


def main(args):
    try:
        launch(args)
    except CommandError as ex:
        abort(ex.message)
    except DataError as ex:
        abort(ex.message)


env_type_pair_help = """
e.g. production-platform-app, which is interpreted as
    environment: production, server_type: ecommerce-web"""

additional_security_group_help = """
Specify additional security groups to create (if
necessary) and assign. Server type and gonzo security
groups will be automatically defined."""

user_data_help = """
File or URL containing user-data to be passed to new
instances and run by cloud-init. Can utilize parameters.
See template/userdata_template."""


def init_parser(parser):
    parser.add_argument(
        'env_type', metavar='environment-server_type', help=env_type_pair_help)
    parser.add_argument(
        '--size', dest='size',  # choices=config.CLOUD['SIZES'],
        help="Override instance size")
    parser.add_argument(
        '--user-data-uri', dest='user_data_uri',
        help=user_data_help)
    parser.add_argument(
        '--user-data-params', dest='user_data_params',
        metavar='key=val[,key=val..]', type=csv_dict,
        help='Additional parameters to be used when rendering user data.')
    parser.add_argument(
        '--print-user-data', dest='print_user_data', default=False,
        action='store_true',
        help='Print the rendered user data script')
    parser.add_argument(
        '--availability-zone', dest='az',
        help="Override availability zone. (defaults to balancing)")
    parser.add_argument(
        '--additional-security-groups', dest='security_groups',
        metavar='sg-name[,sg-name]', type=csv_list,
        help=additional_security_group_help)
    parser.add_argument(
        '--color', dest='color', nargs='?', default='auto',
        choices=['never', 'auto', 'always'],
        help='display coloured output. (default: auto)')
