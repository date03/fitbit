#!/bin/bash

# env check
if [ "$PYENV_VIRTUAL_ENV" != "" ]; then
    echo "$PYENV_VIRTUAL_ENV"
elif [ "$VIRTUAL_ENV" != "" ]; then
    echo "$VIRTUAL_ENV"
elif [ -f /.dockerenv ]; then
    echo "NVIDIA_BUILD_ID=$NVIDIA_BUILD_ID"
else
    echo please activate python3 environment.
    exit 1
fi

pip install -U pip

pip install requests
pip install pyyaml

pip install flask

echo "OK $0"