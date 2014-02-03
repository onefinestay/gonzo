#!/usr/bin/env python
""" Terminate instances
"""

from gonzo.exceptions import CommandError
from gonzo.utils import abort


def terminate(args):
    print "Terminating", args  # TODO: add terminate


def main(args):
    try:
        terminate(args)
    except CommandError as ex:
        abort(ex.message)


def init_parser(parser):
    parser.add_argument('instance_name', help="Terminate an instance")
