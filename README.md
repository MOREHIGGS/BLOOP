# BLOOP (Beyond one LOOp Phase transition)

BLOOP is a Python based code to compute the critical temperature and strength of cosmological phase transitions. BLOOP uses the dimensional reduction approach to compute the effective potential at either 1 loop/NLO or 2 loop/NNLO* accuracy, making use of [DRalgo](https://github.com/DR-algo/DRalgo) to compute the required matching relations, effective potential etc. 

Pre v1 history for BLOOP can be found [here](https://github.com/JasmineTC/Bloop)

*NLO refers to tree level potential + one loop self energies (resummed), NNLO adds one loop corrections to cubic and quartic couplings and two loop self energies.  

## Installing the code:
Download the code base with a git clone. From this point forward all commands are to be run from inside the BLOOP directory

For cross platform compatibility and clean installation environment we recommend install the code in a container using podman (or equivalent). Alternatively, the code can be pip installed locally. Depenedices can be found [here](https://github.com/MOREHIGGS/BLOOP/blob/main/Share/.requirements.txt).
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
The pip installation needs to be done in editable mode as we will be importing C code that is generated and compiled at run time.

</details>

### Test suite
To check if BLOOP was correctly installed run the unit and intergation tests in Source like so

```bash
python3 Tests.py
```

Note: Some tests and the integration tests can soft fail if unexpected versions of packages are installed, this can be safely ignored. 

## Using BLOOP:
To excute BLOOP one must excute the RunStages.py file in Source. For both the pip and container installation we provide a wrapper for RunStages so that you can simply run:

 ```bash
bloop
```
 
from the cmd line. However, this will just crash, as BLOOP requires model specific information from the user which needs to be provided via cmd line arguments. All cmd line arguments can be found adding the help flag (--help). As an actual example here is a snipet to do a parameter scan of 5000 points of the Z2_3HDM with a temperature range 100GeV to 500GeV with a 0.1GeV step size, at NNLO using 50 threads

 ```bash
bloop --configFilePath Z2_3HDMConfigFile.json --benchmarkType random --numBenchmarks 5000 --TRangeStart 100 --TRangeEnd 500 --TRangeStepSize 0.1 --loopOrder 2 --workers 50
```

Where we have streamlined a lot of the model dependent information into a configuration file which can be found [here](https://github.com/MOREHIGGS/BLOOP/blob/main/Run/Z2_3HDMConfigFile.json).

It is worth noting that explicit cmd line arguments will override arguments set in the configuration file.

<details>
<summary>Important flags</summary>
- Model file paths str: --modelDirectory (relative to Build) --loFilePath, nloFilePath etc  (relative to modelDirectory)
- --bmGeneratorModule str: User made py file that produces a list of benchmarks ([example](https://github.com/MOREHIGGS/BLOOP/blob/main/Source/Z2_3HDMBmGenerator.py))
- --loopOrder int: Compute Veff to NLO or NNLO 
   - NLO is 1 loop in masses, NNLO is two loop in masses, one loop in cubic/quartic couplings
- --verbose bool: Print progress to terminal
- --workers int: Run # benchmarks in parallel
- --bPlot bool: Generate a thermal history plot for each benchmark
- --TRange(Start/End/StepSize) float: Define the linspace of temperatures to compute the VEV at
</details>

## Implementing new models in DRalgo:
In order to use BLOOP for your model you must first implement the model in DRalgo following our examples [here](https://github.com/MOREHIGGS/BLOOP/blob/UpdateREADME/Share/DRalgoScripts/Z2_3HDM_DRalgo.wl). At time of writing this part of the code base is still in flux so we won't provide a detailed walk through just yet. 

## Implementing benchmark generating scripts:
Benchmark generating is left to the user as this is inherently model dependent. We recommend editing the example benchmark generating scripts in source to describe your model so that the interfacing with BLOOP is already handled. If you wish to have something more custom we will go over the requirments of the benchmark generating script. 

<details>
<summary>Requirments on benchmark script</summary>
 - A main function called generateBenchmarks which takes one argument for the cmd line arguments.
   - The role of this function is to save all the benchmarks to a json.
   - We expect this benchmark json to live at --moduleDirectory/--benchmarkFilePath
 - The benchmarks must be in the form of a nested dictionary  like {"bmInput": {<yourInputs>}}, "lagranianParameters": {<yourLagranianParameters>}, ...}
   - To be clear this is the lagranian parameters of the zero temperature, 4D theory
   - Because we run these couplings you must provide the RGScale at which they are defined
</details>

## Getting results
When BLOOP has finished with all the benchmarks a json file will be made (path controlled by --resultsDirectory and --scanResultsName) which contains the important information for each benchmark which looks like:
```JSON
[
{
  "bmNumber": 0,
  "bmInput": {
    "mS1": 99.4,
    ....
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
},
{
  "bmNumber": 1,
...
},
...
]
```
Note: We compute the strength as $\frac{\Delta V_c}{T_c}$, where $T_c$ is the critical temperature and $\Delta V_c$ is the change in VEV ($\sqrt{v_iv^i}$) at the critical temperature. Also, v3 is a name of one of the background fields in this model. 
<details>
<summary>Details of output</summary>
 
- **bmNumber** and **bmInput:** These are taken from the user provided benchmark
- **failureReason:** Captures _most_ cases why a benchmark fails, ranging from the benchmark being ill defined (non-pert, unbounded) to run time crashes (divided by 0 etc) 
- **PTData:** A list of all phase transitions that occured containing the critical temperature, strength of the phase transition, if the EFT appears to be valid, and what fields where invovled in the phase transition.
   - EFTBreak will say if any mass is above the hard scale (4$\pi$) and/or the potential is complex at the phase transition
- **strong:** Is there a phase transition with a strength above the user set lower limit (--strengthCutOff)
- **Steps:** How many phase transitions occured
    - Note: Strong and steps are technically redundant, they are there to make filtering the data easier
</details>

### Summarising results
BLOOP will write to a txt file a brief summary of the scan which looks like:

```text
Summary of the results: 
The total number of benchmarks is: 690390, 291884 of which are strong 
Of the strong phase transitions 23922 are mutli step
The strongest BM is 1 with strength 1.9709325947783138 
Tc min/max is: 73.0, 157.0 
Failure summary: dict_items([('unBounded', 856)]) 
EFT break down summary: dict_items([('complex', 9763), ('violatedHardScale&complex', 25), ('violatedHardScale', 18)])
```

Heat maps will also be generated for strong phase transitions. These heat maps will be the first element of bmInput vs the rest, and Tc vs all of bmInput. 

### Thermal history and raw data
To see the thermal history of a benchmark points include the --bPlot flag. To get the raw data BLOOP uses include the --bSave flag.
