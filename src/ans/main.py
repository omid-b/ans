#!/usr/bin/env python3
import sys
import os


import argparse
from PyQt5.QtWidgets import QApplication

from . import gui
from . import config
from . import dependency
from . import download
from . import mseed2sac
from . import sac2ncf
from . import ncf2egf
from . import plot

# global variables
# version 0.0.1 >> EGFs from zero to hero!
version = "0.0.1"
about = "ANS: ambient noise seismology, is a python wrapper \
for a selection of ambient noise seismology codes and procedures. \
\n\nContact information:\
\n    Author: Omid Bagherpur\
\n    Email: omid.bagherpur@gmail.com\
\n    GitHub: https://github.com/omid-b/ans\
\n    PyPI: https://pypi.org/project/ans/\
\n\nPlease enter 'ans -h' or 'ans --help' for usage information."
dev = "Not developed yet!"
pkg_dir, _ = os.path.split(__file__)

# clear_screen
if sys.platform in ["linux","linux2","darwin"]:
    os.system('clear')
elif sys.platform == "win32":
    os.system('cls')
dependency.print_warnings()

def config_gui(maindir):
    app = QApplication(sys.argv)
    win = gui.MainWindow(maindir)
    win.show()
    sys.exit(app.exec_())
    app.exec_()


