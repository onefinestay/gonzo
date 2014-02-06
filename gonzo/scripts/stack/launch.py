#!/usr/bin/env python
""" Launch stacks
"""
import curses
from functools import partial
from time import sleep
import os

from gonzo.backends import launch_stack
from gonzo.exceptions import DataError
from gonzo.scripts.stack.template import (template_uri_option_kwargs,
                                          template_uri_option_args,
                                          template_params_option_args,
                                          template_params_option_kwargs)
from gonzo.scripts.stack.show import print_stack
from gonzo.scripts.utils import colorize
from gonzo.utils import abort


def wait_for_stack_complete(stack):
    curses.wrapper(print_stack_until_complete, stack)


def print_stack_until_complete(window, stack):
    yellow_on_black = 1  # Curses colour pair id for this window
    curses.init_pair(yellow_on_black, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    n = 0
    interval = 1
    while not stack.is_complete:
        window.clear()

        window.addstr("Creating Stack ", curses.color_pair(yellow_on_black))
        window.addstr("""{}... {}s
{}

""".format(stack.name, n, stack.id))

        window.addstr("Resources\n", curses.color_pair(yellow_on_black))
        sort_key = lambda k: k.logical_resource_id
        for resource in sorted(stack.resources, key=sort_key):
            window.addstr("\t{}\t{}\t{}\n".format(
                resource.physical_resource_id,
                resource.logical_resource_id,
                resource.resource_status))

        window.refresh()
        sleep(interval)
        n += interval


def print_output(output):
    print "\t{}: {}".format(output.key, output.value)
    if output.description:
        print "\t\t{}".format(output.description)


def launch(args):
    """ Launch stacks """

    username = os.environ.get('USER')

    stack = launch_stack(args.stack_name, args.template_uri,
                         args.template_params, owner=username)
    wait_for_stack_complete(stack)

    for instance in stack.get_instances():
        instance.create_dns_entries_from_tag(args.dns_tag)

    colorize_ = partial(colorize, use_color=args.color)
    print_stack(stack, colorize_)


def main(args):
    try:
        launch(args)
    except DataError as ex:
        abort(ex.message)


stack_name_help = """
Non-unique name to be appended with an incrementing number and then
used as a stack identifier."""

dns_help = """
If Route53 is configured and instances are launched with a matching tag, the
tag value is parsed as a comma separated list of DNS records to create. DNS
records are suffixed with the current cloud's DNS_ZONE config.
(Default: cnames)"""


def init_parser(parser):
    parser.add_argument(
        'stack_name', help=stack_name_help)
    parser.add_argument(*template_uri_option_args,
                        **template_uri_option_kwargs)
    parser.add_argument(*template_params_option_args,
                        **template_params_option_kwargs)
    parser.add_argument(
        '--dns-tag', dest='dns_tag', default='cnames',
        help=dns_help)
    parser.add_argument(
        '--color', dest='color', nargs='?', default='auto',
        choices=['never', 'auto', 'always'],
        help='display coloured output. (default: auto)')
