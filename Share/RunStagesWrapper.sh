#!/bin/bash
# PYTHON_ARGCOMPLETE_OK

if [ -n "$SHARE_DIR" ]; then
    ## This is an env variable set in the docker to say we are in container
    ## as this script is copied to a different location so below doesn't work
    SHARE_DIR="$SHARE_DIR"
else
    SHARE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi

## Sets OMP_THREADS to 1 unless user sets it manually with env variabable
## "$@" needed for autocomplete on cmd line args
OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}" python3 $SHARE_DIR/../Source/RunStages.py "$@"
