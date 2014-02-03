#!/usr/bin/env python
""" Delete instance images
"""
from gonzo.exceptions import CommandError
from gonzo.backends import get_current_cloud


def image_delete(args):
    """ Delete an image for a given instance, identified by name
    """

    cloud = get_current_cloud()
    cloud.delete_image_by_name(args.image_name)


def main(args):
    try:
        image_delete(args)
    except CommandError as ex:
        print ex
        print


def init_parser(parser):
    parser.add_argument(
        'image_name', help="Name of image to delete")
