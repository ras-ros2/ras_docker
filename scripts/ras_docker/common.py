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
    """
    Enum for defining different asset types used in the system.
    """
    NONE = None
    LAB = "labs"
    MANIPULATOR = "manipulators"

class DockerCmdType(Enum):
    """
    Enum for specifying types of Docker commands to be used.
    """
    NONE = None
    FULL = 1
    RAW = 2
    ATTACH = 3

import re
from string import Formatter

def parse_with_format(format_string, input_string):
    """
    Parses an input string using a Python format string template.

    Args:
        format_string (str): The format string with named fields.
        input_string (str): The actual string to be parsed.

    Returns:
        dict: A dictionary mapping field names to parsed values.

    Raises:
        ValueError: If the input string does not match the format string.
    """
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

def is_wsl():
    """
    Checks if the current environment is a Windows Subsystem for Linux (WSL).

    Returns:
        bool: True if running in WSL, False otherwise.
    """
    return Path("/proc/sys/fs/binfmt_misc/WSLInterop").exists()

def get_docker_cmd_fmt(cmd_type: DockerCmdType):
    """
    Generates a Docker command format string or callable depending on the Docker command type.

    Args:
        cmd_type (DockerCmdType): The type of Docker command to generate.

    Returns:
        function: A partial function that can be called with required parameters to format a Docker command.

    Raises:
        ValueError: If the Docker command type is invalid or unexpected.
    """
    docker_cmd_fmt_prefix = """docker run -it \
                -e DISPLAY={display_env} \
                -e APP_TYPE={app_type} \
                --user {user_id}:{user_id} \
                -v /etc/localtime:/etc/localtime:ro \
                --name {container_name} \
                --workdir {work_dir} \
                --network host """
    passthrough_mounts = ["/tmp/.X11-unix","/mnt/wslg"]
    passthrough_envvars = ["WAYLAND_DISPLAY","XDG_RUNTIME_DIR"]
    docker_gen_cmd_opts = """ -v {app_dir}:/{container_name}/ \
                            {extra_docker_args} -v /var/run/docker.sock:/var/run/docker.sock \
                                {gpu_arg} \
                                 -v /dev:/dev --device-cgroup-rule='c 13:* rmw' --device-cgroup-rule 'c 81:* rmw' \
                            --device-cgroup-rule 'c 189:* rmw' """ + f" -v {ROS2_PKGS_PATH}:/{{container_name}}/ros2_ws/src/common_pkgs "
    docker_cmd_fmt_suffix= """ {image_name} \
                {command} """
    docker_cmd_fmt = None
    for _dir in passthrough_mounts:
        _path = Path(_dir).absolute().resolve()
        if _path.is_dir():
            docker_gen_cmd_opts += f" -v {_path}:{_path} "
    for _env in passthrough_envvars:
        if _env in os.environ.keys():
            docker_gen_cmd_opts += f" -e {_env} "
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
                gpu_arg= docker_gpu_arg,
                app_type=os.environ.get("APP_TYPE", "robot")
            )
    elif (cmd_type==DockerCmdType.RAW):
        return partial(docker_cmd_fmt,
                display_env=get_display_var()
            )
    else:
        raise ValueError(f"Unexpected docker cmd_type{cmd_type}")

def prepend_root_command(command_str:str):
    """
    Wraps a shell command string with `sudo` to execute it as root.

    Args:
        command_str (str): The original shell command.

    Returns:
        str: The command wrapped for sudo execution.
    """
    return f"sudo -E bash -c '{command_str}'"

def run_command_shell(command_str:str,as_root:bool=False,work_dir:Path=None,read_output=False,preview=True):
    """
    Executes a shell command using subprocess.

    Args:
        command_str (str): The command to execute.
        as_root (bool): If True, runs the command as root.
        work_dir (Path): Optional working directory.
        read_output (bool): If True, captures the output.
        preview (bool): If True, prints the command before execution.

    Returns:
        CompletedProcess: The result of subprocess.run.
    """
    if isinstance(work_dir,Path):
        work_dir = str(work_dir)
    if as_root:
        command_str = prepend_root_command(command_str)
    if preview:
        print("Running Command:",command_str)
    return subprocess.run(command_str,shell=True,cwd=work_dir,executable="/bin/bash",\
                          capture_output=read_output)

def run_functions_in_threads(functions_with_args):
    """
    Runs multiple functions in parallel using threads.

    Args:
        functions_with_args (list): List of tuples (function, args, kwargs).

    Raises:
        RuntimeError: If any function raises an exception.
    """
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(partial(func, *args, **kwargs)) for func, args, kwargs in functions_with_args]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                raise RuntimeError(f"Function execution failed: {e}")

def run_command_list_in_threads(commands:list,as_root=False,work_dir:Path=None):
    """
    Executes a list of shell commands in parallel threads.

    Args:
        commands (list): List of shell command strings.
        as_root (bool): Whether to run commands as root.
        work_dir (Path): Optional working directory.

    Returns:
        None
    """
    function_list = [(_cmd,None,{"as_root":as_root,"work_dir":work_dir}) for _cmd in commands]
    return run_functions_in_threads(function_list)

def get_display_var():
    """
    Retrieves the DISPLAY environment variable.

    Returns:
        str: The value of DISPLAY from the environment.
    """
    return os.environ['DISPLAY']
