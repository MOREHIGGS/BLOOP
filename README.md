# BLOOP (Beyond one LOOp Phase transition)
**THIS CODE IS IN ACTIVE DEVELOPMENT, EXPECT BUGS AND FEATURES TO BE CHANGED AND/OR REMOVED. DOUBLE CHECK ANY RESULT FROM THE CODE.**

Pre v1 history for BLOOP can be found [here](https://github.com/JasmineTC/Bloop)

## Installing the code:
Download the code base with a git clone. From this point forward all commands are to be run from inside the BLOOP directory

For cross platform compatibility and clean installation environment we recommend install the code in a container using podman (or equivalent). Alternatively, the code can be pip installed locally.
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

If the container hasn't already been built then run (from inside the BLOOP directory):

```bash 
podman build . -t bloop
```
The container needs to only be built once unless a new version of BLOOP requires the container to be rebuilt (this will be communicated via the release notes). With the container built we can enter the container with:

```bash 
podman run --mount type=bind,src=$PWD,target=/Bloop -it bloop /bin/bash -c "cd /Bloop && exec /bin/bash"
```

This will put you in the Bloop directory for convience. 
</details>

<details>
<summary>Installing with PIP </summary>
From inside the Bloop directory run:

 ```bash
pip install -e .
```
 
</details>

## Using BLOOP:
To excute BLOOP one must excute the RunStages.py file in Source. For both the pip and container installation we provide a wrapper for RunStages so that you can simply run:

 ```bash
bloop
```
 
from the cmd line. However, this will just crash, as BLOOP requires model specific information from the user which needs to be provided via cmd line arguments. All cmd line arguments can be found by doing 
```bash
bloop --help
```

To streamline passing cmd line arguments to BLOOP one can use a bash script, or a configuration file like so

 ```bash
bloop --configFilePath Z2_3HDMConfigFile.json
```
Z2_3HDMConfigFile.json can be found in Run. 

A brief outline of the most important flags:

- Model file paths: --modelDirectory (relative to Build) --loFilePath, nloFilePath etc  (relative to modelDirectory)
- --bmGeneratorModule: User made py file that produces a list of benchmarks (see ??? for details)
- --loopOrder int: Compute Veff to NLO or NNLO
- --verbose bool: Print progress to terminal
- --workers int: Run # benchmarks in parallel
- --bPlot bool: Generate a thermal history plot for each benchmark
- --TRange(Start/End/StepSize) float: Define the linspace of temperatures to compute the VEV at

As a complete example lets do a scan of 5000 random points in the Z2_3HDM, with a temperature range 100GeV to 500GeV with a 0.1GeV step size, at NNLO using 50 threads
 ```bash
--configFilePath Z2_3HDMConfigFile.json --benchmarkType random --numBenchmarks 5000 --TRangeStart 100 --TRangeEnd 500 --TRangeStepSize 0.1 --loopOrder 2 --workers 50
```

## Implementing new models in DRalgo:
In order to use BLOOP for your model you must first implement the model in DRalgo following our examples laid out in the Mathematica directory. We spare the details here as at time of writing this part of the code changes a lot and so this readme can easily get out of sync. 

## Implementing new benchmark generating scripts:
Benchmark generating is largely left to the user as this is inherently model dependent. We simply require a main function called 'generateBenchmarks' which needs to take one argument, args. This args is how you access cmd line arguments like 'benchmarkType' and 'numBenchmarks'. During the running of generateBenchmarks it needs to save benchmark data to a json stored at --moduleDirectory/--benchmarkFilePath. This benchmark data must take the form of a nested dictionary like so {"bmInput": {<yourInputs>}}, "lagranianParameters": {<yourLagranianParameters>}, <OtherStuff>}. Again, for a concrete example see Z2_3HDMBmGenerator.py in Source. bmInput is used to generate basic heat maps of the results and lagranianParameters is used to do the calculations. 

## Getting results
When BLOOP has finished with all the benchmarks a json file will be made (path controlled by --resultsDirectory and --scanResultsName) which contains the important information for each benchmark which looks like:
```JSON
{
  "bmNumber": 0,
  "bmInput": {
    "mS1": 99.4,
    "delta12": 42.8,
    "delta1c": 96.1,
    "deltac": 5.3,
    "ghDM": 0.509,
    "thetaCPV": 2.55,
    "darkHierarchy": 1.00
  },
  "failureReason": false,
  "PTData": [
    {
      "Tc": 128.0,
      "strength": 1.05,
      "EFTBreak": false,
      "v3": -1.05
    }
  ],
  "strong": true,
  "steps": 1
}
```

<More text>
