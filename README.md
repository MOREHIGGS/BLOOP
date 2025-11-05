**THIS CODE WILL BE MOVED TO https://github.com/BLOOP-JTC/BLOOP**

# BLOOP (Beyond one LOOp Phase transition)
**THIS CODE IS IN ACTIVE DEVELOPMENT, EXPECT BUGS AND FEATURES TO BE CHANGED AND/OR REMOVED. DOUBLE CHECK ANY RESULT FROM THE CODE.**

Download the code base with a git clone. From this point forward all commands are to be run from inside the Bloop directory

For easy OS compatibility we run the code inside a container from the command line. This will require podman (or docker) to be installed on your system. 
Podman can be installed via:

- Linux (ubuntu)
```sudo apt install podman```

- Windows
``` ??? ```

- Mac
```???```
  
## Using a container:
On first installisation you will need to do:

```podman build . -t bloop```

With the container built we can enter the container with:

```podman run --mount type=bind,src=$PWD,target=/Bloop -it bloop /bin/bash -c "cd /Bloop/Run && exec /bin/bash"```

This will put you in the Run directory inside Bloop for convience. The container only needs to be built once, unless we add a new dependency or a dependency needs updating.

From this point forward all commands are to be run from inside the Run directory

## Running unit and integration tests:
Ensure the code has been installed successfully via

```UnitAndIntegrationTests.sh```

## Implementing new models:
Before we can get started with this code you need to first implement your own model in DRalgo following our examples laid out in the Mathematica directory. 
Store the generated txt files inside build.

Now we need to point the code to these generated text files this can be done via the command line (python3 -m RunStages --help to see all the command line options). 
However, **we strongly recommend the use of a bash script or config file** for easily excuting the code in a repeatable manner. As an example we have a config file for the default Z2 case which can be found in src. 

The flags that control model dependent behaviour are: 
- Data files: --loFilePath etc 
- Minimisation control: --initialGuesses, --var<Upper/Lower>Bounds, --absLocalTolerance etc 
- Generate benchmarks: --benchmarkFile (this should be a .py)
  
We have an example benchmark generating code in Source. The only thing we require from the user is the benchmark generator produces a json which we then load in benchmarkLooping.py.
## Executing the code:
The code is excuted via

```python3 -m RunStages ```

Generally useful flags:
- --loopOrder
- --verbose


**THIS CODE WILL BE MOVED TO https://github.com/BLOOP-JTC/BLOOP**
