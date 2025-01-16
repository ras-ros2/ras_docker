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

from .common import Path,partial,get_display_var,subprocess,ROS2_PKGS_PATH
import json
from dataclasses import dataclass
import os

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
                            -v /dev/input:/dev/input --device-cgroup-rule='c 13:* rmw' """ + f" -v {ROS2_PKGS_PATH}:/{{container_mame}}/ros2_ws/src/core_pkgs "
docker_cmd_fmt_suffix= """ {image_name} \
            {command} """

docker_raw_cmd_fmt = (docker_cmd_fmt_prefix + docker_cmd_fmt_suffix).format
docker_cmd_fmt = (docker_cmd_fmt_prefix+docker_gen_cmd_opts+docker_cmd_fmt_suffix).format
docker_cmd_login_fmt = "docker exec -it -u {user_id}:{user_id} -w /{work_dir}  {container_name} {command} ".format

DOCKERHUB_REPO = "rasros2temp/ras"

TAG_SUFFIX = "ras_local"


@dataclass
class CoreDockerConf:
    image_name:str
    container_name:str
    work_dir:str

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
        display_env=get_display_var(),
        gpu_arg= docker_gpu_arg
    )
    docker_raw_cmd_fmt = partial(docker_raw_cmd_fmt,
        display_env=get_display_var()
    )


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

