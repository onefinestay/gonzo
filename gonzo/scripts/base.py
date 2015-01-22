import argparse
import logging

import argcomplete

import gonzo
from gonzo.exceptions import ConfigurationError
from gonzo.scripts import config

# from gonzo.scripts.image import create as image_create
# from gonzo.scripts.image import delete as image_delete

from gonzo.scripts import launch as launch
from gonzo.scripts import list_
# from gonzo.scripts.instance import terminate as instance_terminate

# from gonzo.scripts.stack import launch as stack_launch
# from gonzo.scripts.stack import list_ as stack_list
# from gonzo.scripts.stack import show as stack_show
# from gonzo.scripts.stack import template as stack_template
# from gonzo.scripts.stack import terminate as stack_terminate


def main():
    #import ipdb ; ipdb.set_trace()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--version', action='version',
        version='%(prog)s {}'.format(gonzo.VERSION))
    parser.add_argument(
        '--log-level', action='store', help="Log level",
        default=logging.DEBUG)

    subparsers = parser.add_subparsers(help='subcommand help')

    for module in [config, list_, launch]:

        module_name = module.__name__.replace(
            '%s.' % gonzo.scripts.__name__, '')
        module_alias = module_name.strip('_').replace('.', '-')

        module_parser = subparsers.add_parser(
            module_alias, description=module.__doc__)
        module.init_parser(module_parser)
        module_parser.set_defaults(main=module.main)

    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    logging.basicConfig(level=args.log_level)

    try:
        args.main(args)
    except ConfigurationError as ex:
        print "Configuration error: {}".format(ex)

if __name__ == '__main__':
    main()
