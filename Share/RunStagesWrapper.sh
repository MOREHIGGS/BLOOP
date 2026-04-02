#!/bin/bash

## Wrapper script to run BLOOP in the container by just doing 
## bloop
## This also sets OMP_NUM_THREADS to 1 by default to avoid over loading the cpu
## and allows for auto complete on cmd line arg 

# PYTHON_ARGCOMPLETE_OK

OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}" python3 /Bloop/Source/RunStages.py "$@"
