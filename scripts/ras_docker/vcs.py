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
import yaml
from .common import run_command_shell,WORKING_PATH,ROS2_PKGS_PATH,AssetType
from .arg_parser import argparse

def vcs_fetch_repos(repos_file:Path,target_path:Path,pull=False):
    vcs_cmd = f"vcs import --recursive < {repos_file} "
    if pull:
        vcs_cmd += " && vcs pull . ; "
        yaml_obj = yaml.safe_load(repos_file.open())
        if not isinstance(yaml_obj,dict) or "repositories" not in yaml_obj:
            return True
        yaml_obj = yaml_obj["repositories"]
        dirs_to_pull = set()
        if isinstance(yaml_obj,dict):
            for _k,_v in yaml_obj.items():
                if 'type' in _v and _v['type'] == 'git':
                    _path = Path(_k)
                    if _path.parent != Path('.'): 
                        dirs_to_pull.add(_path.parent)
        for _d in dirs_to_pull:
            vcs_cmd += f" pushd {_d} > /dev/null ; vcs pull . ; popd > /dev/null ; "
    ret = run_command_shell(vcs_cmd, work_dir=target_path)
    return ret.returncode==0

def init_setup(args : argparse.Namespace ):
    repos_file = WORKING_PATH/'repos'/(f"deps.repos")
    if repos_file.exists():
        vcs_fetch_repos(repos_file,WORKING_PATH,pull=True)
    assets_dir = WORKING_PATH/"assets"
    assets_dir.mkdir(parents=True,exist_ok=True)
    for _k,_v in AssetType._member_map_.items():
        if not isinstance(_v.value,str):
            continue
        asset_dir = assets_dir/_k.lower()
        asset_dir.mkdir(exist_ok=True,parents=True)
        asset_repos_file = WORKING_PATH/'repos'/"resources"/"assets"/(f"{_v.value}.repos")
        vcs_fetch_repos(asset_repos_file,asset_dir,pull=True)
    ROS2_PKGS_PATH.mkdir(exist_ok=True,parents=True)
    vcs_fetch_repos(WORKING_PATH/'repos'/"ros2.repos",ROS2_PKGS_PATH,pull=True)
