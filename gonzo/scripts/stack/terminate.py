#!/usr/bin/env python
""" Terminate stacks
"""
import curses
from functools import partial
from time import sleep

from gonzo.exceptions import NoSuchResourceError
from gonzo.scripts.utils import colorize
from gonzo.backends import get_current_cloud


def show_delete_progress(stack):
    try:
        curses.wrapper(wait_until_stack_deleted, stack)
    except NoSuchResourceError:
        # We expect there to be no such resource once the stack has been
        # completely deleted
        pass


def wait_until_stack_deleted(window, stack):
    red_on_black = 1  # Curses colour pair id for this window
    curses.init_pair(red_on_black, curses.COLOR_RED, curses.COLOR_BLACK)
    n = 0
    interval = 1
    while not stack.is_complete:
        window.clear()

        window.addstr("Deleting Stack ", curses.color_pair(red_on_black))
        window.addstr("""{}... {}s
{}

""".format(stack.name, n, stack.id))

        window.addstr("Resources\n", curses.color_pair(red_on_black))
        sort_key = lambda k: k.logical_resource_id
        for resource in sorted(stack.resources, key=sort_key):
            window.addstr("\t{}\t{}\t{}\n".format(
                resource.physical_resource_id,
                resource.logical_resource_id,
                resource.resource_status))

        window.refresh()
        sleep(interval)
        n += interval


def terminate(args):
    """ Launch stacks """

    cloud = get_current_cloud()
    stack = cloud.get_stack(args.stack_name)
    stack_name = stack.name  # Get the name before it's deleted

    for instance in stack.get_instances():
        cloud.delete_dns_entries(instance)

    stack.delete()
    show_delete_progress(stack)

    colorize_ = partial(colorize, use_color=args.color)
    print colorize_('Deleted Stack', 'red'), stack_name


def main(args):
    terminate(args)


def init_parser(parser):
    parser.add_argument(
        'stack_name')
    parser.add_argument(
        '--color', dest='color', nargs='?', default='auto',
        choices=['never', 'auto', 'always'],
        help='display coloured output. (default: auto)')
