#!/usr/bin/env python
""" List stacks
"""

import json
from boto.exception import BotoServerError

from gonzo.backends import generate_stack_template, get_current_cloud
from gonzo.exceptions import CommandError
from gonzo.utils import csv_dict, abort


def template(args):
    """ Print the template of a given stack or, if no stack is found, print
    the template that would be generated when launching.

    """

    cloud = get_current_cloud()
    stack_name = args.stack_name_or_id

    try:
        template_ = cloud.orchestration_connection.get_template(stack_name)
        template_ = json.dumps(template_, sort_keys=True,
                               indent=4, separators=(',', ': '))
    except BotoServerError:
        # Stack doesn't exist. Generate a new template.
        stack_type = stack_name
        template_ = generate_stack_template(
            stack_type, stack_name, args.template_uri, args.template_params)

    print template_


def main(args):
    try:
        template(args)
    except CommandError as ex:
        abort(ex.message)


template_help = """
File or URL containing a template to be passed to the selected
cloud provider's orchestration service, such as cloud-formation.
Templates will be parsed as a Jinja2 template and may be supplemented
with parameters."""

template_uri_option_args = ('--template-uri',)
template_uri_option_kwargs = {'dest': 'template_uri', 'help': template_help}

template_params_option_args = ('--template-params',)
template_params_option_kwargs = {
    'dest': 'template_params',
    'metavar': 'key=val[,key=val..]',
    'type': csv_dict,
    'help': 'Additional parameters to be used when rendering templates.',
}


def init_parser(parser):
    parser.add_argument('stack_name_or_id')
    parser.add_argument(*template_uri_option_args,
                        **template_uri_option_kwargs)
    parser.add_argument(*template_params_option_args,
                        **template_params_option_kwargs)
    parser.add_argument(
        '--color', dest='color', nargs='?', default='auto',
        choices=['never', 'auto', 'always'],
        help='display coloured output (default: auto)')
