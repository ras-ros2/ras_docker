#oss_docker_interface
export OSS_DOCKER_PATH=$(realpath $(dirname "${BASH_SOURCE[0]:-$0}"))
odi() { python3 $OSS_DOCKER_PATH/scripts/docker_interface.py "$@" ; }