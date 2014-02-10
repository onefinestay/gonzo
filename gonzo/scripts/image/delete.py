#!/usr/bin/env python
""" Delete instance images
"""
from gonzo.exceptions import MultipleResourcesError, NoSuchResourceError
from gonzo.backends import get_current_cloud
from gonzo.utils import abort


def image_delete(args):
    """ Delete an image for a given instance, identified by name
    """

    cloud = get_current_cloud()
    image = cloud.get_image_by_name(args.image_name)

    if image is not None:
        image.delete()


def main(args):
    try:
        image_delete(args)
    except NoSuchResourceError as ex:
        print ex.message
    except MultipleResourcesError as ex:
        abort(ex.message)


def init_parser(parser):
    parser.add_argument(
        'image_name', help="Name of image to delete")
