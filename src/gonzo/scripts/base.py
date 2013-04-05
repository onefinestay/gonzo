import argparse

import argcomplete

from gonzo.scripts import config, launch, list_, terminate


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='subcommand help')

    for module in [config, launch, list_, terminate]:
        module_name = module.__name__.rsplit('.', 1)[-1]
        module_alias = module_name.strip('_')
        module_parser = subparsers.add_parser(
            module_alias, description=module.__doc__)

        module.init_parser(module_parser)
        module_parser.set_defaults(main=module.main)

    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    args.main(args)

if __name__ == '__main__':
    main()
