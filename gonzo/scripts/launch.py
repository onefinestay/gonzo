#!/usr/bin/env python
""" Launch instances
"""

from functools import partial
import logging
import os
import sys
from time import sleep

from gonzo.helpers.document_loader import get_parsed_document
from gonzo.clouds import get_current_cloud
from gonzo.clouds.dns import DNS
from gonzo.config import config_proxy
from gonzo.exceptions import DataError
from gonzo.scripts.utils import colorize
from gonzo.utils import abort, csv_dict, csv_list


logger = logging.getLogger(__name__)


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
    cloud_config = config_proxy.get_cloud(args.cloud)
    cloud = get_current_cloud(args.cloud)

    # Instantiate DNS
    dns = DNS(cloud_config['AWS_ACCESS_KEY_ID'],
              cloud_config['AWS_SECRET_ACCESS_KEY'])

    # Server Type
    server_type = ("-").join(args.env_type.split("-")[-2:])

    # Instance Full Name
    zone_name = cloud_config['DNS_ZONE']

    full_instance_name = dns.get_next_host(
        args.env_type,
        zone_name
    )

    # Owner
    username = os.environ.get('USER')

    # Instance Size
    if args.size is None:
        sizes = config_proxy.SIZES
        default_size = sizes['default']
        size = sizes.get(server_type, default_size)
    else:
        size = args.size

    # Security Group List
    if args.security_groups is None:
        security_groups = [server_type, 'gonzo']
    else:
        security_groups = args.security_groups

    # Instance Base Image
    if args.image_id is None:
        image_id = cloud_config['IMAGE_ID']
    else:
        image_id = args.image_id

    # User Data
    if args.user_data_params is None:
        user_data_params = cloud_config.get('USER_DATA_PARAMS')
    else:
        user_data_params = args.user_data_params

    if not args.user_data_uri:
        user_data_uri = cloud_config.get('DEFAULT_USER_DATA')
        if user_data_uri is None:
            user_data = {}
        else:
            user_data = get_parsed_document(
                full_instance_name, user_data_uri,
                'USER_DATA_PARAMS', user_data_params
            )

    # Launch Instance
    instance = cloud.create_instance(
        name=full_instance_name,
        size=size,
        user_data=user_data,
        image_name=image_id,
        security_groups=security_groups,
        owner=username,
        key_name=cloud_config.get('PUBLIC_KEY_NAME'),
        volume_size=args.volume_size
    )

    print "Instance created: {}.{}".format(
        instance.name,
        cloud_config['DNS_ZONE']
    )

    dns.create_dns_record(instance.name,
                          instance.extra['gonzo_network_address'],
                          cloud_config['DNS_TYPE'],
                          cloud_config['DNS_ZONE'])


def main(args):
    try:
        launch(args)
    except DataError as ex:
        abort(ex.message)


env_type_pair_help = """
e.g. production-platform-app, which is interpreted as
    environment: production, server_type: ecommerce-web"""

additional_security_group_help = """
Specify additional security groups to create (if
necessary) and assign. Server type and gonzo security
groups will be automatically defined."""

additional_tags_help = """
Specify additional tags to assign (if necessary). server_type, environment and
owner will be automatically defined."""

user_data_help = """
File or URL containing user-data to be passed to new
instances and run by cloud-init. Can utilize parameters.
See template/userdata_template."""

dns_help = """
If Route53 is configured and instances are launched with a matching tag, the
tag value is parsed as a comma separated list of DNS records to create. DNS
records are suffixed with the current cloud's DNS_ZONE config.
(Default: cnames)"""


def init_parser(parser):
    parser.add_argument(
        '--volume-size', dest="volume_size")
    parser.add_argument(
        'env_type', metavar='environment-server_type', help=env_type_pair_help)
    parser.add_argument(
        '--image-id', dest='image_id',
        help="ID of image to boot from")
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
        '--availability-zone', dest='az',
        help="Override availability zone. (defaults to balancing)")
    parser.add_argument(
        '--additional-security-groups', dest='security_groups',
        metavar='sg-name[,sg-name]', type=csv_list,
        help=additional_security_group_help)
    parser.add_argument(
        '--extra-tags', dest='extra_tags',
        metavar='key=val[,key=val..]', type=csv_dict,
        help=additional_tags_help)
    parser.add_argument(
        '--dns-tag', dest='dns_tag', default='cnames',
        help=dns_help)
    parser.add_argument(
        '--color', dest='color', nargs='?', default='auto',
        choices=['never', 'auto', 'always'],
        help='display coloured output. (default: auto)')
