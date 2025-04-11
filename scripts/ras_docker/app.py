from .arg_parser import argparse
from .common import WORKING_PATH,partial,get_display_var,subprocess,WORKSPACE_BUILD_CMD as workspace_build_cmd,Path,get_docker_cmd_fmt,DockerCmdType,is_wsl
from .vcs import init_setup,init_app_setup
from .docker import pull_from_docker_repo,TAG_SUFFIX,regen_docker_fmt,CoreDockerConf,\
        docker_check_image_exists,run_image_command_core,DOCKERHUB_REPO,kill_docker_container
from dataclasses import dataclass, field, InitVar

def init_app(args: argparse.Namespace):
    if not init_setup(args):
        return
    apps_path = WORKING_PATH/'apps'
    apps_path.mkdir(parents=True,exist_ok=True)
    repos_path = WORKING_PATH/'repos'
    app_repos_path = repos_path/'apps'
    app_name = f"ras_{args.app}_app"
    app_path = apps_path/app_name
    if not init_app_setup(args):
        return
    # repos_file = app_repos_path/f"{app_name}.repos"
    # if not repos_file.exists():
    #     print(f"Error: {repos_file} does not exist")
    # if(vcs_fetch_repos(repos_file,apps_path,pull=True)):
    #     dep_repos_file = app_path/"deps.repos"
    #     vcs_fetch_repos(dep_repos_file,app_path,pull=True)
    force_pull = (hasattr(args,"image_pull") and args.image_pull)
    pull_from_docker_repo("ras_base",force_pull)
    pull_from_docker_repo(app_name,force_pull)


@dataclass
class AppCoreConf(CoreDockerConf):
    app_ns:InitVar[str]
    image_name:str = field(init=False)
    container_name:str = field(init=False)
    work_dir:str = field(init=False)
    app_name:str = field(init=False)

    def __post_init__(self,app_ns:str):
        self.app_name = f"ras_{app_ns}_app"
        self.image_name = f"ras_{app_ns}_app:{TAG_SUFFIX}"
        self.container_name = f"ras_{app_ns}_app"
        self.work_dir = f"/{self.app_name}/ros2_ws"



# def get_app_spacific_docker_cmd(args : argparse.Namespace,docker_cmd_fmt_src,remove_cn=True,extra_docker_args = ""):
#     app_conf = AppCoreConf(args.app)
#     app_path = WORKING_PATH/'apps'/app_conf.app_name
#     config_dir=str(WORKING_PATH/'configs')
#     asset_dir=str(WORKING_PATH/'assets')
#     if not app_path.exists():
#         print(f"Error: {app_path} does not exist")
#         print(f"Please run the init command first")
#         exit(1)
#     if remove_cn:
#         extra_docker_args += " --rm "
#     # if app_conf.app_name == "ras_server_app":
#     extra_docker_args += f" -v {asset_dir}:/{app_conf.app_name}/ros2_ws/src/assets "
#     docker_cmd_fmt_local = partial(docker_cmd_fmt_src,
#         display_env=f"{get_display_var()}",
#         app_dir=str(app_path),
#         work_dir="/"+app_conf.app_name,
#         extra_docker_args=f"-v {config_dir}:/{app_conf.app_name}/configs {extra_docker_args}"
#     )
#     allow_login = args.command in ["dev","run"]
#     docker_cmd_fmt_new = regen_docker_fmt(docker_cmd_fmt_local,app_conf,allow_login=allow_login)
#     if isinstance(docker_cmd_fmt_new,type(None)):
#         print("Already Running")
#         exit(1)
#     return docker_cmd_fmt_new

def get_app_spacific_docker_cmd(args: argparse.Namespace, docker_cmd_fmt_src, remove_cn=True, extra_docker_args=""):
    app_conf = AppCoreConf(args.app)
    app_path = WORKING_PATH / 'apps' / app_conf.app_name
    config_dir = str(WORKING_PATH / 'configs')
    asset_dir = str(WORKING_PATH / 'assets')

    if not app_path.exists():
        print(f"Error: {app_path} does not exist")
        print(f"Please run the init command first")
        exit(1)

    # Freshly construct docker args for this app
    docker_args = ""
    if remove_cn:
        docker_args += " --rm "
    
    # Only mount assets if this is the server app
    if app_conf.app_name == "ras_server_app":
        docker_args += f" -v {asset_dir}:/{app_conf.app_name}/ros2_ws/src/assets "
    
    # Always mount the config directory
    docker_args = f"-v {config_dir}:/{app_conf.app_name}/configs {docker_args}"

    docker_cmd_fmt_local = partial(
        docker_cmd_fmt_src,
        display_env=f"{get_display_var()}",
        app_dir=str(app_path),
        work_dir="/" + app_conf.app_name,
        extra_docker_args=docker_args
    )

    allow_login = args.command in ["dev", "run"]
    docker_cmd_fmt_new = regen_docker_fmt(docker_cmd_fmt_local, app_conf, allow_login=allow_login)

    if docker_cmd_fmt_new is None:
        print("Already Running")
        exit(1)

    return docker_cmd_fmt_new




