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
from .common import run_command_shell,WORKING_PATH,ROS2_PKGS_PATH,AssetType,run_functions_in_threads
from .arg_parser import argparse
from dataclasses import dataclass,field
from typing import List,Dict
import vcstool
import subprocess
from enum import Enum
repos_url = "https://github.com/ras-ros2/ras_vcs_repos.git"
vcs_repos_path = WORKING_PATH/'repos'
supported_assets = ["manipulator"]
supported_apps = ["robot","server"]

def get_repos_vcs():
    return VCS(vcs_repos_path,repos_url,"main")

def get_setup_vcs_mapping():
    main_vcs_mapping = parse_vcs_file(vcs_repos_path/"main.repos")
    main_vcs : VCS = main_vcs_mapping.values()[0]
    main_vcs.add_child("deps",VcsMap(vcs_repos_path/"deps.repos",WORKING_PATH,default_pull=True))
    for _asset_name in supported_assets:
        main_vcs.add_child(f"asset_{_asset_name}",VcsMap(vcs_repos_path/"resources"/f"assets/{_asset_name}s.repos",\
                                                         f"assets/{_asset_name}",default_pull=True))
    for _app_name in supported_apps:
        app_vcs_map = main_vcs.add_child(_app_name,VcsMap(vcs_repos_path/"apps"/f"ras_{_app_name}_app"/"main.repos",\
                                                          "apps",default_pull=False))
        app_vcs : VCS = app_vcs_map.vcs_map.values()[0]
        app_vcs.add_child("deps",VcsMap(vcs_repos_path/vcs_repos_path/"apps"/"deps.repos",".",default_pull=True))
    return main_vcs

class GitUrlType(Enum):
    SSH = 'ssh'
    HTTPS = 'https'

def switch_url_to(url:str,git_type:GitUrlType):
    if git_type == GitUrlType.SSH:
        if url.startswith('https://'):
            url = url.replace('https://','git@')
            url = url.replace('/', ':')
    elif git_type == GitUrlType.HTTPS:
        if url.startswith('git@'):
            url = url.replace(':', '/')
            url = url.replace('git@','https://')
    return url

def get_repo_version(repo_path:Path):
    ret = subprocess.run(f"git -C {repo_path} rev-parse --abbrev-ref HEAD",shell=True,capture_output=True)
    if ret.returncode == 0:
        version = ret.stdout.decode().strip()
    else:
        ret = subprocess.run(f"git -C {repo_path} rev-parse HEAD",capture_output=True,shell=True)
        if ret.returncode == 0:
            version = ret.stdout.decode().strip()
        else:
            raise Exception("Could not get version")
    return version

def check_url_git_type(url:str):
    if url.startswith('git@'):
        return GitUrlType.SSH
    if url.startswith('https://'):
        return GitUrlType.HTTPS
    return None

@dataclass
class VCS:
    path:str
    url:str
    version:str
    type:str = "git"
    parent: 'VCS' = None
    children: Dict[str,'VcsMap'] = field(default_factory=dict)

    @staticmethod
    def from_dict(path:str,d:dict):
        return VCS(path,d['url'],d['version'],d['type'])
    
    @staticmethod
    def from_git_repo(repo_path:Path):
        url = get_remote_url(repo_path)
        if url is None:
            return None
        version = get_repo_version(repo_path)
        return VCS(str(repo_path),url,version,"git")
    
    def to_dict(self):
        return {
            'url':self.url,
            'version':self.version,
            'type':self.type
        }
    
    def update_vcs_from_repo(self):
        if self.type == "git":
            repo_path = Path(self.path)
            self.url = get_remote_url(repo_path)
            self.version = get_repo_version(repo_path)
        else:
            raise Exception("Unsupported VCS type")
    
    def update_repo_from_vcs(self):
        if self.type == "git":
            repo_path = Path(self.path)
            set_remote_url(repo_path,self.url)
            run_command_shell(f"git -C {repo_path} checkout {self.version}")
        else:
            raise Exception("Unsupported VCS type")
        
    def switch_url_to(self,git_type:GitUrlType,write=False):
        self.url = switch_url_to(self.url,git_type)
        if write:
            subprocess.run(f"git -C {self.repo_path} remote set-url origin {self.url}",shell=True,check=True)


    @property
    def repo_path(self):
        if isinstance(self.parent,VCS):
            return Path(self.parent.repo_path)/self.path
        return Path(self.path)
    
    def import_repo(self):
        if self.type == "git":
            ret = run_command_shell(f"git clone {self.url} {self.repo_path}")
            if ret.returncode != 0:
                return False
            ret = run_command_shell(f"git -C {self.repo_path} checkout {self.version}")
            return ret.returncode == 0
        return False
    
    def pull_repo(self,switch_version=False):
        if self.type == "git":
            if switch_version:
                ret = run_command_shell(f"git -C {self.repo_path} checkout {self.version}")
                if ret.returncode != 0:
                    return False
            ret = run_command_shell(f"git -C {self.repo_path} pull")
            return ret.returncode == 0
        return False
    
    def init_repo(self):
        if self.repo_path.exists():
            self.update_repo_from_vcs()
            self.pull_repo()
        else:
            self.import_repo()
        for _v in self.children.values():
            if _v.default_pull:
                _v.init_vcs()
    
    def clear_child_repos(self):
        for _v in self.children.values():
            _v.clear_vcs()

    def switch_version(self,version:str):
        if self.type == "git":
            ret = run_command_shell(f"git -C {self.repo_path} checkout {version}")
            return ret.returncode == 0
        return False
    
    def get_branches_and_versions(self):
        if self.type == "git":
            ret = subprocess.run(f"git -C {self.repo_path} branch -a",shell=True,capture_output=True)
            if ret.returncode != 0:
                return []
            branches = []
            for _b in ret.stdout.decode().split('\n'):
                _b = _b.strip()
                if _b.startswith('*'):
                    branches.insert(0,_b[1:].strip())
                else:
                    if len(_b) > 0:
                        branches.append(_b)
            return branches
        return []
    
    def get_current_version(self):
        if self.type == "git":
            return get_repo_version(self.repo_path)
        return None
    
    def clear_repo(self):
        if self.repo_path.exists():
            run_command_shell(f"rm -rf {self.repo_path}")
    
    def new_version(self,version:str):
        if self.type == "git":
            if version in self.get_branches_and_versions():
                return self.switch_version(version)
            ret = run_command_shell(f"git -C {self.repo_path} checkout -b {version}")
            return ret.returncode == 0
        return False
    
    def add_child(self,label:str,vcs_map:'VcsMap'):
        vcs_map.parent = self
        self.children[label] = vcs_map
        return vcs_map

