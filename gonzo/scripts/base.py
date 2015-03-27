import argparse
import logging

import argcomplete

import gonzo
from gonzo.exceptions import ConfigurationError
from gonzo.scripts import config
from gonzo.scripts import launch as launch
from gonzo.scripts import list_


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--version', action='version',
        version='%(prog)s {}'.format(gonzo.VERSION))
    parser.add_argument(
        '--log-level', action='store', help="Log level",
        default=logging.INFO)

    subparsers = parser.add_subparsers(help='subcommand help')

    for module in [config, list_, launch]:

        module_name = module.__name__.replace(
            '%s.' % gonzo.scripts.__name__, '')
        module_alias = module_name.strip('_').replace('.', '-')

        module_parser = subparsers.add_parser(
            module_alias, description=module.__doc__)
        module.init_parser(module_parser)
        module_parser.set_defaults(main=module.main)
    return parser


def main():
    parser = get_parser()

    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    logging.basicConfig(level=args.log_level)

    try:
        args.main(args)
    except ConfigurationError as ex:
        print "Configuration error: {}".format(ex)

if __name__ == '__main__':
    main()
