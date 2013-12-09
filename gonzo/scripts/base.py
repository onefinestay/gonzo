import argparse

import argcomplete

import gonzo
from gonzo.exceptions import ConfigurationError
from gonzo.scripts import config
from gonzo.scripts.stack import launch as stack_launch
from gonzo.scripts.instance import launch as instance_launch
from gonzo.scripts.instance import list_ as instance_list
from gonzo.scripts.instance import terminate as instance_terminate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--version', action='version',
        version='%(prog)s {}'.format(gonzo.VERSION))
    subparsers = parser.add_subparsers(help='subcommand help')

    for module in [config,
                   instance_launch, instance_list, instance_terminate,
                   stack_launch]:

        module_name = module.__name__.replace(
            '%s.' % gonzo.scripts.__name__, '')
        module_alias = module_name.strip('_').replace('.', '-')

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
