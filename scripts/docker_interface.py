import argparse
import subprocess
import os,sys
from pathlib import Path
import vcstool,json,yaml
from functools import partial
from enum import Enum

WORKING_PATH = (Path(__file__)/'../..').resolve()
TAG_SUFFIX = "ras_local"
docker_cmd_fmt = """docker run -it --rm \
            -e DISPLAY={display_env} \
            -e ROS_DOMAIN_ID=2 \
            -v /etc/localtime:/etc/localtime:ro \
            -v {app_dir}:{work_dir} \
            --name {container_name} \
            --workdir {work_dir}/ros2_ws \
            --user {user_id}:{user_id} \
            {extra_docker_args} -v /var/run/docker.sock:/var/run/docker.sock \
            {gpu_arg} \
            --network host \
            -v /dev/input:/dev/input --device-cgroup-rule='c 13:* rmw' \
            {image_name} \
            {command}""".format

DOCKERHUB_REPO = "rasros2temp/ras"
workspace_build_cmd = "colcon build --symlink-install"

class AssetType(Enum):
    NONE = None

    LAB = "labs"
    MANIPULATOR = "manipulators"

def load_docker_common_args():
    global docker_cmd_fmt

    daemon_config_path = Path("/etc/docker/daemon.json")
    
    nvidia_ctk = False
    if daemon_config_path.exists():
        with daemon_config_path.open() as f:
            config = json.load(f)
            # Check if nvidia runtime is present in Docker's daemon config
            if "nvidia" in config.get("runtimes", {}):
                nvidia_ctk = True
    docker_gpu_arg = "--device /dev/dri"
    if(nvidia_ctk):
        docker_gpu_arg = "--gpus all -e NVIDIA_VISIBLE_DEVICES=all \
            -e NVIDIA_DRIVER_CAPABILITIES=all \
            --runtime nvidia"
    docker_cmd_fmt = partial(docker_cmd_fmt,
        display_env=os.environ["DISPLAY"],
        gpu_arg= docker_gpu_arg
    )

def vcs_fetch_repos(repos_file:Path,target_path:Path,pull=False):
    vcs_cmd = f"vcs import --recursive < {repos_file} "
    if pull:
        vcs_cmd += " && vcs pull . ; "
        yaml_obj = yaml.safe_load(repos_file.open())
        dirs_to_pull = set()
        for _k,_v in yaml_obj["repositories"].items():
            if 'type' in _v and _v['type'] == 'git':
                _path = Path(_k)
                if _path.parent != Path('.'): 
                    dirs_to_pull.add(_path.parent)
        for _d in dirs_to_pull:
            vcs_cmd += f" pushd {_d} > /dev/null ; vcs pull . ; popd > /dev/null ; "
    ret = subprocess.run(vcs_cmd, shell=True, cwd=str(target_path),executable="/bin/bash")
    return ret.returncode==0

def docker_check_image_exists(image_tag:str):
    image_exists = False
    images = subprocess.check_output(["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"]).decode("utf-8").splitlines()
    if image_tag in images:
        image_exists = True
        image_id = subprocess.check_output(["docker", "images", "--format", "{{.ID}}", "--filter", f"reference={image_tag}"]).decode("utf-8").strip()
        print(f"Older Image ID: {image_id}")
        print(f"Found Docker Image: {image_tag}")
    return image_exists

def docker_pull_image(image_tag:str):
    ret = subprocess.run(f"docker pull {image_tag}",shell=True)
    return ret.returncode==0

def pull_from_docker_repo_if_not_exists(image_context:str):
    image_tag_local = f"{image_context}:ras_local"
    image_tag_remote = f"{DOCKERHUB_REPO}:{image_context}"
    if not docker_check_image_exists(image_tag_remote):
        print(f"Pulling Image: {image_tag_remote}")
        if not docker_pull_image(image_tag_remote):
            print(f"Error: Image {image_tag_remote} not found")
            exit(1)
        subprocess.run(f"docker tag {image_tag_remote} {image_tag_local}",shell=True)
    else:
        print(f"Image {image_tag_remote} already exists")

