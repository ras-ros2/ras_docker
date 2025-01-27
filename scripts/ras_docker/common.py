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

from pathlib import Path
from enum import Enum
import ras_docker
import subprocess
from functools import partial
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial

WORKING_PATH = Path(os.environ["RAS_DOCKER_PATH"])
ROS2_PKGS_PATH = WORKING_PATH/"ros2_pkgs"

WORKSPACE_BUILD_CMD = "colcon build --symlink-install"

class AssetType(Enum):
    NONE = None

    LAB = "labs"
    MANIPULATOR = "manipulators"

class DockerCmdType(Enum):
    NONE = None

    FULL = 1
    RAW = 2
    ATTACH = 3

import re
from string import Formatter

def parse_with_format(format_string, input_string):
    formatter = Formatter()
    pattern = "^"
    field_names = []

    for literal_text, field_name, format_spec, conversion in formatter.parse(format_string):
        if literal_text:
            pattern += re.escape(literal_text)
        if field_name:
            field_names.append(field_name)
            pattern += r"(?P<" + field_name + r">[^/]+)"

    pattern += "$"

    match = re.match(pattern, input_string)
    if not match:
        raise ValueError(f"Input string does not match the format: {input_string}")

    return match.groupdict()

def get_docker_cmd_fmt(cmd_type: DockerCmdType):
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
                                -v /dev/input:/dev/input --device-cgroup-rule='c 13:* rmw' """ + f" -v {ROS2_PKGS_PATH}:/{{container_name}}/ros2_ws/src/common_pkgs "
    docker_cmd_fmt_suffix= """ {image_name} \
                {command} """
    docker_cmd_fmt = None
    if (cmd_type == DockerCmdType.RAW):
        docker_cmd_fmt = (docker_cmd_fmt_prefix + docker_cmd_fmt_suffix).format
    elif (cmd_type == DockerCmdType.FULL):
        docker_cmd_fmt = (docker_cmd_fmt_prefix+docker_gen_cmd_opts+docker_cmd_fmt_suffix).format
    elif (cmd_type == DockerCmdType.ATTACH):
        docker_cmd_fmt = "docker exec -it -u {user_id}:{user_id} -w /{work_dir}  {container_name} {command} ".format
        return docker_cmd_fmt
    else:
        raise ValueError(f"invalid docker cmd_type {cmd_type}")

    daemon_config_path = Path("/etc/docker/daemon.json")
    
    nvidia_ctk = False
    if daemon_config_path.exists():
        import json
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
    if (cmd_type==DockerCmdType.FULL):
        return partial(docker_cmd_fmt,
                display_env=get_display_var(),
                gpu_arg= docker_gpu_arg
            )
    elif (cmd_type==DockerCmdType.RAW):
        return partial(docker_cmd_fmt,
                display_env=get_display_var()
            )
    else:
        raise ValueError(f"Unexpected docker cmd_type{cmd_type}")


def prepend_root_command(command_str:str):
    return f"sudo -E bash -c '{command_str}'"

def run_command_shell(command_str:str,as_root:bool=False,work_dir:Path=None,read_output=False,preview=True):
    if isinstance(work_dir,Path):
        work_dir = str(work_dir)
    if as_root:
        command_str = prepend_root_command(command_str)
    if preview:
        print("Running Command:",command_str)
    return subprocess.run(command_str,shell=True,cwd=work_dir,executable="/bin/bash",\
                          capture_output=read_output)

def run_functions_in_threads(functions_with_args):
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(partial(func, *args, **kwargs)) for func, args, kwargs in functions_with_args]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                raise RuntimeError(f"Function execution failed: {e}")

def run_command_list_in_threads(commands:list,as_root=False,work_dir:Path=None):
    function_list = [(_cmd,None,{"as_root":as_root,"work_dir":work_dir}) for _cmd in commands]
    return run_functions_in_threads(function_list)

def get_display_var():
    return os.environ['DISPLAY']