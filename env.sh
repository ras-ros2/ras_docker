#ras_docker_interface
export RAS_DOCKER_PATH=$(realpath $(dirname "${BASH_SOURCE[0]:-$0}"))
RDI_PATH=$RAS_DOCKER_PATH/scripts
if [ -z "$RAS" ]; then
    export PATH=$RDI_PATH:$PATH
fi
if [ ! -f "$HOME/.bash_completion.d/python-argcomplete.sh" ]; then
    activate-global-python-argcomplete3 --user
fi
export RAS="RAS"