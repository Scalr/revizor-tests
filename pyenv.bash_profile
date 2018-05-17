#!/bin/sh


export PYENV_ROOT="/usr/local/pyenv"
export PATH="${PYENV_ROOT}/bin:${PYENV_ROOT}/shims:$PATH"
eval "$(pyenv init -)"

