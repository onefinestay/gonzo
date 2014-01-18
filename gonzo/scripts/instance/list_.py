#!/usr/bin/env python
""" List instances
"""

from functools import partial

from gonzo.exceptions import CommandError
from gonzo.backends import get_current_cloud
from gonzo.scripts.utils import colorize, print_table, format_uptime


headers = [
    "name",
    "type",
    "location",
    "status",
    "owner",
    "uptime",
    "group_name_list",
]


def print_instance_summary(instance, use_color='auto'):
    """ Print summary info line for the supplied instance """

    colorize_ = partial(colorize, use_color=use_color)

    name = colorize_(instance.name, "yellow")

    instance_type = instance.instance_type

    status_colour = "green" if instance.is_running() else "red"
    status = colorize_(instance.status, status_colour)

    owner = instance.tags.get("owner", "--")

    uptime = format_uptime(instance.launch_time)
    uptime = colorize_(uptime, "blue")

    group_list = [group.name for group in instance.groups]
    group_list.sort()
    group_name_list = ",".join(group_list)

    availability_zone = instance.availability_zone

    result_list = [
        name,
        instance_type,
        status,
        owner,
        uptime,
        group_name_list,
        availability_zone,
    ]
    return result_list


def list_(args):
    """ Print summary info for all running instances, or all instances
        in any state (e.g. terminated) if args.only_running == True

    """

    cloud = get_current_cloud()
    instances = cloud.list_instances(only_running=args.only_running)

    if args.order == 'name':
        instances.sort(key=lambda i: i.tags.get(args.order))

    print_table(print_instance_summary, headers, instances,
                use_color=args.color)


def main(args):
    try:
        list_(args)
    except CommandError as ex:
        print ex
        print


def init_parser(parser):
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
