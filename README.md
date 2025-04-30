# RAS Docker Walkthrough

This document provides a comprehensive walkthrough of the RAS Docker environment structure and functionality. Use this guide to navigate the codebase and understand how to use the system.

## Directory Structure
```
.
├── apps                   # Contains application-specific code
│   ├── ras_robot_app      # Robot controller application
│   └── ras_server_app     # Server application for remote control and monitoring
├── assets                 # Static assets (images, 3D models, etc.)
├── configs                # Configuration files for the system
│   ├── experiments        # Robot experiment definitions
│   ├── lab_setup.yaml     # Laboratory environment configuration
│   ├── objects.yaml       # Object definitions for manipulation
│   └── ras_conf.yaml      # Main RAS system configuration
├── context                # Docker context files
├── repos                  # External repositories and dependencies
├── ros2_pkgs              # ROS2 packages for robot control
│   ├── ras_bt_framework   # Behavior Tree framework for task execution
│   ├── ras_core_pkgs      # Core ROS2 packages for robot functionality
│   └── ras_sim            # Simulation environment packages
├── scripts                # Utility scripts for various tasks
└── env.sh                 # Environment setup script
```
---
## Prerequisites
Before starting, ensure your system has the following installed:

1. **Ubuntu OS** (RAS officially supports Ubuntu)
2. **Git** (To download the required files)
   ```bash
   sudo apt install git
   ```
