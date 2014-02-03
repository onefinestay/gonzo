#!/usr/bin/env python
""" List stacks
"""

from functools import partial

from gonzo.backends import get_current_cloud
from gonzo.scripts.utils import colorize, print_table, format_uptime, ellipsize


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

    description = ellipsize(stack.description, 75)

    status_colour = "green" if stack.is_complete else "red"
    status = colorize_(stack.status, status_colour)

    #owner = stack.tags.get("owner", "--")

    uptime = format_uptime(stack.launch_time)
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
    list_(args)


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
