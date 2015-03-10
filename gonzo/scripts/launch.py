#!/usr/bin/env python
""" Launch instances
"""

from functools import partial
import logging
import os
import sys
from time import sleep

#from gonzo.backends import launch_instance, configure_instance
from gonzo.helpers.document_loader import get_parsed_document
from gonzo.clouds.compute import Cloud
from gonzo.clouds.dns import DNS
from gonzo.config import config_proxy
from gonzo.exceptions import DataError
from gonzo.scripts.utils import colorize
from gonzo.utils import abort, csv_dict, csv_list


logger = logging.getLogger(__name__)


def get_next_host(dns, server_name, zone_name):
    count_record = "_count-{}".format(server_name)
    record = dns.get_dns_record(count_record, zone_name)
    if record:
        next_count = int(record.data.strip('"')) + 1
        dns.update_dns_record(
            record=record,
            value='"{}"'.format(next_count),
        )
    else:
#       ipdb.set_trace()
        next_count = 1
        dns.create_dns_record(
            name=count_record,
            value='"{}"'.format(next_count),
            record_type="TXT",
            zone_name=zone_name
        )
    return "%s-%03d" % (server_name, next_count)


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

    # Instantiate Cloud Backend
    cloud_config = config_proxy.CLOUD
    region = config_proxy.REGION
    cloud = Cloud.from_config(cloud_config, region)

    # Instantiate DNS
    #ipdb.set_trace()
    dns = DNS(cloud_config['AWS_ACCESS_KEY_ID'],
              cloud_config['AWS_SECRET_ACCESS_KEY'])

    # Server Type
    server_type = ("-").join(args.env_type.split("-")[-2:])
    #ipdb.set_trace()

    # Instance Full Name
    zone_name = cloud_config['DNS_ZONE']

    full_instance_name = get_next_host(dns, args.env_type,
                                       zone_name)

    print full_instance_name
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
        user_data_params = cloud_config['USER_DATA_PARAMS']
    else:
        user_data_params = args.user_data_params

    if not args.user_data_uri:
        user_data_uri = cloud_config['DEFAULT_USER_DATA']
        user_data = get_parsed_document(full_instance_name, user_data_uri,
                                        'USER_DATA_PARAMS', user_data_params)

    # Launch Instance
    instance = cloud.create_instance(
        name=full_instance_name,
        size=size,
        user_data=user_data,
        image_name=image_id,
        security_groups=security_groups,
        owner=username,
        key_name=cloud_config['PUBLIC_KEY_NAME'],
    )
    print instance
    #ipdb.set_trace()

    dns.create_dns_record(instance.name,
                          instance.extra['gonzo_network_address'],
                          cloud_config['DNS_TYPE'],
                          cloud_config['DNS_ZONE'])
    #instance.create_dns_entries_from_tag(args.dns_tag)
    #wait_for_instance_boot(instance, args.color)
    #print "Created instance {}".format(instance.name)


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
        'env_type', metavar='environment-server_type', help=env_type_pair_help)
    parser.add_argument(
        '--image-name', dest='image_id',
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
