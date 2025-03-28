# RAS Docker Walkthrough

This document provides a comprehensive walkthrough of the RAS (Robot Arm System) Docker environment structure and functionality. Use this guide to navigate the codebase and understand how to use the system.

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
├── generate_experiments.py # Tool for generating experiment configurations
├── repos                  # External repositories and dependencies
├── ros2_pkgs              # ROS2 packages for robot control
│   ├── ras_bt_framework   # Behavior Tree framework for task execution
│   ├── ras_core_pkgs      # Core ROS2 packages for robot functionality
│   └── ras_sim            # Simulation environment packages
├── scripts                # Utility scripts for various tasks
└── env.sh                 # Environment setup script
```

## Key Components

### Configuration System

The `configs` directory contains all configuration files for the RAS system:

- **experiments/**: YAML files defining robot arm experiments with pick-and-place actions
- **lab_setup.yaml**: Physical lab environment settings (camera positions, workspace limits)
- **objects.yaml**: Definitions of objects the robot can manipulate
- **ras_conf.yaml**: Main system configuration parameters

### ROS2 Packages

The `ros2_pkgs` directory contains the core ROS2 functionality:

- **ras_bt_framework/**: Behavior Tree framework for defining complex robot tasks
- **ras_core_pkgs/**: Essential packages for robot control, perception, and motion planning
- **ras_sim/**: Simulation environment for testing without physical hardware

### Applications

The `apps` directory contains high-level applications:

- **ras_robot_app/**: Main robot controller application
- **ras_server_app/**: Server application for remote monitoring and control

## Getting Started

### 1. Environment Setup

Initialize the environment by sourcing the environment script:

```bash
source env.sh
```

This sets up necessary environment variables and ROS2 workspace.

### 2. Creating Experiments

You can create robot experiments in two ways:

#### Using the Experiment Generator

Generate a basic pick-and-place experiment:

```bash
python generate_experiments.py --rows 3 --cols 3 --pattern pick_and_place --id 1
```

This will create a new experiment file at `configs/experiments/exp_generated_1.yaml`.

#### Manual Creation

Create a custom experiment by manually writing a YAML file:

1. Create a new file in `configs/experiments/` (e.g., `my_experiment.yaml`)
2. Define poses, grids, and target actions
3. See `README_EXPERIMENT_GENERATOR.md` for detailed instructions

### 3. Running Experiments

Launch the RAS system and execute an experiment:

```bash
# Start the ROS2 core system
ros2 launch ras_core_pkgs ras_system.launch.py

# In a new terminal, run your experiment
ros2 run ras_core_pkgs run_experiment --experiment exp_generated_1
```

## Common Tasks

### Simulating Robot Behavior

To test experiments in simulation before using physical hardware:

```bash
# Launch the simulation environment
ros2 launch ras_sim ras_simulation.launch.py

# Run an experiment in simulation
ros2 run ras_core_pkgs run_experiment --experiment exp_generated_1 --sim
```

### Working with Real Hardware

When using a physical robot:

```bash
# Connect to the robot hardware
ros2 launch ras_core_pkgs hardware.launch.py

# Calibrate the workspace (if needed)
ros2 run ras_core_pkgs calibrate_workspace

# Run an experiment on the physical robot
ros2 run ras_core_pkgs run_experiment --experiment exp_generated_1
```

### Monitoring and Debugging

To monitor the robot's state and debug issues:

```bash
# Launch visualization tools
ros2 launch ras_core_pkgs visualization.launch.py

# View robot status
ros2 topic echo /robot/status

# Check camera feeds
ros2 run rqt_image_view rqt_image_view
```

## Advanced Usage

### Custom Behavior Trees

For complex tasks beyond simple pick-and-place operations:

1. Create a behavior tree XML file in `ros2_pkgs/ras_bt_framework/trees/`
2. Register custom behavior tree nodes if needed
3. Launch using:
   ```bash
   ros2 run ras_bt_framework run_tree --tree my_custom_tree
   ```

### Creating Custom Objects

To add new object types for manipulation:

1. Edit `configs/objects.yaml` to add object definitions
2. Ensure objects have appropriate physical properties and dimensions
3. Update your experiment files to use the new objects

### Extending the System

To add new functionality:

1. Create new ROS2 packages in `ros2_pkgs/` for major components
2. Use the existing framework APIs for integration
3. Update launch files to include your new components

## Troubleshooting

Common issues and their solutions:

- **Coordinate Limits Warnings**: Ensure all positions are within the safe workspace boundaries
- **Connection Errors**: Check hardware connections and verify ROS2 network configuration
- **Motion Planning Failures**: Verify that target positions are reachable and collision-free
- **Perception Issues**: Ensure proper lighting conditions and camera calibration

## Further Resources

- **Code Documentation**: Available in source code and ROS2 package README files
- **ROS2 Documentation**: https://docs.ros.org/en/humble/
- **Behavior Tree Concepts**: See documentation in `ros2_pkgs/ras_bt_framework/docs/`

## Example Workflow

Here's a complete example workflow:

1. Generate an experiment:
   ```bash
   python generate_experiments.py --rows 2 --cols 2 --pattern grid --id 42
   ```

2. Start the RAS system:
   ```bash
   source env.sh
   ros2 launch ras_core_pkgs ras_system.launch.py
   ```

3. Run the experiment:
   ```bash
   ros2 run ras_core_pkgs run_experiment --experiment exp_generated_42
   ```

4. Monitor execution:
   ```bash
   ros2 topic echo /robot/state
   ```

This walkthrough should help you navigate and utilize the RAS Docker environment effectively. 