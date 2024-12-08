# OSS Docker Workspace

OSS Docker is the main workspace where two applications, **real** and **sim**, can be worked with seamlessly. This document provides an overview of its setup and usage.

## 1. Clone the Repository
```bash
git clone --recursive https://github.com/ras-ros2/oss_docker
```

## OSS Docker Interface (ODI)
OSS Docker includes a command-line utility called **ODI** (OSS Docker Interface), implemented in `docker_interface.py` under the `scripts` directory.

### 2. Source the Environment File
```bash
source env.sh
```

### 3. Check Available Commands
To see the available ODI commands, run:
```bash
odi -h
```

## Directory Structure
### `apps` Directory
The `apps` directory houses the two applications, **sim** and **real**, which are Docker containers built using the Docker images located in the `context` directory.

### `context` Directory
The `context` directory contains the Docker images used to build the applications:
1. **Dockerfile.base**: Based on the `humble-desktop-full` image, it installs dependencies common to both applications (e.g., `python3-pip`).
2. **Dockerfile.sim**: Extends `Dockerfile.base` and adds dependencies specific to the **sim** application (e.g., `ignition-fortress`).
3. **Dockerfile.real**: Extends `Dockerfile.base` and adds dependencies specific to the **real** application.

### 4. Check App-Specific Commands
To see commands specific to an application (e.g., `sim`):
```bash
odi sim -h
```

## Working with the Sim Application
### 5. Initialize Sim
```bash
odi sim init
```
This creates a `oss_sim_lab` directory under the `apps` folder.

### 6. Build the Docker Image for the Sim App
```bash
odi sim build
```

### 7. Build the ROS 2 Workspace
```bash
odi sim build
```
This builds the `src` folder inside the `ros2_ws` directory present in `oss_sim_lab`.

### 8. Run the Sim Lab
```bash
odi sim run
```
This starts the container and executes the code defined in the `run.sh` file within `oss_sim_lab`.

