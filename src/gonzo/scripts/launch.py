#!/usr/bin/env python
""" Launch instances
"""

import os

from gonzo.aws.route53 import Route53
from gonzo.backends import get_current_cloud
from gonzo.config import config_proxy as config
from gonzo.exceptions import CommandError


def get_next_hostname(env_type):
    """ Calculate the next hostname for a given environment, server_type
        returns the full hostname, including the counter, e.g.
        production-ecommerce-web-013
    """
    record_name = "-".join(["_count", env_type])
    next_count = 1
    r53 = Route53()
    try:
        count_value = r53.get_values_by_name(record_name)[0]
        next_count = int(count_value.replace('\"', '')) + 1
        r53.update_record(record_name, "TXT", "%s" % next_count)
    except:  # TODO: specify
        r53.add_remove_record(record_name, "TXT", "%s" % next_count)
    name = "%s-%03d" % (env_type, next_count)
    return name


def find_or_create_security_groups(environment):
    cloud = get_current_cloud()
    if not cloud.security_group_exists(environment):
        cloud.create_security_group(environment)

    return ['gonzo', environment]


def launch(args):
    """ Launch instances

    """

    cloud = get_current_cloud()
    environment, server_type = args.env_type.split("-", 1)

    name = get_next_hostname(args.env_type)
    print "Name: %s" % name

    image_name = config.CLOUD['AMI_NAME']

    sizes = config.SIZES
    default_size = sizes['default']
    instance_type = sizes.get(environment, default_size)

    zone = cloud.next_az(server_type)

    find_or_create_security_groups('gonzo')
    security_groups = find_or_create_security_groups(environment)

    key_name = config.CLOUD['KEY_NAME']

    tags = {
        'environment': environment,
        'server_type': server_type,
    }

    if 'USER' in os.environ:
        tags['owner'] = os.environ['USER']

    instance = cloud.launch(
        name, image_name, instance_type, zone, security_groups, key_name,
        tags)

    print instance


def main(args):
    try:
        launch(args)
    except CommandError as ex:
        print ex
        print


env_type_pair_help = """
e.g. produiction-platform-app, which is interpreted as
    environment: production, server_type: ecommerce-web"""


def init_parser(parser):
    parser.add_argument(
        'env_type', metavar='environment-server_type', help=env_type_pair_help)
    parser.add_argument(
        '--size', dest='size',  # choices=config.CLOUD['SIZES'],
        help="Override instance size")
    parser.add_argument(
        '--availability-zone', dest='az',
        help="Override availability zone. (defaults to balancing)")
