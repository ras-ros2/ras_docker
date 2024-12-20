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

import argparse
import subprocess
import os,sys
from pathlib import Path
import vcstool,json,yaml
from functools import partial
from enum import Enum
from dataclasses import dataclass, field, InitVar

WORKING_PATH = (Path(__file__)/'../..').resolve()
TAG_SUFFIX = "ras_local"
docker_cmd_fmt_prefix = """docker run -it \
            -e DISPLAY={display_env} \
            --user {user_id}:{user_id} \
            -v /etc/localtime:/etc/localtime:ro \
            --name {container_name} \
            --workdir {work_dir} \
            --network host """
docker_gen_cmd_opts = """ -v {app_dir}:/{container_name}/ \
                         {extra_docker_args} -v /var/run/docker.sock:/var/run/docker.sock \
                            {gpu_arg} \
                            -v /dev/input:/dev/input --device-cgroup-rule='c 13:* rmw' """
docker_cmd_fmt_suffix= """ {image_name} \
            {command} """

docker_raw_cmd_fmt = (docker_cmd_fmt_prefix + docker_cmd_fmt_suffix).format
docker_cmd_fmt = (docker_cmd_fmt_prefix+docker_gen_cmd_opts+docker_cmd_fmt_suffix).format
docker_cmd_login_fmt = "docker exec -it -u {user_id}:{user_id} -w /{work_dir}  {container_name} {command} ".format

DOCKERHUB_REPO = "rasros2temp/ras"
workspace_build_cmd = "colcon build --symlink-install"

class AssetType(Enum):
    NONE = None

    LAB = "labs"
    MANIPULATOR = "manipulators"

