# OSS

# oss_docker

### Setup Instructions:

 git clone --recursive git@github.com:acceleration-robotics/oss_docker.git
 source oss_docker/env.sh
 odi sim init
 odi sim build # To Build Docker Image
 odi sim build # To Build Ros 2 Packages
 odi sim run # Starts the simulation 


### To perform the target poses sequentially 

ros2 run oss_bt_framework batman.py

Poses or targets can be updated multiple times in a simulation session 

### To Update Pose and Targets

Target is the sequence in which execution will take place of the poses.

To modify or add new pose modify user_input.yaml.

File Location:-

/oss_sim_lab/ros2_ws/src/oss_bt_framework/config



yaml
Poses:
  pose1:
    x: -0.14
    y: -0.25
    z: 0.119
    roll: -3.14
    pitch: 0
    yaw: 1.57Poses:
  pose1:
    x: -0.14
    y: -0.25
    z: 0.119
    roll: -3.14
    pitch: 0
    yaw: 1.57
  pose2:
    x: -0.14
    y: 0.25
    z: 0.124
    roll: -3.14
    pitch: 0
    yaw: 1.57

targets:
 - pose1
 - pose2



## Getting Started

### 1. Clone the Repository
bash
git clone --recursive git@github.com:acceleration-robotics/oss_docker.git


### 2. Source the Environment File
bash
source env.sh


### 3. Check Available Commands
Use the following command to see what you can do with ODI:
bash
odi -h


## Simulation Setup

### 1. Initialize the Simulation
Initialize the simulation environment which will create the first application under apps as oss_sim_lab:
bash
odi sim init


This step will clone all the required repositories.

### 2. Build the Simulation Workspace
Build the simulation workspace:
bash
odi sim build


This will first build the Docker file. Build again to build workspace:
bash
odi sim build


### 3. Run the Simulation
Run the simulation:
bash
odi sim run


This will take you inside the Docker environment.

## Behavior Tree (BT) Setup

### 1. Build the Behavior Tree
Run the following command to build the BT and generate the XML file:
bash
ros2 run oss_bt_framework batman.py


### 2. Run the Simulation
Launch the simulation:
bash
ros2 launch oss_core main.launch.py


### 3. Start the MoveIt Node
Start the MoveIt node:
bash
ros2 run oss_bt_framework ExecuteSim


### 4. Execute the Behavior Tree
Execute the BT using:
bash
ros2 run oss_bt_framework executor