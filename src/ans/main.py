#!/usr/bin/env python3
import sys
import os
from . import gui
from . import config
from . import dependency
import argparse
from PyQt5.QtWidgets import QApplication


# global variables
version = "0.0.0"
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

def setting_gui(maindir):
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
    subparsers = parser.add_subparsers(dest='command')
    # MODULE 1: init
    init_cmd = subparsers.add_parser('init', help='initialize ans project',
    description="Initialize a project directory. Example: $ ans init <PATH>")
    init_cmd.add_argument(
        type=str,
        dest='maindir',
        help='path to the main project directory (default=".")',
        action='store',
        default='.'
    )
    # MODULE 2: setting
    setting_cmd = subparsers.add_parser('setting', help='configure project settings',
    description="Configure project settings")
    setting_cmd.add_argument(
        '--maindir',
        type=str,
        help='path to the main project directory (default=".")',
        action='store',
        default='.'
    )
    # MODULE 3: download
    download_cmd = subparsers.add_parser('download', help='download module',
    description="Download station list, station meta files, and mseed files.")
    download_cmd.add_argument(
        '--maindir',
        type=str,
        help='path to the main project directory (default=".")',
        action='store',
        default='.'
    )
    # MODULE 4: mseed2sac
    mseed2sac_cmd = subparsers.add_parser('mseed2sac', help='mseed2sac processes module',
    description="mseed2sac processes module.")
    mseed2sac_cmd.add_argument(
        '--maindir',
        type=str,
        help='path to the main project directory (default=".")',
        action='store',
        default='.'
    )
    # MODULE 5: sac2ncf
    sac2ncf_cmd = subparsers.add_parser('sac2ncf', help='sac2ncf processes module',
    description="sac2ncf processes module.")
    sac2ncf_cmd.add_argument(
        '--maindir',
        type=str,
        help='path to the main project directory (default=".")',
        action='store',
        default='.'
    )
    # MODULE 6: ncf2egf
    ncf2egf_cmd = subparsers.add_parser('ncf2egf', help='ncf2egf processes module',
    description="ncf2egf processes module.")
    ncf2egf_cmd.add_argument(
        '--maindir',
        type=str,
        help='path to the main project directory (default=".")',
        action='store',
        default='.'
    )

    #########################
    #    PARSE ARGUMENTS
    #########################
    args = parser.parse_args()
    if args.about or len(sys.argv) == 1:
        print(f"{about}\n")
        sys.exit(0)
    print(f"Project directory: {os.path.abspath(args.maindir)}")
    # init
    args.maindir = os.path.abspath(args.maindir)
    if args.command == 'init':
        if not os.path.isdir(args.maindir):
            os.mkdir(args.maindir)
        defaults = config.Defaults(args.maindir)
        parameters = defaults.parameters()
        config.write_config(os.path.join(args.maindir,'ans.conf'), parameters)
    # setting
    if args.command == 'setting':
        setting_gui(args.maindir)
    # download
    if args.command == 'download':
        print(dev)
    # mseed2sac
    if args.command == 'mseed2sac':
        print(dev)
    # sac2ncf
    if args.command == 'sac2ncf':
        print(dev)
    # ncf2egf
    if args.command == 'ncf2egf':
        print(dev)

if __name__ == "__main__":
    main(**vars(args))
