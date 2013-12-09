#!/usr/bin/env python
""" List stacks
"""

from functools import partial

from prettytable import PrettyTable

from gonzo.exceptions import CommandError
from gonzo.backends import get_current_cloud
from gonzo.scripts.utils import colorize


def build_resources_table(stack, colorize_):
    headers = [
        "name",
        "id",
        "type",
        "status",
    ]

    table = PrettyTable(headers)
    for column in headers:
        table.align[column] = "l"
    table.header = False
    table.sortby = "name"
    table.vertical_char = " "
    table.horizontal_char = " "
    table.junction_char = " "

    for resource in stack.resources:

        resource_color = 'red'
        if resource.resource_status == stack.running_state:
            resource_color = 'green'

        table.add_row([
            colorize_(resource.logical_resource_id, 'yellow'),
            resource.physical_resource_id,
            resource.resource_type,
            colorize_(resource.resource_status, resource_color),
        ])

    return table


def build_outputs_table(stack, colorize_):
    headers = [
        "key",
        "value",
        "description"
    ]

    table = PrettyTable(headers)
    for column in headers:
        table.align[column] = "l"
    table.header = False
    table.sortby = "key"
    table.vertical_char = " "
    table.horizontal_char = " "
    table.junction_char = " "

    for output in stack.outputs:
        table.add_row([
            colorize_(output.key, 'yellow'),
            colorize_(output.value, 'green'),
            output.description,
        ])

    return table


def show(args):
    """ Print summary info for all running stacks, or all stacks
        in any state (e.g. terminated) if args.only_running == True

    """
    colorize_ = partial(colorize, use_color=args.color)

    cloud = get_current_cloud()
    stack = cloud.get_stack(args.stack_name_or_id)

    # Title
    print
    print colorize_('Stack Name', 'yellow'), stack.name
    print colorize_('Stack Id', 'yellow'), stack.id
    print

    # Resources
    print colorize_('Resources', 'yellow')
    print build_resources_table(stack, colorize_)

    # Outputs
    if stack.outputs:
        print colorize_('Outputs', 'yellow')
        print build_outputs_table(stack, colorize_)


def main(args):
    try:
        show(args)
    except CommandError as ex:
        print ex
        print


def init_parser(parser):
    parser.add_argument('stack_name_or_id')
    parser.add_argument(
        '--color', dest='color', nargs='?', default='auto',
        choices=['never', 'auto', 'always'],
        help='display coloured output (default: auto)')
