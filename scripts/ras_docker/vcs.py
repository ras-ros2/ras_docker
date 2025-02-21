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
from .common import run_command_shell,WORKING_PATH,ROS2_PKGS_PATH,AssetType,run_functions_in_threads,parse_with_format
from .arg_parser import argparse
from dataclasses import dataclass,field
from typing import List,Dict,ClassVar
import vcstool
import subprocess
from enum import Enum
repos_url = "https://github.com/ras-ros2/ras_vcs_repos.git"
vcs_repos_path = WORKING_PATH/'repos'
supported_assets = ["manipulator"]
supported_apps = ["robot","server"]

def get_repos_vcs():
    return VCS(vcs_repos_path,repos_url,"dev")

def get_setup_vcs_mapping():
    if not vcs_repos_path.exists():
        return VCS.from_git_repo(WORKING_PATH)
    main_vcs_mapping = parse_vcs_file(vcs_repos_path/"main.repos",WORKING_PATH.parent)
    main_vcs : VCS = next(iter(main_vcs_mapping.values()))
    main_vcs.add_child("deps",VcsMap(vcs_repos_path/"common.repos",WORKING_PATH/"ros2_pkgs",default_pull=True))
    for _asset_name in supported_assets:
        main_vcs.add_child(f"asset_{_asset_name}",VcsMap(vcs_repos_path/"resources"/f"assets/{_asset_name}s.repos",\
                                                         f"assets/{_asset_name}",default_pull=True))
    for _app_name in supported_apps:
        app_vcs_map = main_vcs.add_child(_app_name,VcsMap(vcs_repos_path/"apps"/f"ras_{_app_name}_app"/"main.repos",\
                                                          "apps",default_pull=False))
        app_vcs_map.vcs_map[f"ras_{_app_name}_app"].add_child("deps",VcsMap(vcs_repos_path/"apps"/f"ras_{_app_name}_app"/"deps.repos",".",default_pull=True))


    return main_vcs


class GitUrlType(Enum):
    SSH = "git@{hostname}:{org_name}/{repo_name}"
    HTTPS = "https://{hostname}/{org_name}/{repo_name}"


def switch_url(url:str,git_type:GitUrlType=None):
    remote = VcsRemote.from_url(url)
    if git_type:
        remote.url_type = git_type
        return remote.get_url()
    else:
        return remote.get_url(reformed=True)

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
    return VcsRemote.from_url(url).url_type



@dataclass
class VCS(object):
    path:str
    url:str
    version:str
    type:str = "git"
    parent: 'VCS' = None
    children: Dict[str,'VcsMap'] = field(default_factory=dict)

    @property
    def reformed_url(self):
        return VcsRemote.from_url(self.url).get_url(reformed=True)
    
    def reform_repo_url(self):
        set_remote_url(self.repo_path,self.reformed_url)

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
            repo_path = Path(self.repo_path)
            self.url = get_remote_url(repo_path)
            self.version = get_repo_version(repo_path)
        else:
            raise Exception("Unsupported VCS type")
        
    def print_status(self,fetch=False,children=False):
        if self.is_repo_path_valid():
            if fetch:
                try:
                    run_command_shell(f"git -C {self.repo_path} fetch")
                except:
                    pass
            run_command_shell(f"git -C {self.repo_path} status")
        else:
            if self.repo_path.exists():
                print(f"{self.repo_path} is corrupted! Cannot get status")
            else:
                print(f"{self.repo_path} is not set up. ")
        if children:
            for _child in self.iterate_children(log=True):
                _child.print_status(fetch=fetch,children=children)
    
    def update_repo_from_vcs(self):
        if self.type == "git":
            repo_path = Path(self.repo_path)
            set_remote_url(repo_path,self.reformed_url)
            run_command_shell(f"git -C {repo_path} checkout {self.version}")
        else:
            raise Exception("Unsupported VCS type")
    
    def iterate_children(self,log=False):
        for _child in self.children.values():
            if log:
                print(f"currently on {_child.work_dir}")
            yield _child
        
    def switch_url(self,git_type:GitUrlType=None,write=False):
        # print(f"switch url {self.repo_path}")
        self.url = switch_url(self.url,git_type)
        if write and self.repo_path.exists():
            if not self.is_repo_path_valid():
                raise ValueError(f"Repo path {self.repo_path} is invalid")
            subprocess.run(f"git -C {self.repo_path} remote set-url origin {self.url}",shell=True,check=True)
        for _child in self.iterate_children(log=False):
            _child.switch_git_type(git_type,write)

    def is_repo_path_valid(self):
        if self.type == "git":
            repo_path = Path(self.repo_path)
            if repo_path.exists():
                if (repo_path/".git").exists():
                    url = get_remote_url(repo_path)
                    return VcsRemote.from_url(url).is_same_remote(VcsRemote.from_url(self.url))
        return False
    @property
    def repo_path(self):
        if isinstance(self.parent,VCS):
            return Path(self.parent.repo_path)/self.path
        return Path(self.path)
    
    def import_repo(self):
        if self.type == "git":
            ret = run_command_shell(f"git clone --recursive {self.reformed_url} -b {self.version} {self.repo_path}")
            if ret.returncode != 0:
                return False
            ret = run_command_shell(f"git -C {self.repo_path} checkout --recurse-submodules {self.version}")
            return ret.returncode == 0
        return False
    
    def pull_repo(self,switch_version=False):
        if self.type == "git":
            if switch_version:
                ret = run_command_shell(f"git -C {self.repo_path} checkout --recurse-submodules {self.version}")
                if ret.returncode != 0:
                    return False
            ret = run_command_shell(f"git -C {self.repo_path} pull")
            return ret.returncode == 0
        return False
    
    def init_repo(self,from_repo=False):
        # print(self.repo_path,from_repo)
        self_init_status  = True
        if self.repo_path.exists():
            if not self.is_repo_path_valid():
                raise Exception(f"Invalid repo path {self.repo_path}")
            if from_repo:
                self.update_vcs_from_repo()
            else:
                self.update_repo_from_vcs()
            self_init_status = self.pull_repo()
        else:
            self_init_status = self.import_repo()
        if self_init_status:
            for _v in self.iterate_children(log=True):
                if _v.default_pull:
                    _v.init_vcs(from_repo=from_repo)
                elif _v.absoulte_work_dir.exists():
                    _v.init_vcs(from_repo=from_repo)
        return self_init_status
            
    
    def clear_child_repos(self):
        for _v in self.iterate_children(log=True):
            _v.clear_vcs()

    def switch_version(self,version:str):
        if self.type == "git":
            ret = run_command_shell(f"git -C {self.repo_path} checkout --recurse-submodules {version}")
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
        # vcs_map.parent = self
        self.children[label] = VcsMap(vcs_map.file_path,vcs_map.work_dir,default_pull=vcs_map.default_pull,parent=self)
        return self.children[label]