def build_image_app(args : argparse.Namespace):
    
    force_option = False
    clean_option = False
    offline_option = False
    if args.force:
        force_option = True
    if args.clean:
        clean_option = True

    app_name = f"ras_{args.app}_app"
    image_name = f"ras_{args.app}_app"
    image_tag = f"ras_{args.app}_app:{TAG_SUFFIX}"

    docker_cmd_fmt_local = get_app_spacific_docker_cmd(args,get_docker_cmd_fmt(DockerCmdType.FULL))

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


def run_image_command(args : argparse.Namespace, command_str):
    app_conf = AppCoreConf(args.app)
    extra_docker_args = ""
    as_root=(hasattr(args,"root") and args.root)
    if not as_root:
        dev_container_path = WORKING_PATH/'.devcontainer'/app_conf.container_name
        extra_docker_args = f" -v {dev_container_path}/.vscode:/home/ras/.vscode-server "
    if hasattr(args,"vscode") and args.vscode:
        if as_root:
            print("Error: Cannot run vscode as root")
            exit(1)
        container_name = app_conf.container_name
        container_conf_path = Path.home()/f".config/Code/User/globalStorage/ms-vscode-remote.remote-containers/imageConfigs/"
        container_conf_path.mkdir(parents=True,exist_ok=True)
        dev_container_path = WORKING_PATH/'.devcontainer'/container_name
        pre_vscode_cmd = f"cp {dev_container_path}/image_config.json {container_conf_path}/{container_name}.json"
        subprocess.run(pre_vscode_cmd,shell=True)
        vscode_ws = f"{dev_container_path}/{container_name}"
        code_cmd = f"code"
        if is_wsl():
            # vscode_ws += "_wsl"
            code_cmd = "/mnt/c/Program Files/Microsoft VS Code/Code.exe"
            if not Path(code_cmd).exists():
                print("Unwxpected vscode setup")
            code_cmd = f"\"{code_cmd}\""
            subprocess.run(f"{code_cmd} {vscode_ws}.code-workspace &",shell=True)
        else:
            vscode_cmd = f"{code_cmd} {vscode_ws}.code-workspace"
            subprocess.run(vscode_cmd,shell=True)
    docker_cmd_fmt_local = get_app_spacific_docker_cmd(args,get_docker_cmd_fmt(DockerCmdType.FULL),extra_docker_args=extra_docker_args)
    return run_image_command_core(docker_cmd_fmt_local,command_str,as_root=as_root)

def run_image_commits(args : argparse.Namespace):
    docker_cmd_fmt_local = get_app_spacific_docker_cmd(args,get_docker_cmd_fmt(DockerCmdType.RAW),remove_cn=False)
    run_image_command_core(docker_cmd_fmt_local,"/bin/bash",as_root=True)
    app_conf = AppCoreConf(args.app)
    ret = subprocess.run(f"docker commit {app_conf.container_name} {app_conf.image_name}",check=True,shell=True)
    if ret.returncode == 0:
        print(f"Commited changes to image: {app_conf.image_name}")
        subprocess.run(f"docker tag {app_conf.image_name} {DOCKERHUB_REPO}:{app_conf.container_name}",check=True,shell=True)
    subprocess.run(f"docker rm {app_conf.container_name}",shell=True)


def run_image_app(args : argparse.Namespace ):
    app_name = f"ras_{args.app}_app"
    bash_cmd = f"source /{app_name}/scripts/env.sh && ras_app " + " ".join(args.args)
    run_image_command(args=args, command_str=f"bash -c \"{bash_cmd}\"")


def kill_app(args : argparse.Namespace):
    app_conf = AppCoreConf(args.app)
    kill_docker_container(app_conf.container_name)
