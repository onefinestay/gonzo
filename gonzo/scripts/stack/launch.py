#!/usr/bin/env python
""" Launch stacks
"""
import curses
from functools import partial
from time import sleep
import sys

from gonzo.backends import launch_stack
from gonzo.exceptions import DataError, UnhealthyResourceError
from gonzo.scripts.stack.template import (template_uri_option_kwargs,
                                          template_uri_option_args,
                                          template_params_option_args,
                                          template_params_option_kwargs)
from gonzo.scripts.stack.show import print_stack
from gonzo.scripts.utils import colorize
from gonzo.utils import abort


POLLING_INTERVAL = 5  # seconds


def wait_for_stack_complete(stack, quiet):
    if quiet:
        while not stack.is_complete:
            sleep(POLLING_INTERVAL)
    else:
        curses.wrapper(print_stack_until_complete, stack)


def print_stack_until_complete(window, stack):
    yellow_on_black = 1  # Curses colour pair id for this window
    curses.init_pair(yellow_on_black, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    n = 0
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
        sleep(POLLING_INTERVAL)
        n += POLLING_INTERVAL


def print_output(output):
    print "\t{}: {}".format(output.key, output.value)
    if output.description:
        print "\t\t{}".format(output.description)


def launch(args):
    """ Launch stacks """

    stack = launch_stack(args.stack_name, args.template_uri,
                         args.template_params)
    wait_for_stack_complete(stack, args.quiet)
    if not stack.is_healthy:
        raise UnhealthyResourceError("Stack was not healthy upon completion.")

    if args.create_images:
        # Create or update images for the stack
        for image in stack.create_or_update_images():
            sys.stdout.write("Waiting on image creation: %s" % image.name)
            sys.stdout.flush()
            while not image.is_complete:
                sys.stdout.write(".")
                sys.stdout.flush()
                sleep(POLLING_INTERVAL)
            print

    if not args.quiet:
        colorize_ = partial(colorize, use_color=args.color)
        print_stack(stack, colorize_)

    if args.delete_after_complete:
        stack.delete()
    else:
        # Create instance dns from tag
        for instance in stack.get_instances():
            instance.create_dns_entries_from_tag(args.dns_tag)


def main(args):
    try:
        launch(args)
    except DataError as ex:
        abort(ex.message)
    except UnhealthyResourceError as ex:
        abort(ex.message)


stack_name_help = """
Non-unique name to be appended with an incrementing number and then
used as a stack identifier."""

dns_help = """
If Route53 is configured and instances are launched with a matching tag, the
tag value is parsed as a comma separated list of DNS records to create. DNS
records are suffixed with the current cloud's DNS_ZONE config.
(Default: cnames)"""

create_images_help = """
Capture instance images upon completion of the stack. Image names will be
follow the format of <non-unique-stack-name>-<resource-logical-id>.
e.g. full-stack-instance-ecommerce."""

delete_after_complete_help = """
This option will trigger the launched stack's deletion immediately after it has
completed. This has usages, for example, in refreshing instance images or
launching stacks to complete a one time task."""


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
        '--create-images', dest='create_images', default=False,
        action='store_true', help=create_images_help)
    parser.add_argument(
        '--quiet', dest='quiet', default=False, action='store_true',
        help="Only display erroneous output.")
    parser.add_argument(
        '--delete-after-complete', dest='delete_after_complete',
        default=False, action='store_true',
        help=delete_after_complete_help)
    parser.add_argument(
        '--color', dest='color', nargs='?', default='auto',
        choices=['never', 'auto', 'always'],
        help='display coloured output. (default: auto)')
