#!/bin/bash
# PYTHON_ARGCOMPLETE_OK

if [ -n "$BLOOP_SHARE_DIR" ]; then
    echo container
    BASE_DIR="$BLOOP_SHARE_DIR"
else
    echo non contianer
    BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi

python3 $BASE_DIR/../Source/RunStages.py "$@"