def load_docker_common_args():
    global docker_cmd_fmt
    global docker_raw_cmd_fmt

    daemon_config_path = Path("/etc/docker/daemon.json")
    
    nvidia_ctk = False
    if daemon_config_path.exists():
        with daemon_config_path.open() as f:
            config = json.load(f)
            # Check if nvidia runtime is present in Docker's daemon config
            if "nvidia" in config.get("runtimes", {}):
                nvidia_ctk = True
    elif Path("/proc/driver/nvidia").exists():
        print("Warning: Docker Daemon Config not found")
        print("Warning: Please setup nvidia-ctk.")
    docker_gpu_arg = "--device /dev/dri"
    if(nvidia_ctk):
        docker_gpu_arg = "--gpus all -e NVIDIA_VISIBLE_DEVICES=all \
            -e NVIDIA_DRIVER_CAPABILITIES=all \
            --runtime nvidia"
    docker_cmd_fmt = partial(docker_cmd_fmt,
        display_env=os.environ["DISPLAY"],
        gpu_arg= docker_gpu_arg
    )
    docker_raw_cmd_fmt = partial(docker_raw_cmd_fmt,
        display_env=os.environ["DISPLAY"]
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

def pull_from_docker_repo(image_context:str,force=False):
    image_tag_local = f"{image_context}:ras_local"
    image_tag_remote = f"{DOCKERHUB_REPO}:{image_context}"
    if force or (not docker_check_image_exists(image_tag_remote)):
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
    force_pull = (hasattr(args,"image_pull") and args.image_pull)
    pull_from_docker_repo("ras_base",force_pull)
    pull_from_docker_repo(app_name,force_pull)

@dataclass
class CoreDockerConf:
    image_name:str
    container_name:str
    work_dir:str

@dataclass
class AppCoreConf(CoreDockerConf):
    app_ns:InitVar[str]
    image_name:str = field(init=False)
    container_name:str = field(init=False)
    work_dir:str = field(init=False)
    app_name:str = field(init=False)

    def __post_init__(self,app_ns:str):
        self.app_name = f"ras_{app_ns}_lab"
        self.image_name = f"ras_{app_ns}_lab:{TAG_SUFFIX}"
        self.container_name = f"ras_{app_ns}_lab"
        self.work_dir = f"/{self.app_name}/ros2_ws"


def get_app_spacific_docker_cmd(args : argparse.Namespace,docker_cmd_fmt_src,remove_cn=True,extra_docker_args = ""):
    app_conf = AppCoreConf(args.app)
    app_path = WORKING_PATH/'apps'/app_conf.app_name
    config_dir=str(WORKING_PATH/'configs')
    asset_dir=str(WORKING_PATH/'assets')
    if not app_path.exists():
        print(f"Error: {app_path} does not exist")
        print(f"Please run the init command first")
        exit(1)
    if remove_cn:
        extra_docker_args += " --rm "
    # if app_conf.app_name == "ras_sim_lab":
    extra_docker_args += f" -v {asset_dir}:/{app_conf.app_name}/ros2_ws/src/assets "
    docker_cmd_fmt_local = partial(docker_cmd_fmt_src,
        display_env=f"{os.environ['DISPLAY']}",
        app_dir=str(app_path),
        work_dir="/"+app_conf.app_name,
        extra_docker_args=f"-v {config_dir}:/{app_conf.app_name}/configs {extra_docker_args}"
    )
    
    allow_login = args.command in ["dev","run"]
    docker_cmd_fmt_new = regen_docker_fmt(docker_cmd_fmt_local,app_conf,allow_login=allow_login)
    if isinstance(docker_cmd_fmt_new,type(None)):
        print("Exiting")
        exit(1)
    return docker_cmd_fmt_new

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

    docker_cmd_fmt_local = get_app_spacific_docker_cmd(args,docker_cmd_fmt)

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
    workspace_path = f"/{app_name}/ros2_ws"
    run_command = f"{setup_cmd} && cd {workspace_path} && {workspace_build_cmd}"

    if clean_option:
        print("*****Clean Build Enabled*****")
        run_command = f"cd {workspace_path} && rm -rf build log install && {setup_cmd} && cd {workspace_path} && {workspace_build_cmd}"
    command_str =f"/bin/bash -c \"source /{app_name}/scripts/env.sh && {run_command}\""
    print(f"Building packages from docker file: {image_tag}")
    
    status = run_image_command_core(docker_cmd_fmt_local,command_str,as_root=False)
    if status:
        print("*****Build Successful, Ready for execution*****")
    else:
        print("*****Build error occurred. Image buuild will not be executed*****")

def run_image_app(args : argparse.Namespace ):
    app_name = f"ras_{args.app}_lab"
    bash_cmd = f"source /{app_name}/scripts/env.sh && ras_app"
    run_image_command(args=args, command_str=f"bash -c \"{bash_cmd}\"")

def check_container_already_running(container_name):
    command = ["docker", "ps", "--format", "{{.Names}}"]
    output = subprocess.check_output(command).decode("utf-8")
    return container_name in output

def regen_docker_fmt(docker_cmd_fmt,core_conf:CoreDockerConf,allow_login=False):
    if check_container_already_running(core_conf.container_name):
        if not allow_login:
            print(f"Container {core_conf.container_name} is already running")
            print("This command is not allowed to run on a running container")
            return None
        else:
            docker_cmd_fmt = docker_cmd_login_fmt
    docker_cmd_fmt_new = partial(docker_cmd_fmt,
                                 container_name =core_conf.container_name,
                                    work_dir = core_conf.work_dir,
                                    image_name = core_conf.image_name)

    return docker_cmd_fmt_new

def run_image_command_core(docker_command_fmt,command_str,as_root=False):
    os.system("xhost +local:root")
    user_id = 1000
    if as_root:
        user_id = 0
    docker_cmd = docker_command_fmt(
        user_id=user_id,
        command=command_str
    )
    assert isinstance(docker_cmd,str)
    _cmd_elems = []
    for _elem in docker_cmd.split(" "):
        _elem = _elem.strip()
        if len(_elem) > 0:
            _cmd_elems.append(_elem)
    print(f"Running Docker Command: {' '.join(_cmd_elems)}")
    ret = subprocess.run(docker_cmd,shell=True)
    return ret.returncode==0
    

def run_image_command(args : argparse.Namespace, command_str):
    docker_cmd_fmt_local = get_app_spacific_docker_cmd(args,docker_cmd_fmt)
    return run_image_command_core(docker_cmd_fmt_local,command_str,as_root=(hasattr(args,"root") and args.root))

def run_image_commits(args : argparse.Namespace):
    docker_cmd_fmt_local = get_app_spacific_docker_cmd(args,docker_raw_cmd_fmt,remove_cn=False)
    run_image_command_core(docker_cmd_fmt_local,"/bin/bash",as_root=True)
    app_conf = AppCoreConf(args.app)
    ret = subprocess.run(f"docker commit {app_conf.container_name} {app_conf.image_name}",check=True,shell=True)
    if ret.returncode == 0:
        print(f"Commited changes to image: {app_conf.image_name}")
        subprocess.run(f"docker tag {app_conf.image_name} {DOCKERHUB_REPO}:{app_conf.container_name}",check=True,shell=True)
    subprocess.run(f"docker rm {app_conf.container_name}",shell=True)


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
        nested_init_parser.add_argument("--image-pull","-i", action="store_true",default=False,dest="image_pull", help="Force pull the image from the docker repo")

        nested_build_parser = nested_subparsers.add_parser("build", help="Build the robot image")
        nested_build_parser.add_argument("--force", action="store_true", help="Force rebuild of the image")
        nested_build_parser.add_argument("--clean", action="store_true", help="Clean up intermediate build files")
        # nested_build_parser.add_argument("--offline", action="store_true", help="Build the image offline")

        nested_run_parser = nested_subparsers.add_parser("run", help="Run the real robot image")
        nested_dev_parser = nested_subparsers.add_parser("dev", help="Open terminal in Container")
        nested_dev_parser.add_argument("--root","-r", action="store_true", help="Open terminal as root user")
        nested_dev_parser.add_argument("--commit","-c", action="store_true", help="Commit changes to the image")
        nested_dev_parser.add_argument("--terminator","-t", action="store_true", help="Open terminal in terminator")

        # nested_push_parser = nested_subparsers.add_parser("push", help="Push the repos ")

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
        load_docker_common_args()
        build_image(args)
    elif args.command == "run":
        load_docker_common_args()
        run_image_app(args)
    elif args.command == "init":
        init_app(args)
    elif args.command == "dev":
        load_docker_common_args()
        if hasattr(args,"commit") and args.commit:
            run_image_commits(args)
        elif hasattr(args,"terminator") and args.terminator:
            run_image_command(args, "/bin/bash -c terminator")
        else:
            run_image_command(args, "/bin/bash")
        

    elif args.command == "test":
        load_docker_common_args()
        test_func(args)
    else:
        parser.print_help()

def main():
    parser = get_parser()
    parse_args(parser)
    
if __name__ == "__main__":
    main()
