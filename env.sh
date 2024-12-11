#ras_docker_interface
export RAS_DOCKER_PATH=$(realpath $(dirname "${BASH_SOURCE[0]:-$0}"))
rdi() { python3 $RAS_DOCKER_PATH/scripts/docker_interface.py "$@" ; }