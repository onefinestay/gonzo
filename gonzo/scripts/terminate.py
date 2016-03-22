#!/usr/bin/env python
""" Terminate instances
"""


def terminate(args):
    print("Terminating", args)  # TODO: add terminate


def main(args):
    terminate(args)


def init_parser(parser):
    parser.add_argument('instance_name', help="Terminate an instance")
