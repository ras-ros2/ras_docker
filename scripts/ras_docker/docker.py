from .common import Path,partial,get_display_var,subprocess,ROS2_PKGS_PATH,get_docker_cmd_fmt,DockerCmdType
import json
from dataclasses import dataclass
import os

DOCKERHUB_REPO = "rasros2temp/ras"
TAG_SUFFIX = "ras_local"

@dataclass
class CoreDockerConf:
    """
    Data class to store core Docker configuration.

    Attributes:
        image_name (str): The name of the Docker image.
        container_name (str): The name of the Docker container.
        work_dir (str): The working directory inside the container.
    """
    image_name: str
    container_name: str
    work_dir: str

def docker_check_image_exists(image_tag: str):
    """
    Check if a Docker image with the given tag exists locally.

    Args:
        image_tag (str): The tag of the Docker image.

    Returns:
        bool: True if the image exists, False otherwise.
    """
    image_exists = False
    images = subprocess.check_output(["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"]).decode("utf-8").splitlines()
    if image_tag in images:
        image_exists = True
        image_id = subprocess.check_output(["docker", "images", "--format", "{{.ID}}", "--filter", f"reference={image_tag}"]).decode("utf-8").strip()
        print(f"Older Image ID: {image_id}")
        print(f"Found Docker Image: {image_tag}")
    return image_exists

def docker_pull_image(image_tag: str):
    """
    Pull a Docker image from a remote repository.

    Args:
        image_tag (str): The tag of the Docker image to pull.

    Returns:
        bool: True if the pull was successful, False otherwise.
    """
    ret = subprocess.run(f"docker pull {image_tag}", shell=True)
    return ret.returncode == 0

def pull_from_docker_repo(image_context: str, force=False):
    """
    Pull and tag a Docker image from the DockerHub repository.

    Args:
        image_context (str): The context/tag of the Docker image.
        force (bool, optional): Whether to force the pull even if the image exists. Defaults to False.
    """
    image_tag_local = f"{image_context}:ras_local"
    image_tag_remote = f"{DOCKERHUB_REPO}:{image_context}"
    if force or (not docker_check_image_exists(image_tag_remote)):
        print(f"Pulling Image: {image_tag_remote}")
        if not docker_pull_image(image_tag_remote):
            print(f"Error: Image {image_tag_remote} not found")
            exit(1)
        subprocess.run(f"docker tag {image_tag_remote} {image_tag_local}", shell=True)
    else:
        print(f"Image {image_tag_remote} already exists")

def check_container_already_running(container_name):
    """
    Check if a Docker container is currently running.

    Args:
        container_name (str): The name of the Docker container.

    Returns:
        bool: True if the container is running, False otherwise.
    """
    command = ["docker", "ps", "--format", "{{.Names}}"]
    output = subprocess.check_output(command).decode("utf-8")
    return container_name in output

def regen_docker_fmt(docker_cmd_fmt, core_conf: CoreDockerConf, allow_login=False):
    """
    Regenerate the Docker command format with updated configuration.

    Args:
        docker_cmd_fmt (Callable): The Docker command format function.
        core_conf (CoreDockerConf): The Docker configuration.
        allow_login (bool, optional): Whether to allow attaching to running containers. Defaults to False.

    Returns:
        Callable: A partial function for Docker command formatting, or None if blocked.
    """
    if check_container_already_running(core_conf.container_name):
        if not allow_login:
            print(f"Container {core_conf.container_name} is already running")
            print("This command is not allowed to run on a running container")
            return None
        else:
            docker_cmd_fmt = get_docker_cmd_fmt(DockerCmdType.ATTACH)
    docker_cmd_fmt_new = partial(docker_cmd_fmt,
                                 container_name=core_conf.container_name,
                                 work_dir=core_conf.work_dir,
                                 image_name=core_conf.image_name)
    return docker_cmd_fmt_new

def run_image_command_core(docker_command_fmt, command_str, as_root=False):
    """
    Execute a command inside a Docker container.

    Args:
        docker_command_fmt (Callable): The formatted Docker command.
        command_str (str): The command to run inside the container.
        as_root (bool, optional): Whether to run the command as root. Defaults to False.

    Returns:
        bool: True if the command ran successfully, False otherwise.
    """
    os.system("xhost +local:root")
    user_id = 1000
    if as_root:
        user_id = 0
    docker_cmd = docker_command_fmt(
        user_id=user_id,
        command=command_str
    )
    assert isinstance(docker_cmd, str)
    _cmd_elems = []
    for _elem in docker_cmd.split(" "):
        _elem = _elem.strip()
        if len(_elem) > 0:
            _cmd_elems.append(_elem)
    print(f"Running Docker Command: {' '.join(_cmd_elems)}")
    ret = subprocess.run(docker_cmd, shell=True)
    return ret.returncode == 0

def kill_docker_container(container_name):
    """
    Kill a running Docker container by name.

    Args:
        container_name (str): The name of the Docker container to kill.
    """
    if check_container_already_running(container_name):
        print(f"Killing Container: {container_name}")
        subprocess.run(f"docker kill {container_name}", shell=True)
    else:
        print(f"Container {container_name} is not running")