@dataclass
class VcsMap:
    file_path : Path
    work_dir : Path
    vcs_map : Dict[str,VCS] = None
    parent : 'VCS' = field(default=None,init=False)
    default_pull : bool = True

    def __post_init__(self):
        self.vcs_map = parse_vcs_file(self.file_path)
        for _v in self.vcs_map.values():
            _v.parent = self.parent

    def write(self):
        write_vcs_file(self.file_path,self.vcs_map)

    def switch_git_type(self,git_type:GitUrlType):
        for _v in self.vcs_map.values():
            _v.switch_url_to(git_type)
        # self.write()
    
    def get_vcs(self,path:str):
        return self.vcs_map.get(path)
    
    def add_vcs(self,path:str,vcs:VCS):
        self.vcs_map[path] = vcs
        # self.write()
    
    def remove_vcs(self,path:str):
        self.vcs_map.pop(path)
        # self.write()
    
    def import_vcs(self):
        # ret = run_command_shell(f"vcs import --recursive < {self.file_path}", work_dir=self.work_dir)
        # return ret.returncode == 0
        function_list = []
        for _v in self.vcs_map.values():
            function_list.append((_v.import_repo,None,None))
        return run_functions_in_threads(function_list)

    def pull_vcs(self):
        repos = [ _v.repo_path for _v in self.vcs_map.values()]
        ret = run_command_shell(f"vcs pull {' '.join(repos)}", work_dir=self.work_dir)
        return ret.returncode == 0
    
    def init_vcs(self):
        function_list = []
        for _v in self.vcs_map.values():
            function_list.append((_v.init_repo,None,None))
        return run_functions_in_threads(function_list)

    def clear_vcs(self):
        function_list = []
        for _v in self.vcs_map.values():
            function_list.append((_v.clear_repo,None,None))
        return run_functions_in_threads(function_list)


    
def parse_vcs_file(vcs_file:Path):
    vcs_dict = {}
    with vcs_file.open() as f:
        vcs_dict = yaml.safe_load(f)["repositories"]
    return { k:VCS.from_dict(v) for k,v in vcs_dict.items()}

def write_vcs_file(vcs_file:Path,vcs_dict:Dict[str,VCS]):
    vcs_dict = { k:v.to_dict() for k,v in vcs_dict.items()}
    with vcs_file.open('w') as f:
        yaml.dump({'repositories':vcs_dict},f)

def get_remote_url(repo_path:Path):
    ret = subprocess.run(f'git -C {repo_path} remote get-url origin',shell=True,capture_output=True)
    if ret.returncode != 0:
        return None
    return ret.stdout.decode().strip()

def set_remote_url(repo_path:Path,url:str):
    ret = run_command_shell(f'git -C {repo_path} remote set-url origin {url}')
    return ret.returncode == 0

def get_path_GitUrlType(repo_path:Path):
    url = get_remote_url(repo_path)
    if url is None:
        return None
    return check_url_git_type(url)

def set_path_GitUrlType(repo_path:Path,git_type:GitUrlType):
    url = get_remote_url(repo_path)
    if url is None:
        return False
    url = switch_url_to(url,git_type)
    return set_remote_url(repo_path,url)

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

# def init_setup(args : argparse.Namespace ):
#     repos_file = WORKING_PATH/'repos'/(f"deps.repos")
#     if repos_file.exists():
#         vcs_fetch_repos(repos_file,WORKING_PATH,pull=True)
#     assets_dir = WORKING_PATH/"assets"
#     assets_dir.mkdir(parents=True,exist_ok=True)
#     for _k,_v in AssetType._member_map_.items():
#         if not isinstance(_v.value,str):
#             continue
#         asset_dir = assets_dir/_k.lower()
#         asset_dir.mkdir(exist_ok=True,parents=True)
#         asset_repos_file = WORKING_PATH/'repos'/"resources"/"assets"/(f"{_v.value}.repos")
#         vcs_fetch_repos(asset_repos_file,asset_dir,pull=True)
#     ROS2_PKGS_PATH.mkdir(exist_ok=True,parents=True)
#     vcs_fetch_repos(WORKING_PATH/'repos'/"ros2.repos",ROS2_PKGS_PATH,pull=True)


def init_setup(args: argparse.Namespace):
    repos_vcs = get_repos_vcs()
    repos_vcs.init_repo()
    main_vcs = get_setup_vcs_mapping()
    main_vcs.init_repo()

def clear_setup(args: argparse.Namespace):
    repos_vcs = get_repos_vcs()
    repos_vcs.clear_repo()
    main_vcs = get_setup_vcs_mapping()
    main_vcs.clear_child_repos()
    

def test():
    vcs = get_repos_vcs()
    if(vcs.repo_path.exists()):
        vcs.update_vcs_from_repo()
    
