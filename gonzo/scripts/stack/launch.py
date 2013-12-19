#!/usr/bin/env python
""" Launch stacks
"""
import curses
from functools import partial
from time import sleep

from gonzo.backends import launch_stack
from gonzo.exceptions import DataError
from gonzo.scripts.utils import colorize
from gonzo.utils import csv_dict, abort


def wait_for_stack_complete(window, stack):
    curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    n = 0
    interval = 1
    while not stack.is_complete:
        window.clear()

        window.addstr("Creating Stack ", curses.color_pair(1))
        window.addstr("{}... {}s\n".format(stack.name, n))
        window.addstr("{}\n\n".format(stack.id))

        window.addstr("Resources\n", curses.color_pair(1))
        sort_key = lambda k: k.logical_resource_id
        for resource in sorted(stack.resources, key=sort_key):
            window.addstr("\t{}\t{}\t{}\n".format(
                resource.physical_resource_id,
                resource.logical_resource_id,
                resource.resource_status))

        window.refresh()
        sleep(interval)
        n += interval


def launch(args):
    """ Launch stacks """

    stack = launch_stack(args.stack_name, args.template, args.template_params)
    curses.wrapper(wait_for_stack_complete, stack)

    colorize_ = partial(colorize, use_color=args.color)
    print colorize_('Created Stack', 'yellow'), stack.name
    print "{}\n".format(stack.id)

    if stack.outputs:
        print colorize_('Outputs', 'yellow')
        for output in stack.outputs:
            print "\t{}: {}".format(output.key, output.value)
            if output.description:
                print "\t\t{}".format(output.description)


def main(args):
    try:
        launch(args)
    except DataError as ex:
        abort(ex.message)


stack_name_help = """
Non-unique name to be appended with an incrementing number and then
used as a stack identifier."""


template_help = """
File or URL containing a template to be passed to the selected
cloud provider's orchestration service, such as cloud-formation.
Templates will be parsed as a Jinja2 template and may be supplemented
with parameters."""


def init_parser(parser):
    parser.add_argument(
        'stack_name', help=stack_name_help)
    parser.add_argument(
        '--template', dest='template',
        help=template_help)
    parser.add_argument(
        '--template-params', dest='template_params',
        metavar='key=val[,key=val..]', type=csv_dict,
        help='Additional parameters to be used when rendering templates.')
    parser.add_argument(
        '--color', dest='color', nargs='?', default='auto',
        choices=['never', 'auto', 'always'],
        help='display coloured output. (default: auto)')