3. **Docker** (For running applications in containers)
   ```bash
   sudo apt install docker.io
   ```
   or

   [Docker](https://docs.docker.com/engine/install/ubuntu/)
  
   Verify Docker installation:
   - run the following command to check for the `docker installation`:
   ```bash
   docker
4. **Nvidia Container Toolkit** (If your system have nvidia GPU installed)

   Check for Nvidia GPU,
   ```bash
   nvidia-smi
   ```
   If not installed, it will show versions to install the nvidia drivers.
   
   If already have then run the following command to install nvidia container toolkit.
   ```bash
   sudo apt-get install -y nvidia-container-toolkit
   ```
6. **vcstool** (For managing repositories)
   ```bash
   python3 -m pip install vcstool
   ```
   If pip is not installed:
   ```bash
   sudo apt install python3-pip
   ```
7. **Argcomplete** (For auto-completing commands)
   ```bash
   sudo apt install python3-argcomplete
   ```
8. **Stable Internet Connection** (Required to pull Docker images properly)
9. **xArm Robotic Manipulator** (With Dedicated Desktop Setup for Robot Setup)
10. **Robot Hardware Connection** (For Robot Desktop Setup)
   Use an Ethernet cable to connect the robot and your PC.
   Default IP of xArm: `192.168.1.111`

   Set Manual Ethernet IP Address:
   1. Go to **Settings → Network → Ethernet → IPv4**
   2. Select **Manual** and enter:
      - **IP Address**: `192.168.1.78` (or any IP in the xArm's subnet)
      - **Subnet Mask**: `255.255.255.0`

   ![IP_settings](images/ip_settings.png)

   Check connection:
   ```bash
   ping 192.168.1.111
   ```
   If packets are sent and received successfully, the connection is established.   
   
---
## Installation

### Step 1: Clone the Repository
Download the RAS Docker workspace files by running:
```bash
git clone --recursive https://github.com/ras-ros2/ras_docker
```
---
### Step 2: Set Up Environment
Go inside the `ras_docker` folder and set up the environment:
```bash
cd ras_docker
```
Source the environment using the following command:
```bash
. env.sh
```
---
### Step 3: Check Available Commands
List available commands for the RAS Docker Interface (RDI):
```bash
ras -h
```
---
### Step 4: Initialize the App
Set up the application:
```bash
ras <app> init
```
`Note:` If the internet is unstable, this command may build the image locally. Run the following command to force pull the image from DockerHub:
```bash
ras <app> init -i
```
This creates the `ras_server_app/ras_robot_app` folder inside the `apps` directory.

---
### Step 5: Build the Application
Build the application:
```bash
ras <app> build
```
This command will build 
- the necessary Docker image for the server.
- the ROS 2 workspace inside the ras_server_app/ros2_ws and ras_robot_app/ros2_ws directory.
If the ROS 2 workspace is not built then run it again.

`Note:` If you've downloaded new images or updated an existing one, make sure to clean the build before rebuilding:
```bash
ras <app> build --clean
```
---
### Step 6: Configure the Network
Before running the <app>, configure `ras_conf.yaml`:
```bash
nano ras_docker/configs/ras_conf.yaml
```
Update transport settings based on your network setup:
### Default: 
Running on the Same Machine (Localhost)
```yaml
ras:
  transport:
    implementation: default
    file_server:
      use_external: false
      ip: localhost
      port: 2122
    mqtt:
      use_external: false
      ip: localhost
      port: 2383
```
For more examples, see [Network Configuration Setup README](Network_configuration_setup_readme.md).

---
### Step 7: Run the App
Start the app inside a Docker container:
```bash
ras <app> run
```
For more details, see [Applications README](tmux_tabs_readme.md).

---
### Step 8: Access the Container
To log into the running <app> container:
```bash
ras <app> dev
```
To exit:
```bash
exit
```
or press `Ctrl + D`.

---
### Step 9: Kill the App
To stop the app, use:
```bash
ras_kill
```
### Done!
Your app is now set up and running. If you face any issues:
- Follow the troubleshooting steps provided.
- Restart your system.
- For docker troubleshooting, [Docker Network and Configuration README](docker_setup_troubleshoot_readme.md).
- For GUI interaction, [UFactory Studio README](UFactory_Studio_App_readme.md).
- Refer this [RAS Server Setup README](RAS_Server_Setup_readme.md). for complete Server Setup.
- Refer this [RAS Robot Setup README](RAS_Robot_Setup_readme.md). for complete Server Setup.
  
For further assistance, refer to the documentation or raise an issue on the project repository.



# Experiment Creation Guide

## Overview

This guide explains how to create an experiment using the RAS framework from scratch. It covers defining poses, grid layouts, object dimensions, locations, and actions using YAML files. Additionally, it details the available primitives and how they map to robot actions, enabling structured behavior execution for robotic arms like xArm.

## Workspace Dimensions for xArm Lite

The xArm Lite 6 has the following workspace dimensions:

- **X (Forward-Backward):** Approximately -0.44 m to +0.44 m
- **Y (Left-Right):** Approximately -0.44 m to +0.44 m
- **Z (Up-Down):** Approximately 0 m to +0.55 m

All defined poses should fall within these limits to ensure valid robot operation.

## Setting Up an Experiment

### Step 1: Define Poses

Poses define key locations for the robot to move to. Each pose includes position (x, y, z) and orientation (roll, pitch, yaw).

### Step 2: Define Grid Layout

Grids define structured locations for object placement.

### Step 3: Define Object Locations

Each object can be associated with a grid and a specific location.


## Available Primitives
RAS provides pre-defined primitive actions for robotic manipulation.

### Movement Primitives
- **MoveToPose**: Moves the robot to a predefined pose.
- **MoveToJointState**: Moves the robot to a predefined joint state.
- **ExecuteTrajectory**: Executes a predefined motion sequence.

### Interaction Primitives
- **Trigger**: Triggers a binary state change.
- **RotateEffector**: Rotates the end-effector by a given angle.
- **SaySomething**: Outputs a message.
- **ThinkSomethingToSay**: Processes an input reference to generate an output message.

### Logging & Debugging
- **LoggerClientTrigger**: Logs execution details for debugging.

## Grouping Primitives into Actions
Actions consist of a sequence of primitives. A YAML-based approach enables defining complex tasks easily.

### Example Action: `pick_location` and `place_location`

#### `pick_location` Available Parameters:
```python
pick_location(self, object: str, grid: str, location: str, level: int = 0, clearance: float = 0.07, height: float = 0.07)
```
- **object**: The name of the object to pick.
- **grid**: The grid where the object is located.
- **location**: The specific location within the grid.
- **level** (default = 0): The stacking level for the object.
- **clearance** (default = 0.07): The clearance height before picking(in meter).
- **height** (default = 0.07): The height at which the object is grasped(in meter).

#### `place_location` Available Parameters:
```python
place_location(self, object: str, grid: str, location: str, level: int = 0, clearance: float = 0.07)
```
- **object**: The name of the object to place.
- **grid**: The grid where the object should be placed.
- **location**: The specific location within the grid.
- **level** (default = 0): The stacking level for the object.
- **clearance** (default = 0.07): The clearance height before placing(in meter).

  ## Object Definitions
Objects must be predefined in `objects.yaml` to be referenced in experiments. The model name can be different in `pick_location` and `place_location`, but the object name must match exactly in both `objects.yaml` and `experiment.yaml`.

#### Example `objects.yaml`:
```yaml
Objects:
  wooden_cube1:
    interaction_height: 0.0152
    max_height: 0.0252
    model: "wooden_cube"
```

## Creating New Primitives

### Automated Approach
To automate primitive creation, use the existing RAS framework scripts that auto-generate required Behavior Tree (BT) nodes.

#### Step 1: Declare the Primitive in YAML
Edit the file `ros2_pkgs/ras_bt_framework/config/primitive_declaration.yaml` and add the new primitive under the `primitives` section.

#### Step 2: Generate the Primitive Template
Run the following command to generate a new primitive file:
```bash
ros2 run ras_bt_framework generate_primitive
```
This will create a new primitive file inside `ros2_pkgs/ras_bt_framework/generated_files`.

#### Step 3: Modify the Primitive Behavior
Use the generated template and edit it according to your required functionality.

### Manual Approach
For a manual implementation:
1. Create a new primitive class (e.g., `PickObject`).
2. Implement the behavior tree node:
   - Subscribe to necessary ROS topics.
   - Call required action servers (e.g., `MoveToPose` for reaching objects).
3. Register the new primitive in `registerNodes()`.
4. Test the primitive using a sample behavior tree configuration.

## Creating a New Experiment from Scratch

### Step 1: Create a YAML File
Create a new YAML file inside `config/experiments/` with a meaningful experiment name, e.g., `stacking.yaml`.

### Step 2: Define Poses
Poses represent key locations for the robot during the experiment. Each pose includes:
- Position `(x, y, z)` in meters.
- Orientation `(roll, pitch, yaw)` in radians.
- and provide a meaningfull name to pose (Ex-out1,in1 etc).


#### Example:
```yaml
Poses:
  out1: {x: 0.2, y: 0, z: 0.5, roll: 3.14, pitch: 0, yaw: 0}
  above1: {x: 0.425, y: 0.010, z: 0.280, roll: 3.14, pitch: 0, yaw: 0}
  in1: {x: 0.425, y: 0.010, z: 0.175, roll: 3.14, pitch: 0, yaw: 0}
```

### Step 3: Define the Grid Section
The grid represents object placement locations. Each grid consists of:
- A reference pose defining its position and orientation.
- Locations relative to the reference pose.

#### Example:
```yaml
Grids:
  grid0:
    pose: {x: 0.425, y: 0.010, z: 0.165, roll: 3.14, pitch: 0, yaw: 0} //reference pose
    locations:
      x1y1: {x: 0.0, y: 0.08}
      x1y2: {x: 0.0, y: 0.0}
      x1y3: {x: 0.0, y: -0.08}
      x2y1: {x: -0.08, y: 0.08}
      x2y2: {x: -0.08, y: 0.0}
      x2y3: {x: -0.08, y: -0.08}
```

### Step 4: Define Targets
The targets section defines the sequence of actions the robot will execute.

#### Example:
```yaml
targets:
  - move2pose: out1    //primitive
  - pick_location:      //action
      object: wooden_cube1
      grid: grid0
      location: x1y1
  - place_location:
      object: wooden_cube1
      grid: grid0
      location: x2y3
  - pick_location:
      object: wooden_cube1
      grid: grid0
      location: x2y1
  - place_location:
      object: wooden_cube1
      grid: grid0
      location: x2y3
      level: 1
  - pick_location:
      object: wooden_cube1
      grid: grid0
      location: x1y3
  - place_location:
      object: wooden_cube1
      grid: grid0
      location: x2y3
      level: 2
  - move2pose: out1
```

### Explanation:
- **Move to out1**: The robot starts at the standby position.
- **Pick wooden_cube1 from grid0 at x1y1**.
- **Place wooden_cube1 at x2y3**.
- **Pick another cube from x2y1**.
- **Stack it at x2y3 at level 1 (second layer)**.
- **Pick another cube from x1y3**.
- **Stack it at x2y3 at level 2 (third layer)**.
- **Return to out1**.

## Conclusion
This guide provides a structured approach to designing and executing experiments using the RAS framework. By following these steps, you can define poses, grids, object locations, and robotic actions efficiently, leveraging YAML files for ease of configuration.