def init_app(args: argparse.Namespace):
    init_setup(args)
    apps_path = WORKING_PATH/'apps'
    repos_path = WORKING_PATH/'repos'
    app_repos_path = repos_path/'apps'
    app_name = f"ras_{args.app}_lab"
    app_path = apps_path/app_name
    repos_file = app_repos_path/f"{app_name}.repos"
    if not repos_file.exists():
        print(f"Error: {repos_file} does not exist")
    if(vcs_fetch_repos(repos_file,apps_path,pull=True)):
        dep_repos_file = app_path/"deps.repos"
        vcs_fetch_repos(dep_repos_file,app_path,pull=True)
    pull_from_docker_repo_if_not_exists("ras_base")
    pull_from_docker_repo_if_not_exists(app_name)

def get_app_spacific_docker_cmd(args : argparse.Namespace,extra_docker_args = ""):
    app_name = f"ras_{args.app}_lab"
    container_name = f"ras_{args.app}_lab"
    image_tag = f"ras_{args.app}_lab:{TAG_SUFFIX}"
    app_path = WORKING_PATH/'apps'/app_name
    config_dir=str(WORKING_PATH/'configs')
    asset_dir=str(WORKING_PATH/'assets')
    user_id = 1000
    if hasattr(args,"root") and args.root:
        user_id = 0
    if not app_path.exists():
        print(f"Error: {app_path} does not exist")
        print(f"Please run the init command first")
        exit(1)

    if app_name == "ras_sim_lab":
        extra_docker_args = f" -v {asset_dir}:/{app_name}/ros2_ws/src/assets "
    docker_cmd_fmt_local = partial(docker_cmd_fmt,
        display_env=f"{os.environ['DISPLAY']}",
        app_dir=str(app_path),
        work_dir="/"+app_name,
        user_id=user_id,
        container_name=container_name,
        extra_docker_args=f"-v {config_dir}:/{app_name}/configs {extra_docker_args}",
        image_name=image_tag,
    )
    return docker_cmd_fmt_local

def build_image(args : argparse.Namespace):
    
    force_option = False
    clean_option = False
    offline_option = False

    if args.force:
        force_option = True
    if args.clean:
        clean_option = True

    app_name = f"ras_{args.app}_lab"
    image_name = f"ras_{args.app}_lab"
    image_tag = f"ras_{args.app}_lab:{TAG_SUFFIX}"

    docker_cmd_fmt_local = get_app_spacific_docker_cmd(args)

    def _build_image():
        print(f"*****Building Existing Docker Image: {image_name}*****")
        context_path = WORKING_PATH/'context'
        app_dockerfile = context_path/f"apps/Dockerfile.{args.app}"
        subprocess.run(f"docker build -t ras_base:{TAG_SUFFIX} -f Dockerfile.base .",shell=True,cwd=str(context_path))
        subprocess.run(f"docker build -t {image_tag} -f {app_dockerfile} .",shell=True,cwd=str(context_path))
    
    image_exists = docker_check_image_exists(image_tag)
    if (not image_exists) or force_option:
        _build_image()

    
    setup_cmd = f"cd /{app_name}/scripts && ./setup.sh"
    os.system("xhost +local:root")
    workspace_path = f"/{app_name}/ros2_ws"
    run_command = f"{setup_cmd} && cd {workspace_path} && {workspace_build_cmd} && exit"

    if clean_option:
        print("*****Clean Build Enabled*****")
        run_command = f"cd {workspace_path} && rm -rf build log install && {setup_cmd} && cd {workspace_path} && {workspace_build_cmd} && exit"

    print(f"Building packages from docker file: {image_tag}")
    try:
        docker_cmd = docker_cmd_fmt_local(
            command=f"/bin/bash -c \"source /{app_name}/scripts/env.sh && {run_command}\""
        )
        # print(docker_cmd.splitlines())
        assert isinstance(docker_cmd,str)
        subprocess.run(docker_cmd, check=True, shell=True)
        print("*****Build Successful, Ready for execution*****")
    except subprocess.CalledProcessError:
        print("*****Build error occurred. Image buuild will not be executed*****")

def run_image(args : argparse.Namespace ):
    app_name = f"ras_{args.app}_lab"
    bash_cmd = f"""if [ -e /tmp/.RAS_RUN ]
    then
        echo App is Already Running
    else
        echo Starting App
        touch /tmp/.RAS_RUN
        source /{app_name}/scripts/env.sh && /{app_name}/scripts/run.sh
        rm /tmp/.RAS_RUN
    fi
    """
    run_image_command(args=args, command_str=f"bash -c \"{bash_cmd}\"")

