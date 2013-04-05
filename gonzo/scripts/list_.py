#!/usr/bin/env python
""" List instances
"""

from datetime import datetime

from prettytable import PrettyTable

from gonzo.exceptions import CommandError
from gonzo.backends import get_current_cloud


def _print_table(headers, output_list, show_header=False):
    tableoutput = PrettyTable(headers)
    for column in headers:
        tableoutput.align[column] = "l"

    tableoutput.header = show_header
    tableoutput.sortby = "name"
    tableoutput.vertical_char = " "
    tableoutput.horizontal_char = " "

    tableoutput.junction_char = " "
    for tableresult in output_list:
        tableoutput.add_row(tableresult)

    return tableoutput


def colorize(msg, colour):
    colour_map = {
        'red': '\x1b[31m',
        'yellow': '\x1b[33m',
        'green': '\x1b[32m',
        'blue': '\x1b[34m',
    }

    reset = "\x1b[0m"
    colour = colour_map[colour]

    return "%s%s%s" % (colour, msg, reset)


def print_instance(instance):
    """ Print summary info line for the supplied instance """

    name = colorize(instance.name, "yellow")
    instance_type = instance.instance_type

    instancecolour = "red"
    if instance.is_running():
        instancecolour = "green"

    status = colorize(instance.status, instancecolour)
    owner = instance.tags.get("owner", "--")

    start_time = instance.launch_time
    try:
        delta = datetime.now() - start_time
        days = delta.days
        hours = delta.seconds / 3600
        minutes = (delta.seconds % 3600) / 60
        seconds = (delta.seconds % 3600) % 60
        uptime = "%dd %dh %dm %ds" % (days, hours, minutes, seconds)
    except TypeError:
        uptime = 'n/a'

    uptime = colorize(uptime, "blue")
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

    tablelist = [
        "name",
        "type",
        "location",
        "status",
        "owner",
        "uptime",
        "group_name_list",
    ]
    table_output = []
    for instance in instances:
        table_output.append(print_instance(instance))

    print _print_table(tablelist, table_output)


def main(args):
    try:
        list_(args)
    except CommandError as ex:
        print ex
        print


def init_parser(parser):
    parser.add_argument(
        '--order', dest='order', metavar='ORDER', nargs='?', default='name',
        choices=['name', 'age'], help='list all instances')
    parser.add_argument(
        '--all', dest='only_running', action='store_false', default=True,
        help='include terminating instances')