def main():
    #########################
    #    ARGUMENT PARSER    #
    #########################
    parser = argparse.ArgumentParser('ans',
    description="ANS: Ambient Noise Seismology python wrappers.",
    conflict_handler='resolve')
    parser.add_argument(
        '-a',
        '--about',
        action='store_true',
        help='about this package and contact information'
    )
    parser.add_argument('--version', action='version', version=f'%(prog)s {version}')
    parser._positionals.title = 'list of modules'
    ###
    commands = parser.add_subparsers(dest='command')
    # MODULE 1: init
    init_cmd = commands.add_parser('init', help='initialize ans project',
    description="Initialize a project directory. Example: $ ans init <PATH>")
    init_cmd.add_argument(
        type=str,
        dest='maindir',
        help='path to the main project directory',
        action='store'
    )
    # MODULE 2: config
    config_cmd = commands.add_parser('config', help='configure project settings',
    description="Configure project settings in a GUI")
    config_cmd.add_argument(
        '--maindir',
        type=str,
        help='path to the main project directory (default=".")',
        action='store',
        default='.'
    )
    # MODULE 3: download
    download_cmd = commands.add_parser('download', help='download module',
    description="Download station list, station meta files, and mseed files.")
    download_subcmd = download_cmd.add_subparsers(dest='subcommand')

    download_stations = download_subcmd.add_parser('stations', help="download station list",
        description="Download station list")

    download_metadata = download_subcmd.add_parser('metadata', help="download station meta files",
        description="Download '*.xml' meta files")

    download_mseeds = download_subcmd.add_parser('mseeds', help="download mseed files",
        description="Download '*.mseed' data files")

    download_stations.add_argument(
        '--maindir',
        type=str,
        help='path to the main project directory (default=".")',
        action='store',
        default='.'
    )
    download_metadata.add_argument(
        '--maindir',
        type=str,
        help='path to the main project directory (default=".")',
        action='store',
        default='.'
    )
    download_metadata.add_argument(
        '--update_stations',
        help='update the list of stations based on the content of metadata directory after download',
        action='store_true',
        default=False
    )
    download_mseeds.add_argument(
        '--maindir',
        type=str,
        help='path to the main project directory (default=".")',
        action='store',
        default='.'
    )
    download_cmd.add_argument(
        '--maindir',
        type=str,
        help='path to the main project directory (default=".")',
        action='store',
        default='.'
    )
    # MODULE 4: mseed2sac
    mseed2sac_cmd = commands.add_parser('mseed2sac', help='mseed2sac processes module',
    description="mseed2sac processes module.")
    mseed2sac_cmd.add_argument(
        'mseeds_dir',
        type=str,
        help='path to the downloaded MSEED files dataset directory',
        action='store',
    )
    mseed2sac_cmd.add_argument(
        'sacs_dir',
        type=str,
        help='path to the output SAC files dataset directory',
        action='store',
    )
    mseed2sac_cmd.add_argument(
        '--maindir',
        type=str,
        help='path to the main project directory (default=".")',
        action='store',
        default='.'
    )
    mseed2sac_cmd.add_argument(
        '--all',
        help='output all and ignore station list',
        action='store_true',
    )
    # MODULE 5: sac2ncf
    sac2ncf_cmd = commands.add_parser('sac2ncf', help='sac2ncf processes module',
    description="sac2ncf processes module.")
    sac2ncf_cmd.add_argument(
        'sacs_dir',
        type=str,
        help='path to the input SAC files dataset directory',
        action='store',
    )
    sac2ncf_cmd.add_argument(
        'ncfs_dir',
        type=str,
        help='path to the output NCF files dataset directory',
        action='store',
    )
    sac2ncf_cmd.add_argument(
        '--maindir',
        type=str,
        help='path to the main project directory (default=".")',
        action='store',
        default='.'
    )
    sac2ncf_cmd.add_argument(
        '--all',
        help='output all and ignore station list',
        action='store_true',
    )
    # MODULE 6: ncf2egf
    ncf2egf_cmd = commands.add_parser('ncf2egf', help='ncf2egf processes module',
    description="ncf2egf processes module.")
    ncf2egf_cmd.add_argument(
        'ncfs_dir',
        type=str,
        help='path to the input NCF files dataset directory',
        action='store',
    )
    ncf2egf_cmd.add_argument(
        'egfs_dir',
        type=str,
        help='path to the output EGF files dataset directory',
        action='store',
    )
    ncf2egf_cmd.add_argument(
        '--cmp',
        nargs='*',
        type=str,
        action='store',
        default=['ZZ','TT'],
        help='cross-correlation component(s) (default: ZZ TT)')
    ncf2egf_cmd.add_argument(
        '--maindir',
        type=str,
        help='path to the main project directory (default=".")',
        action='store',
        default='.'
    )


    # MODULE 7: plot
    plot_cmd = commands.add_parser('plot', help='plot module',
    description="Plot module.")
    plot_subcmd = plot_cmd.add_subparsers(dest='subcommand')
    plot_stations = plot_subcmd.add_parser('stations', help="plot station list",
        description="Plot station list using GMT")
    plot_stations.add_argument(
        '--maindir',
        type=str,
        help='path to the main project directory (default=".")',
        action='store',
        default='.'
    )
    plot_stations.add_argument('--labels', action='store_true',help='print station labels on the output map')

    # MODULE N: egf2fan
    # egf2fan_cmd = commands.add_parser('egf2fan', help='ncf2egf processes module',
    # description="ncf2egf processes module.")

    #########################
    #    PARSE ARGUMENTS
    #########################
    args = parser.parse_args()
    if args.about or len(sys.argv) == 1:
        print(f"{about}\n")
        sys.exit(0)
    
    print(f"Project directory: {os.path.abspath(args.maindir)}\n")
    # init
    args.maindir = os.path.abspath(args.maindir)
    if args.command == 'init':
        if not os.path.isdir(args.maindir):
            os.mkdir(args.maindir)
        if not os.path.isdir(os.path.join(args.maindir, '.ans')):
            os.mkdir(os.path.join(args.maindir, '.ans'))
        defaults = config.Defaults(args.maindir)
        parameters = defaults.parameters()
        config.write_config(args.maindir, parameters)
        print("Project directory was successfully initialized!\n")
    # config
    if args.command == 'config':
        config_gui(args.maindir)
    # download
    if args.command == 'download':
        if args.subcommand == 'stations':
            download.download_stations(args.maindir)
        elif args.subcommand == 'metadata':
            download.download_metadata(args.maindir, args.update_stations)
        elif args.subcommand == 'mseeds':
            download.download_mseeds(args.maindir)
    # mseed2sac
    if args.command == 'mseed2sac':
        mseed2sac.mseed2sac_run_all(args.maindir, args.mseeds_dir, args.sacs_dir, args.all)
    # sac2ncf
    if args.command == 'sac2ncf':
        sac2ncf.sac2ncf_run_all(args.maindir, args.sacs_dir, args.ncfs_dir, args.all)
    # ncf2egf
    if args.command == 'ncf2egf':
        ncf2egf.ncf2egf_run_all(args.maindir, args.ncfs_dir, args.egfs_dir, args.cmp)
    # plot
    if args.command == 'plot':
        if args.subcommand == 'stations':
            plot.plot_stations(args.maindir, labels=args.labels)


if __name__ == "__main__":
    main(**vars(args))
