#!/usr/bin/env python
""" List stacks
"""

from datetime import datetime
from functools import partial

from gonzo.exceptions import CommandError
from gonzo.backends import get_current_cloud
from gonzo.scripts.utils import colorize, print_table


headers = [
    "name",
    "description",
    "status",
    #"owner", # TODO: support ownership of stacks
    "uptime",
]


def print_stack_summary(stack, use_color='auto'):
    """ Print summary info line for the supplied instance """

    colorize_ = partial(colorize, use_color=use_color)

    name = colorize_(stack.name, "yellow")

    description = stack.description
    description = (description[:75] + '..') if len(description) > 75\
        else description

    stack_color = "red"
    if stack.is_complete:
        stack_color = "green"
    status = colorize_(stack.status, stack_color)

    #owner = stack.tags.get("owner", "--")

    start_time = stack.launch_time
    try:
        delta = datetime.now() - start_time
        days = delta.days
        hours = delta.seconds / 3600
        minutes = (delta.seconds % 3600) / 60
        seconds = (delta.seconds % 3600) % 60
        uptime = "%dd %dh %dm %ds" % (days, hours, minutes, seconds)
    except TypeError:
        uptime = 'n/a'

    uptime = colorize_(uptime, "blue")

    result_list = [
        name,
        description,
        status,
        #owner,
        uptime,
    ]
    return result_list


def list_(args):
    """ Print summary info for all running stacks, or all stacks
        in any state (e.g. terminated) if args.only_running == True

    """

    cloud = get_current_cloud()
    stacks = cloud.list_stacks(only_running=args.only_running)

    print_table(print_stack_summary, headers, stacks, use_color=args.color)


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
