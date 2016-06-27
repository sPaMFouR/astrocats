"""
"""


def main():
    from datetime import datetime

    from . import Catalog

    beg_time = datetime.now()
    # Process command-line arguments to determine action
    #    If no subcommand (e.g. 'impoter') is given, returns 'None' --> exit
    args = load_args()
    if args is None:
        return

    catalog = Catalog.Catalog(args)
    git_vers = get_git()
    title_str = "Open Supernova Catalog, version: {}".format(git_vers)
    catalog.log.warning("\n\n{}\n{}\n{}\n".format(
        title_str, '=' * len(title_str), beg_time.ctime()))

    # Choose which submodule to run (note: can also use `set_default` with
    # function)
    if args._name == 'importer':
        from . import importer
        catalog.log.info("Running `importer`.")
        importer.importer.import_main(catalog)

    end_time = datetime.now()
    catalog.log.warning("All complete at {}, After {}".format(
        end_time, end_time - beg_time))
    return


def load_args(args=None):
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate a catalog JSON file and plot HTML files from SNE data.')
    # parser.add_argument('--foo', action='store_true', help='foo help')
    subparsers = parser.add_subparsers(description='valid subcommands', dest='_name',
                                       help='sub-command help')

    # Build a 'parent' parser whose settings are inhereted by children parsers
    pars_parent = argparse.ArgumentParser(add_help=False)
    pars_parent.add_argument('--verbose', '-v', dest='verbose', default=False, action='store_true',
                             help='Print more messages to the screen.')
    pars_parent.add_argument('--debug', '-d', dest='debug', default=False, action='store_true',
                             help='Print excessive messages to the screen.')
    pars_parent.add_argument('--travis', '-t',  dest='travis',  default=False, action='store_true',
                             help='Run import script in test mode for Travis.')
    pars_parent.add_argument('--log',  dest='log_filename',  default=None,
                             help='Filename to which to store logging information.')

    write_group = pars_parent.add_mutually_exclusive_group()
    write_group.add_argument('--write', action='store_true', dest='write_events', default=True,
                             help='Write events to files [default].')
    write_group.add_argument('--no-write', action='store_false', dest='write_events', default=True,
                             help='do not write events to file.')

    # Construct the subparser for `importer` submodule --- importing supernova
    # data
    pars_imp = subparsers.add_parser("importer", parents=[pars_parent],
                                     help="Generate a catalog JSON file")
    pars_imp.add_argument('--update', '-u', dest='update',
                          default=False, action='store_true',
                          help='Only update catalog using live sources.')
    pars_imp.add_argument('--refresh', '-r', dest='refresh',
                          default=False, action='store_true',
                          help='Ignore most task caches.')
    pars_imp.add_argument('--full-refresh', '-f', dest='full_refresh',
                          default=False, action='store_true',
                          help='Ignore all task caches.')
    pars_imp.add_argument('--archived', '-a', dest='archived',
                          default=False, action='store_true',
                          help='Always use task caches.')
    pars_imp.add_argument('--refreshlist', '-rl', dest='refresh_list', default='', nargs='+',
                          help='Space-delimited list of caches to clear.')

    pars_imp.add_argument('--tasks', dest='args_task_list', nargs='+', default=None,
                          help='space delimited list of tasks to perform (exclusively).')
    pars_imp.add_argument('--yes', dest='yes_task_list', nargs='+', default=None,
                          help='space delimited list of tasks to add to default list.')
    pars_imp.add_argument('--no', dest='no_task_list', nargs='+', default=None,
                          help='space delimited list of tasks to omit from default list.')

    args = parser.parse_args(args=args)
    # Print the help information if no subcommand is given (required for
    # operation)
    if args._name is None:
        parser.print_help()
        return None

    return args


def get_git():
    """Get a string representing the current git status --- i.e. tag and commit hash.
    """
    import subprocess
    git_vers = subprocess.getoutput(["git describe --always"]).strip()
    return git_vers
