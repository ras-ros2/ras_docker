#ras_docker_interface
export RAS_DOCKER_PATH=$(realpath $(dirname "${BASH_SOURCE[0]:-$0}"))
export RAS_WORKSPACE_PATH=$RAS_DOCKER_PATH/ros2_ws
source /opt/ros/humble/setup.bash
export RAS_ROS_RC=$RAS_WORKSPACE_PATH/install/setup.bash
source_ras_ros() {
    if [  -f $RAS_ROS_RC ]; then
        source $RAS_ROS_RC
    fi
}
source_ras_ros

rdi() { python3 $RAS_DOCKER_PATH/scripts/docker_interface.py "$@" ; }