@dataclass
class VcsMap:
    file_path : Path
    work_dir : Path
    vcs_map : Dict[str,VCS] = None
    parent : 'VCS' = field(default=None)
    default_pull : bool = True

    def __post_init__(self):
        if isinstance(self.vcs_map,type(None)):
            self.vcs_map = parse_vcs_file(self.file_path,Path(self.work_dir))
        for _v in self.iterate_vcs(log=False):
            _v.parent = self.parent

    def write(self):
        write_vcs_file(self.file_path,self.vcs_map)
    
    @property
    def absoulte_work_dir(self):
        if isinstance(self.parent,VCS):
            return Path(self.parent.repo_path)/self.work_dir
        return self.work_dir

    def switch_git_type(self,git_type:GitUrlType=None,write=False):
        for _v in self.iterate_vcs(log=False):
            if _v.repo_path.exists():
                _v.switch_url(git_type,write)
            else:
                _v.switch_url(git_type)
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
        for _v in self.iterate_vcs(log=True):
            function_list.append((_v.import_repo,[],{}))
        return run_functions_in_threads(function_list)

    def pull_vcs(self):
        repos = [ _v.repo_path for _v in self.iterate_vcs(log=True)]
        ret = run_command_shell(f"vcs pull {' '.join(repos)}", work_dir=self.work_dir)
        return ret.returncode == 0
    
    def print_status(self,fetch=False,children=False):
        for _v in self.iterate_vcs(log=True):
            _v.print_status(fetch=fetch,children=children)
            
    def init_vcs(self,from_repo=False):
        function_list = []
        for _v in self.iterate_vcs():
            function_list.append((_v.init_repo,[],{"from_repo":from_repo}))
        try:
            run_functions_in_threads(function_list)
        except Exception as e:
            print(f"Error in init_vcs: {e}")
            return False
        for _v in self.iterate_vcs():
            if not _v.is_repo_path_valid():
                return False
        return True

    def clear_vcs(self):
        function_list = []
        for _v in self.iterate_vcs():
            function_list.append((_v.clear_repo,[],{}))
        return run_functions_in_threads(function_list)
    
    def iterate_vcs(self,log=False):
        for _v in self.vcs_map.values():
            if log:
                print(f"working on {_v.repo_path}")
            yield _v


def parse_vcs_file(vcs_file:Path,parent_path:Path=None):
    vcs_dict = {}
    with vcs_file.open() as f:
        vcs_dict = yaml.safe_load(f)["repositories"]
    ret_dict = {}
    for k,v in vcs_dict.items():
        path = k
        if not isinstance(parent_path,type(None)):
            path = parent_path/k
        ret_dict[k] = VCS.from_dict(path,v)
    return ret_dict

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
    print(f"Switch url {repo_path}")
    ret = run_command_shell(f'git -C {repo_path} remote set-url origin {url}')
    return ret.returncode == 0

def get_path_GitUrlType(repo_path:Path):
    url = get_remote_url(repo_path)
    if url is None:
        return None
    return check_url_git_type(url)

def set_path_GitUrlType(repo_path:Path,git_type:GitUrlType=None):
    url = get_remote_url(repo_path)
    if url is None:
        return False
    url = switch_url(url,git_type)
    return set_remote_url(repo_path,url)


