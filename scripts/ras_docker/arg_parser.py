"""
Copyright (C) 2024 Harsh Davda

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.

For inquiries or further information, you may contact:
Harsh Davda
Email: info@opensciencestack.org
"""
# PYTHON_ARGCOMPLETE_OK

import argcomplete, argparse
from .app import build_image_app,run_image_app,init_app,run_image_command,run_image_commits
def get_parser(test_func_en = False):
    def add_nested_subparsers(subparser: argparse.ArgumentParser):
        nested_subparsers = subparser.add_subparsers(dest="command", help="Command to execute")

        nested_init_parser = nested_subparsers.add_parser("init", help="Initialize the application")
        nested_init_parser.add_argument("--image-pull","-i", action="store_true",default=False,dest="image_pull", help="Force pull the image from the docker repo")

        nested_build_parser = nested_subparsers.add_parser("build", help="Build the robot image")
        nested_build_parser.add_argument("--force", action="store_true", help="Force rebuild of the image")
        nested_build_parser.add_argument("--clean", action="store_true", help="Clean up intermediate build files")
        # nested_build_parser.add_argument("--offline", action="store_true", help="Build the image offline")

        nested_run_parser = nested_subparsers.add_parser("run", help="Run the robot robot image")
        nested_run_parser.add_argument("args", nargs=argparse.REMAINDER, help="Arguments to pass to the run command")

        nested_dev_parser = nested_subparsers.add_parser("dev", help="Open terminal in Container")
        nested_dev_parser.add_argument("--root","-r", action="store_true", help="Open terminal as root user")
        nested_dev_parser.add_argument("--commit","-c", action="store_true", help="Commit changes to the image")
        nested_dev_parser.add_argument("--terminator","-t", action="store_true", help="Open terminal in terminator")
        nested_dev_parser.add_argument("--vscode","-v", action="store_true", help="Attach container in vscode")

        # nested_push_parser = nested_subparsers.add_parser("push", help="Push the repos ")
        if test_func_en:
            nested_test_parser = nested_subparsers.add_parser("test", help="Run a test in the container")

        return nested_subparsers
        
    parser = argparse.ArgumentParser(description="RAS Docker Interface.\nBuild and run RAS applications")
    subparsers = parser.add_subparsers(dest="app", help="Application to run/build")

    real_parser = subparsers.add_parser("robot", help="robot robot application")
    nested_real_parsers = add_nested_subparsers(real_parser)

    sim_parser = subparsers.add_parser("server", help="Simulation application")
    nested_sim_parsers = add_nested_subparsers(sim_parser)

    argcomplete.autocomplete(parser)
    return parser

def parse_args(parser : argparse.ArgumentParser,test_func = None):
    args = parser.parse_args()
    if (not hasattr(args, "app")) or isinstance(args.app, type(None)):
        parser.print_help()
        exit(1)
        
    elif args.command == "build":
        build_image_app(args)
    elif args.command == "run":
        run_image_app(args)
    elif args.command == "init":
        init_app(args)
    elif args.command == "dev":
        if hasattr(args,"commit") and args.commit:
            run_image_commits(args)
        elif hasattr(args,"terminator") and args.terminator:
            run_image_command(args, "/bin/bash -c terminator")
        else:
            run_image_command(args, "/bin/bash")
    
    elif args.command == "test":
        if callable(test_func):
            test_func(args)
        else:
            raise ValueError(f"Invalid Test Function {test_func}")
    else:
        parser.print_help()
