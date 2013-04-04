import argparse

from gonzo.scripts import config, list_


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='subcommand help')

    for module in [config, list_]:
        module_name = module.__name__.rsplit('.', 1)[-1]
        module_alias = module_name.strip('_')
        module_parser = subparsers.add_parser(
            module_alias, description=module.__doc__)

        module.init_parser(module_parser)
        module_parser.set_defaults(main=module.main)

    args = parser.parse_args()

    args.main(args)

if __name__ == '__main__':
    main()
