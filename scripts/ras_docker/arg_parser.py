import os
import argcomplete, argparse
from .app import build_image_app,run_image_app,init_app,run_image_command,run_image_commits,kill_app
from .vcs import init_setup,clear_setup,init_app_setup,repos_vcs_version,pull_repos_vcs,url_mode,get_vcs_status

supported_apps = ["robot","server"]

def get_parser(test_func_en = False):
    """
    Create and configure the argument parser for the RAS application interface.

    Args:
        test_func_en (bool): If True, includes the 'test' command under each app.

    Returns:
        argparse.ArgumentParser: The configured argument parser.
    """
    def add_nested_subparsers(subparser: argparse.ArgumentParser):
        """
        Adds nested subparsers to the given app-level parser for commands like init, build, run, etc.

        Args:
            subparser (argparse.ArgumentParser): The app-level parser to attach subcommands to.

        Returns:
            argparse._SubParsersAction: The nested subparsers object.
        """
        nested_subparsers = subparser.add_subparsers(title="app",dest="command", help="Command to execute")

        nested_init_parser = nested_subparsers.add_parser("init", help="Initialize the application")
        nested_init_parser.add_argument("--image-pull","-i", action="store_true",default=False,dest="image_pull", help="Force pull the image from the docker repo")

        nested_build_parser = nested_subparsers.add_parser("build", help="Build the robot image")
        nested_build_parser.add_argument("--force", action="store_true", help="Force rebuild of the image")
        nested_build_parser.add_argument("--clean", action="store_true", help="Clean up intermediate build files")

        nested_run_parser = nested_subparsers.add_parser("run", help="Run the robot robot image")
        nested_run_parser.add_argument("args", nargs=argparse.REMAINDER, help="Arguments to pass to the run command")
        
        nested_kill_parser = nested_subparsers.add_parser("kill", help="Kill the robot image")
        
        nested_dev_parser = nested_subparsers.add_parser("dev", help="Open terminal in Container")
        nested_dev_parser.add_argument("--root","-r", action="store_true", help="Open terminal as root user")
        nested_dev_parser.add_argument("--commit","-c", action="store_true", help="Commit changes to the image")
        nested_dev_parser.add_argument("--terminator","-t", action="store_true", help="Open terminal in terminator")
        nested_dev_parser.add_argument("--vscode","-v", action="store_true", help="Attach container in vscode")

        if test_func_en:
            nested_test_parser = nested_subparsers.add_parser("test", help="Run a test in the container")

        return nested_subparsers

    parser = argparse.ArgumentParser(description="RAS Application Interface.\nBuild and run RAS applications")
    app_subparsers = parser.add_subparsers(dest="app", help="Application to run/build")

    def add_app_subparsers(app_subparsers : argparse._SubParsersAction ):
        """
        Adds app-specific subparsers for each supported app.

        Args:
            app_subparsers (argparse._SubParsersAction): Top-level app subparsers to which app-specific subcommands are added.

        Returns:
            argparse._SubParsersAction: The updated app subparsers.
        """
        for app_name in supported_apps:
            app_parser = app_subparsers.add_parser(app_name, help=f"{app_name} application")
            nested_app_parsers = add_nested_subparsers(app_parser)
        return app_subparsers

    app_subparsers = add_app_subparsers(app_subparsers)

    app_parser : argparse.ArgumentParser = app_subparsers.add_parser("app", help="Application commands")
    cmd_app_subparsers = app_parser.add_subparsers(title="app",dest="app", help="Application to run/build")
    cmd_app_subparsers = add_app_subparsers(cmd_app_subparsers)

    setup_parser : argparse.ArgumentParser = app_subparsers.add_parser("init", help="Initialize the RAS setup")
    clear_parser : argparse.ArgumentParser = app_subparsers.add_parser("clear", help="Clear the RAS setup")

    vcs_parser : argparse.ArgumentParser = app_subparsers.add_parser("vcs", help="VCS commands")
    cmd_vcs_subparsers = vcs_parser.add_subparsers(title="vcs",dest="vcs", help="VCS commands")

    url_parser = cmd_vcs_subparsers.add_parser("url-mode", help="Set the url mode to https or ssh")
    url_parser.add_argument("url_mode", help="URL mode to set (https/ssh).", choices=["https","ssh"],default=None,nargs="?")

    pull_parser = cmd_vcs_subparsers.add_parser("pull", help="Pull the repositories")
    pull_parser.add_argument("version", help="Version to pull",default=None,nargs="?")

    version_parser = cmd_vcs_subparsers.add_parser("version", help="Set/Get the version of the repositories")
    version_parser.add_argument("version", help="Version to set (empty if get)",default=None,nargs="?")
    
    status_parser = cmd_vcs_subparsers.add_parser("status", help="Get the status of the repositories")
    status_parser.add_argument("--fetch","-f", action="store_true", help="Fetch the repositories")

    argcomplete.autocomplete(parser)
    return parser

def parse_args(parser : argparse.ArgumentParser,test_func = None):
    """
    Parse the command line arguments and call the appropriate handler based on the parsed arguments.

    Args:
        parser (argparse.ArgumentParser): The argument parser.
        test_func (callable, optional): A function to run if 'test' command is issued.

    Raises:
        ValueError: If the test_func is not callable and 'test' command is issued.
    """
    args = parser.parse_args()

    if hasattr(args, "app") and args.app in supported_apps:
        os.environ["APP_TYPE"] = args.app
    if (not hasattr(args, "app")) or isinstance(args.app, type(None)):
        parser.print_help()
        exit(1)
    if (args.app == "app") or (args.app in supported_apps):
        if args.command == "build":
            build_image_app(args)
        elif args.command == "run":
            run_image_app(args)
        elif args.command == "kill":
            kill_app(args)
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
    elif args.app == "init":
        init_setup(args)
    elif args.app == "clear":
        clear_setup(args)
    elif args.app == "vcs":
        if args.vcs == "url-mode":
            url_mode(args)
        elif args.vcs == "pull":
            version = pull_repos_vcs(args)
            if version:
                print("Pulled to Version :",version )
        elif args.vcs == "version":
            version = repos_vcs_version(args)
            if version:
                print("Current Version :", version)
        elif args.vcs == "status":
            get_vcs_status(args)
        else:
            parser.print_help()
    else:
        parser.print_help()
