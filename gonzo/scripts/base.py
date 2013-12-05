import argparse

import argcomplete

import gonzo
from gonzo.exceptions import ConfigurationError
from gonzo.scripts import config, launch, launch_stack, list_, terminate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--version', action='version',
        version='%(prog)s {}'.format(gonzo.VERSION))
    subparsers = parser.add_subparsers(help='subcommand help')

    for module in [config, launch, launch_stack, list_, terminate]:
        module_name = module.__name__.rsplit('.', 1)[-1]
        module_alias = module_name.strip('_')
        module_parser = subparsers.add_parser(
            module_alias, description=module.__doc__)

        module.init_parser(module_parser)
        module_parser.set_defaults(main=module.main)

    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    try:
        args.main(args)
    except ConfigurationError as ex:
        print "Configuration error: {}".format(ex)

if __name__ == '__main__':
    main()
