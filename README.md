# BLOOP (Beyond one LOOp Phase transition)
**THIS CODE IS IN ACTIVE DEVELOPMENT, EXPECT BUGS AND FEATURES TO BE CHANGED AND/OR REMOVED. DOUBLE CHECK ANY RESULT FROM THE CODE.**

##Installing the code:
Download the code base with a git clone. From this point forward all commands are to be run from inside the Bloop directory

For cross platform compatibility and clean installation environment we recommend install the code in a container using podman (or docker). Alternatively, the code can be pip installed locally.
<details>
 <summary>Installition with podman</summary>

If podman is not already installed on your computer you can follow the relavent instructions:

<details>
 
<summary>Windows (using winget in the powershell)</summary>
Virtualization must be enabled in the BIOS (default for windows 11) 

 ```bash
winget install -e --id RedHat.Podman
```
```bash 
podman machine init
```
```bash
podman machine start
 ```

</details>

<details>
<summary>macOS</summary>
Virtualization must be enabled (on by default)
 
```bash 
brew install podman
```
```bash
podman machine init
```
```bash
podman machine start
```

</details>

<details>
<summary>Linux(Ubuntu/Debian)</summary>


```bash 
sudo apt install podman
```

</details>

If the container hasn't already been built then run (from inside the Bloop directory):

```bash 
podman build . -t bloop
```

With the container built we can enter the container with:

```bash 
podman run --mount type=bind,src=$PWD,target=/Bloop -it bloop /bin/bash -c "cd /Bloop/Run && exec /bin/bash"
```

This will put you in the Run directory inside Bloop for convience. The container only needs to be built once, and only needs to be rebuilt if a new dependency needs to be installed, or an old one updated.
</details>

<details>
<summary>Installing with PIP </summary>
From inside the Bloop directory run:

 ```bash
pip install -e .
```
 
</details>

From this point forward all commands are to be run from inside the Run directory

## Executing BLOOP:
Excuting BLOOP depends on installation method:
<details>
<summary>Container installation: </summary>
From inside the Run directory:

 ```bash
python3 -m RunStages
```
 
</details>
<details>
<summary>PIP installation: </summary>
From inside the Run directory:

 ```bash
bloop
```
 
</details>
This will run run BLOOP with the Z2-3HDM model. Details of which can be found here https://arxiv.org/abs/2511.04636. 

BLOOP is intended to be controlled by command line arguments. To see a full list of arguments simply run  --help when excuting the code (see above). 

A brief outline of the most important flags:

- Model file paths: --loFilePath etc (relative to Run) 
- Generating benchmarks: --bmGeneratorModule
- --loopOrder
- --verbose


## Implementing new models:
Before we can get started with this code you need to first implement your own model in DRalgo following our examples laid out in the Mathematica directory. 
Store the generated txt files inside build.

BLOOP needs to be given the model file paths via the cmd line. To make this easier **we strongly recommend the use of a bash script or config file**. We have an example config file for the default Z2 case which can be found in Run. 
  
We have an example benchmark generating code in Source. The only thing we require from the user is the benchmark generator produces a json which we then load in benchmarkLooping.py.

