#!/usr/bin/env python
""" List instances
"""

from functools import partial

from libcloud.compute.types import NodeState

from gonzo.scripts.utils import colorize, print_table, format_uptime
from gonzo.clouds import get_current_cloud


headers = [
    "name",
    "type",
    "status",
    "owner",
    "uptime",
    "location",
]


def print_instance_summary(instance, use_color='auto'):
    """ Print summary info line for the supplied instance """

    colorize_ = partial(colorize, use_color=use_color)

    name = colorize_(instance.name, "yellow")
    instance_type = instance.extra['gonzo_size']

    if instance.state == NodeState.RUNNING:
        status_colour = "green"
    else:
        status_colour = "red"

    instance_status = NodeState.tostring(instance.state)
    status = colorize_(instance_status, status_colour)

    if 'owner' in instance.extra['gonzo_tags']:
        owner = instance.extra['gonzo_tags']['owner']
    else:
        owner = "---"

    uptime = format_uptime(instance.extra['gonzo_created_time'])
    uptime = colorize_(uptime, "blue")

    availability_zone = instance.extra['gonzo_az']

    result_list = [
        name,
        instance_type,
        status,
        owner,
        uptime,
        availability_zone,
    ]
    return result_list


def list_(args):
    """ Print summary info for all running instances, or all instances
        in any state (e.g. terminated) if args.only_running == True

    """

    # Get Config.py
    cloud = get_current_cloud()

    instances = cloud.list_instances(name_filter=args.name_filter)

    print_table(print_instance_summary, headers, instances,
                use_color=args.color)


def main(args):
    list_(args)


def init_parser(parser):
    parser.add_argument(
        '--filter', dest='name_filter', nargs='?', default=None,
        help='filter instance names')
    parser.add_argument(
        '--order', dest='order', nargs='?', default='name',
        choices=['name', 'age'], help='set instance order (default: name)')
    parser.add_argument(
        '--all', dest='only_running', action='store_false', default=True,
        help='include terminating instances')
    parser.add_argument(
        '--color', dest='color', nargs='?', default='auto',
        choices=['never', 'auto', 'always'],
        help='display coloured output (default: auto)')
