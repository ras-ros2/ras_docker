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

WORKING_PATH = Path(os.environ["RAS_DOCKER_PATH"])
ROS2_PKGS_PATH = WORKING_PATH/"ros2_pkgs"

WORKSPACE_BUILD_CMD = "colcon build --symlink-install"

class AssetType(Enum):
    NONE = None

    LAB = "labs"
    MANIPULATOR = "manipulators"

def prepend_root_command(command_str:str):
    return f"sudo -E bash -c '{command_str}'"

def run_command_shell(command_str:str,as_root:bool=False,work_dir:Path=None):
    if isinstance(work_dir,Path):
        work_dir = str(work_dir)
    if as_root:
        command_str = prepend_root_command(command_str)
    return subprocess.run(command_str,shell=True,cwd=work_dir,executable="/bin/bash")

def get_display_var():
    return os.environ['DISPLAY']