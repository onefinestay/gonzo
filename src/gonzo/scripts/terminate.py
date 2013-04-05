#!/usr/bin/env python
""" Terminate instances
"""

from gonzo.exceptions import CommandError


def terminate(args):
    # TODO
    print "Terminating", args



def main(args):
    try:
        terminate(args)
    except CommandError as ex:
        print ex
        print


def init_parser(parser):
    parser.add_argument(
        'instance_name', help="Terminate an instance")
