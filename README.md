# RAS Docker Workspace

RAS Docker is the main workspace where two applications, **robot** and **server**, can be worked with seamlessly. This document provides an overview of its setup and usage.


>Currently Ubuntu is officially supported distro for RAS

## Prequisites to use RAS

Before using RAS, ensure that you have the following dependencies installed:

1. **Vcstool** - A command-line tool for managing multiple repositories in ROS2 workspaces.

```bash
python3 -m pip install vcstool
```

2. **Docker-CE** - The community edition of Docker for containerized application management and Nvidia Container Toolkit if device has Nvidia GPU.

- [Docker](https://docs.docker.com/engine/install/ubuntu/)

- [Nvidia Contianer Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)

3. **Argcomplete** - A Python package that provides tab completion for command-line programs.

```bash
sudo apt install python3-argcomplete
```

4. **Git** - A version control system used for tracking changes in source code.

```bash
sudo apt install git
```


## 1. Clone the Repository
```bash
git clone --recursive https://github.com/ras-ros2/ras_docker
```

## RAS Docker Interface (RDI)
RAS Docker includes a command-line utility called **RDI** (RAS Docker Interface), implemented in `docker_interface.py` under the `scripts` directory.

### 2. Source the Environment File
```bash
source ./ras_docker/env.sh
```

### 3. Check Available Commands
To see the available RDI commands, run:
```bash
ras -h
```

## Directory Structure
### `apps` Directory
The `apps` directory houses the two applications, **server** and **robot**, which are Docker containers built using the Docker images located in the `context` directory.

### `context` Directory
The `context` directory contains the Docker images used to build the applications:
1. **Dockerfile.base**: Based on the `humble-desktop-full` image, it installs dependencies common to both applications (e.g., `python3-pip`).
2. **Dockerfile.server**: Extends `Dockerfile.base` and adds dependencies specific to the **server** application (e.g., `ignition-fortress`).
3. **Dockerfile.robot**: Extends `Dockerfile.base` and adds dependencies specific to the **robot** application.

### 4. Check App-Specific Commands
To see commands specific to an application (e.g., `server`):
```bash
ras server -h
```

## Working with the Server Application
### 5. Initialize Server
```bash
ras server init
```
This creates a `ras_server_app` directory under the `apps` folder.

### 6. Build the Docker Image for the Server App
```bash
ras server build
```

### 7. Build the ROS 2 Workspace
```bash
ras server build
```
This builds the `src` folder inside the `ros2_ws` directory present in `ras_server_app`.

### 8. Run the Server Lab
```bash
ras server run
```
This starts the container and executes the code defined in the `run.sh` file within `ras_server_app`.

### 9. Hack into the container
```bash
ras server dev
```
Login to the container, explore and hack your way into the application.
