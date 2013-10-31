#!/usr/bin/env python
""" Launch instances
"""

from functools import partial
import os
import sys
from time import sleep
from urllib2 import urlopen, URLError

from gonzo.backends.base import launch_instance, configure_instance
from gonzo.config import config_proxy as config
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


def get_user_data(uri):
    """ Attempt to fetch user data from URL or file. Failing that, assume raw
     user data has been passed """
    if uri is None:
        return None

    if os.path.isfile(uri):
        print os.path.expanduser(uri)
        return file(os.path.expanduser(uri), 'r').read()
    else:
        try:
            return urlopen(uri).read()
        except:
            return uri


def parse_user_data_params(user_data_params=None):
    if user_data_params is None:
        return {}

    return dict(kv.split("=") for kv in user_data_params.split(","))


def launch(args):
    """ Launch instances """

    username = os.environ.get('USER')

    # If user data hasn't been passed by argument, check for default in config.
    user_data_uri = args.user_data
    if user_data_uri is None and 'DEFAULT_USER_DATA' in config.CLOUD:
        user_data_uri = config.CLOUD['DEFAULT_USER_DATA']
    # Attempt to read user data from url or file
    user_data = get_user_data(user_data_uri)
    user_data_params = parse_user_data_params(args.user_data_params)

    raise Exception("UserData: %s" % user_data)

    instance = launch_instance(args.env_type, user_data=user_data,
                               user_data_params=user_data_params,
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
        help="File, URL or explicit contents of user-data to be passed to new "
             "instance and run by cloud-init. Can utilize parameters. See "
             "template/userdata_template.")
    parser.add_argument(
        '--user-data-params', dest='user_data_params',
        metavar='key=val[,key=val..]',
        help='Additional parameters to use when rendering user data.')
    parser.add_argument(
        '--availability-zone', dest='az',
        help="Override availability zone. (defaults to balancing)")
    parser.add_argument(
        '--color', dest='color', nargs='?', default='auto',
        choices=['never', 'auto', 'always'],
        help='display coloured output. (default: auto)')
