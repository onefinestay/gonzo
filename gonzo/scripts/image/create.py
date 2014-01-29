#!/usr/bin/env python
""" Create instance images
"""
from gonzo.exceptions import CommandError
from gonzo.backends import get_current_cloud


def image_create(args):
    """ Create an image for a given instance, identified by name
    """

    cloud = get_current_cloud()
    instance = cloud.get_instance_by_name(args.instance_name)
    cloud.create_image(instance, args.image_name)


def main(args):
    try:
        image_create(args)
    except CommandError as ex:
        print ex
        print


def init_parser(parser):
    parser.add_argument(
        'instance_name',
        help="Name of the instance for which to capture an image")
    parser.add_argument(
        'image_name', help="Name for the resulting image")