class RemoteMeta(type):
    def __init__(cls,name,bases,dct):
        super().__init__(name,bases,dct)
        cls.url_mode = GitUrlType.HTTPS
        setup_path = get_setup_vcs_mapping().repo_path
        cls.url_mode = get_path_GitUrlType(setup_path)
    

    # def get_reformed_url(cls,url):
@dataclass
class VcsRemote(object):
    url_mode : ClassVar[GitUrlType] = GitUrlType.HTTPS
    url_type : GitUrlType
    hostname : str
    org_name : str
    repo_name : str

    @classmethod
    def init(cls):
        setup_repo = get_setup_vcs_mapping()
        setup_repo.update_vcs_from_repo()
        if setup_repo.is_repo_path_valid():
            setup_repo.update_vcs_from_repo()
            cls.url_mode = VcsRemote.from_url(setup_repo.url).url_type

    @classmethod
    def set_url_mode(cls,mode:GitUrlType):
        if not isinstance(mode,GitUrlType):
            raise ValueError(f"Invalid modetype {type(mode)}")
        if mode==cls.url_mode:
            return
        cls.url_mode = mode
        setup_repo = get_setup_vcs_mapping()
        setup_repo.update_vcs_from_repo()
        if setup_repo.is_repo_path_valid():
            setup_repo.switch_url(None,write=True)

    def __post_init__(self):
        if (self.repo_name.endswith(".git")):
            self.repo_name = self.repo_name[:-4]


    def get_url(self,reformed=False):
        if reformed:
            return VcsRemote(
                url_type=VcsRemote.url_mode,
                hostname=self.hostname,
                org_name=self.org_name,
                repo_name=self.repo_name).get_url()
        return self.url_type.value.format_map(self.__dict__)
    
    
    @staticmethod
    def from_url(url : str):
        url_type : GitUrlType
        _except = None
        for url_type in GitUrlType._member_map_.values():
            try:
                parsed_dict = parse_with_format(url_type.value,url)
                return VcsRemote(
                    url_type=url_type,
                    **parsed_dict
                )
            except Exception as e:
                _except = e
        raise ValueError(f"No way to form remote from url {url}: {_except}")

    def is_same_remote(self,other:'VcsRemote'):
        return (self.repo_name==other.repo_name) and\
                (self.org_name==other.org_name) and\
                (self.hostname==other.hostname)
    
    
VcsRemote.init()



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
    status = True
    repos_vcs = get_repos_vcs()
    status = repos_vcs.init_repo(from_repo=True)
    if not status:
        return False
    main_vcs = get_setup_vcs_mapping()
    status = main_vcs.init_repo(from_repo=False)
    if not status:
        return False
    return True

def pull_repos_vcs(args: argparse.Namespace):
    repos_vcs = get_repos_vcs()
    repos_vcs.update_vcs_from_repo()
    if args.version:
        repos_vcs.switch_version(args.version)
    repos_vcs.pull_repo(switch_version=False)
    return repos_vcs.get_current_version()

def repos_vcs_version(args: argparse.Namespace):
    repos_vcs = get_repos_vcs()
    repos_vcs.update_vcs_from_repo()
    if args.version:
        repos_vcs.pull_repo()
        repos_vcs.switch_version(args.version)
        main_vcs = get_setup_vcs_mapping()
        main_vcs.init_repo(from_repo=False)
        # return args.version
    print(repos_vcs.get_branches_and_versions())
    
    return repos_vcs.get_current_version()

def init_app_setup(args: argparse.Namespace):
    main_vcs = get_setup_vcs_mapping()
    main_vcs.update_vcs_from_repo()
    return main_vcs.children[args.app].init_vcs(from_repo=False)

def get_vcs_status(args: argparse.Namespace):
    main_vcs = get_setup_vcs_mapping()
    main_vcs.update_vcs_from_repo()
    fetch_vcs=False
    if hasattr(args,"fetch") and args.fetch:
        fetch_vcs=True
    main_vcs.print_status(fetch=fetch_vcs,children=True)

def clear_setup(args: argparse.Namespace):
    main_vcs = get_setup_vcs_mapping()
    main_vcs.clear_child_repos()
    repos_vcs = get_repos_vcs()
    repos_vcs.clear_repo()

    
def url_mode(args: argparse.Namespace):
    if isinstance(args.url_mode,str):
        url_mode = args.url_mode.upper()
        if url_mode in GitUrlType._member_names_:
            VcsRemote.set_url_mode(GitUrlType._member_map_[url_mode])
        else:
            print(f"Invalid url_mode {url_mode}")
    print(f"Current url-mode: {VcsRemote.url_mode.name.lower()}")
    



def test():
    remote = VcsRemote.from_url("https://github.com/ras-ros2/ras_docker.git")
    ssh_remote = VcsRemote.from_url("git@github.com:ras-ros2/ras_docker")
    print(remote.is_same_remote(ssh_remote))
    print(remote)
    print(ssh_remote)
    print(ssh_remote.get_url())
    reformed = ssh_remote.get_url(reformed=True)
    print(reformed)
    new_remote = VcsRemote.from_url(reformed)
    print(new_remote)
    print(new_remote == remote)
    
    
