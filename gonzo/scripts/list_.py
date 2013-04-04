#!/usr/bin/env python
""" List instances
"""

from gonzo.exceptions import CommandError


def list_(args):
    print "a list of instances"
    return


def main(args):
    try:
        list_(args)
    except CommandError as e:
        print e
        print


def init_parser(parser):
    parser.add_argument(
        '--order', dest='order', metavar='ORDER', nargs='?', default='name',
        choices=['name', 'age'], help='list all instances')
    parser.add_argument(
        '--all', dest='only_running', action='store_false', default=True,
        help='include terminating instances')
