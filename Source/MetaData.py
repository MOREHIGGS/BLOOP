import socket
from datetime import datetime, timezone
import os
import psutil
import subprocess
import importlib.metadata
import platform
import getpass

def getGitInfo():
    gitCommands = {
        "tag": ["git", "describe", "--tags", "--always"],
         "branch": ["git", "rev-parse", "--abbrev-ref", "HEAD"],
         "dirtyFiles": ["git", "status", "--porcelain"]
    }

    output = dict()

    for key, command in gitCommands.items():
        gitInfo = subprocess.run(
            command,
            capture_output=True,
        )

        if gitInfo.returncode != 0:
            ## TODO put this in args.debug
            print(gitInfo.stderr.decode())
            output[key] = f"Unable to obtain {key}"
        
        else:
            output[key] = gitInfo.stdout.decode().strip().splitlines()
    
    return output

def getImportantDependcies():
    packages = ["nlopt", "pdg", "cython", "numpy", "sympy", "jinja2"]
    
    output = dict()

    for package in packages:
        output[package] = importlib.metadata.version(package)
    
    return output

def printMetaData(args):
    print(datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"))
    print(platform.python_version())
    print(getpass.getuser())
    print(socket.gethostname())
    print(getGitInfo())
    print(getImportantDependcies())
    print(" ".join(psutil.Process(os.getpid()).cmdline()))
