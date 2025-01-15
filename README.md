# RAS Docker Workspace

RAS Docker is the main workspace where two applications, **robot** and **server**, can be worked with seamlessly. This document provides an overview of its setup and usage.

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
rdi -h
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
rdi server -h
```

## Working with the Server Application
### 5. Initialize Server
```bash
rdi server init
```
This creates a `ras_server_app` directory under the `apps` folder.

### 6. Build the Docker Image for the Server App
```bash
rdi server build
```

### 7. Build the ROS 2 Workspace
```bash
rdi server build
```
This builds the `src` folder inside the `ros2_ws` directory present in `ras_server_app`.

### 8. Run the Server Lab
```bash
rdi server run
```
This starts the container and executes the code defined in the `run.sh` file within `ras_server_app`.

### 9. Hack into the container
```bash
rdi server dev
```
Login to the container, explore and hack your way into the application.
