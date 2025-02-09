#ras_docker_interface
export RAS_DOCKER_PATH=$(realpath $(dirname "${BASH_SOURCE[0]:-$0}"))
RDI_PATH=$RAS_DOCKER_PATH/scripts
if [ -z "$RAS" ]; then
    export PATH=$RDI_PATH:$PATH
fi
if [ ! -f "$HOME/.bash_completion.d/python-argcomplete.sh" ]; then
    if command -v activate-global-python-argcomplete3 &> /dev/null; then
        activate-global-python-argcomplete3 --user
        exec bash
    elif command -v activate-global-python-argcomplete &> /dev/null; then
            activate-global-python-argcomplete --user
            exec bash
    fi
fi
export RAS="RAS"