def run_image_command(args : argparse.Namespace, command_str):

    os.system("xhost +local:root")
    container_name = f"ras_{args.app}_lab"
    app_name = f"ras_{args.app}_lab"
    docker_cmd_fmt_local = get_app_spacific_docker_cmd(args)

    command = ["docker", "ps", "--format", "{{.Names}}"]
    output = subprocess.check_output(command).decode("utf-8")
    if container_name in output:
        if args.command == "run":
            print(f"Error: Container {container_name} is already running.")
            print("`run` command is only allowed to run on the main session to avoid ghost apps.")
            exit(1)
        user_id = 1000
        if hasattr(args,"root") and args.root:
            user_id = 0
        command = f"docker exec -it -u {user_id}:{user_id} -w /{app_name}/ros2_ws  {container_name} {command_str} "
        subprocess.run(command, shell=True)
    else:
        docker_cmd = docker_cmd_fmt_local(
            command=command_str
        )
        assert isinstance(docker_cmd,str)
        subprocess.run(docker_cmd,shell=True)

def init_setup(args : argparse.Namespace ):
    repos_file = WORKING_PATH/'repos'/(f"deps.repos")
    vcs_fetch_repos(repos_file,WORKING_PATH,pull=True)
    for _k,_v in AssetType._member_map_.items():

        if not isinstance(_v.value,str):
            continue
        asset_dir = WORKING_PATH/'assets'/_k.lower()
        asset_dir.mkdir(exist_ok=True)
        asset_repos_file = WORKING_PATH/'repos'/"resources"/"assets"/(f"{_v.value}.repos")
        vcs_fetch_repos(asset_repos_file,asset_dir,pull=True)

def test_func(args : argparse.Namespace):
    # docker_check_image_exists(f"ras_{args.app}_lab:ras_local")
    # pull_from_docker_repo_if_not_exists(f"ras_{args.app}_lab")
    pass

def get_parser():
    def add_nested_subparsers(subparser: argparse.ArgumentParser):
        nested_subparsers = subparser.add_subparsers(dest="command", help="Command to execute")

        nested_init_parser = nested_subparsers.add_parser("init", help="Initialize the application")

        nested_build_parser = nested_subparsers.add_parser("build", help="Build the robot image")
        nested_build_parser.add_argument("--force", action="store_true", help="Force rebuild of the image")
        nested_build_parser.add_argument("--clean", action="store_true", help="Clean up intermediate build files")
        # nested_build_parser.add_argument("--offline", action="store_true", help="Build the image offline")

        nested_run_parser = nested_subparsers.add_parser("run", help="Run the real robot image")
        nested_dev_parser = nested_subparsers.add_parser("dev", help="Open terminal in Container")
        nested_dev_parser.add_argument("--root","-r", action="store_true", help="Open terminal as root user")

        # nested_test_parser = nested_subparsers.add_parser("test", help="Run a test in the container")

        return nested_subparsers
        
    parser = argparse.ArgumentParser(description="RAS Docker Interface.\nBuild and run RAS applications")
    subparsers = parser.add_subparsers(dest="app", help="Application to run/build")

    real_parser = subparsers.add_parser("real", help="Real robot application")
    nested_real_parsers = add_nested_subparsers(real_parser)

    sim_parser = subparsers.add_parser("sim", help="Simulation application")
    nested_sim_parsers = add_nested_subparsers(sim_parser)

    return parser

def parse_args(parser : argparse.ArgumentParser):
    args = parser.parse_args()
    if (not hasattr(args, "app")) or isinstance(args.app, type(None)):
        parser.print_help()
        exit(1)
        
    elif args.command == "build":
        build_image(args)
    elif args.command == "run":
        run_image(args)
    elif args.command == "init":
        init_app(args)
    elif args.command == "dev":
        run_image_command(args, "/bin/bash")
    elif args.command == "test":
        test_func(args)
    else:
        parser.print_help()

def main():
    load_docker_common_args()
    parser = get_parser()
    parse_args(parser)
    
if __name__ == "__main__":
    main()