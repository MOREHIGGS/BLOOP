import argcomplete
import argparse
import multiprocessing
import json
from sys import maxsize

class UserInput(argparse.ArgumentParser):
    def __init__(self):
       super().__init__()

       configGroup = self.add_argument_group('Configuration options')
       configGroup.add_argument = self.addArgumentNoMetaVar(configGroup)
       
       configGroup.add_argument(
           "--configFilePath",
           action="store",
           type=str,
           help="Str: Path (relative to cwd) to load cmd line args from json ",
       )
       configGroup.add_argument(
           "--gccFlags",
           nargs="*",
           action="store",
           default=["O3", "flto", "g2","march=native"],
           help="List[str]: Flags to pass to gcc. Defaults choosen to try to maximise perfomance and minimise binary size"
       )
       configGroup.add_argument(
           "--profile",
           action="store_true",
           default=False,
           help="Bool: Flag to allow for profiling of cython code"
       )
       configGroup.add_argument(
           "--verbose",
           action="store_true",
           default=False,
           help="Bool: If activated code will print as it progresses",
       )
       configGroup.add_argument(
           "--workers",
           action="store",
           default=1,
           choices=list(range(1, multiprocessing.cpu_count() + 1)),
           type=int,
           help="Int: Specify how many benchmarks to run in parallel",
       )
       configGroup.add_argument(
           "--chunkSize",
           action="store",
           default=5,
           type=int,
           help="Int: How many bm should each worker handle at a time (higher means less overheads but more sporadic saving of data)",
       )
       configGroup.add_argument(
           "--loopOrder",
           action="store",
           default=1,
           type=int,
           choices=[1, 2],
           help="Int: Specify the order to compute the effective potential to",
       )
       
       ########################################################################
       benchmarkGroup = self.add_argument_group('Benchmark Options')
       benchmarkGroup.add_argument = self.addArgumentNoMetaVar(benchmarkGroup)
       
       benchmarkGroup.add_argument(
           "--benchmarkFilePath",
           action="store",
           default="handPickedBenchmarks.json",
           help="Str: File path (relative to --modelDirectory) used for saving benchmarks"
       )
       benchmarkGroup.add_argument(
           "--benchmarkType",
           action="store",
           default="handPicked",
           help="Str: Specify the mode to generate bm with.",
       )
       benchmarkGroup.add_argument(
           "--maxNumBenchmarks",
           type=int,
           action="store",
           default = 1000,
           help="Int: Specify the maximum nunmber of benchmarks to generate. Needed for random mode.",
       )
       benchmarkGroup.add_argument(
           "--firstBenchmark", 
           default=0, 
           type=int,
           help="Int: First benchmark to do computations with"
       )
       benchmarkGroup.add_argument(
           "--lastBenchmark", 
           default=maxsize, 
           type=int,
           help="Int: Last benchmark to do computations with"
       )
       benchmarkGroup.add_argument(
           "--bmGeneratorModule",
           action="store",
           default="Z2_3HDMBmGenerator",
           help="Str: Module (living in source) name to generate benchmarks with. Needs a function called generateBenchmarks."
       )
       benchmarkGroup.add_argument(
           "--previousResultDirectory",
           action="store",
           help="str: File path (relative to cwd) used to load previously generated results to perfom another scan only using the points tagged as strong.",
       )
       
       ########################################################################
       nloptGroup = self.add_argument_group('NLOPT controls', """Important note:
       bgf bounds and initial guesses are applied to bgf the length of the name, then aplhabetically,
       i.e. if you have 4 bgf named v1, v1a, v1b, v2 and bounds [0, 1, 10, 50] then you have
       v1a:0 v1b:1 v1:10, v2:50 
       (you can get this order easily by doing sorted(fieldnames, reverse=True, key=len))
       """)
       nloptGroup.add_argument = self.addArgumentNoMetaVar(nloptGroup)
       nloptGroup.add_argument(
           "--absGlobalTolerance", 
           action="store", 
           default=0.5, 
           type=float,
           help="Float: Sets the absolute tolerance for global minimisation routine in NLOPT"
       )
       nloptGroup.add_argument(
           "--relGlobalTolerance", 
           action="store", 
           default=0.5, 
           type=float,
           help="Float: Sets the relative tolerance for global minimisation routine in NLOPT"
       )
       nloptGroup.add_argument(
           "--absLocalTolerance", 
           action="store", 
           default=1e-2, 
           type=float,
           help="Float: Sets the absolute tolerance for local minimisation routine in NLOPT"
       )
       nloptGroup.add_argument(
           "--relLocalTolerance", 
           action="store", 
           default=1e-3, 
           type=float,
           help="Float: Sets the relative tolerance for local minimisation routine in NLOPT"
       )
       nloptGroup.add_argument(
           "--bgfLowerBounds",
           nargs="*",
           action="store",
           type=float,
           help="List[float]: Sets the lower bound on background fields for NLOPT. Bounds are in the same order as field names"
       )
       nloptGroup.add_argument(
           "--bgfUpperBounds",
           nargs="*",
           action="store",
           type=list,
           help="List[float]: Sets the upper bound on background fields for NLOPT. Bounds are in the same order as field names",
       )
       nloptGroup.add_argument(
           "--initialGuesses",
           nargs="*",
           action="store",
           type=list,
           help="List[List[float]]: Initial values of background fields to be given to local minimisation routine in NLOPT",
       )
       
       ########################################################################
       tempGroup = self.add_argument_group('Temperature Range')
       tempGroup.add_argument = self.addArgumentNoMetaVar(tempGroup)
       tempGroup.add_argument(
           "--TRangeStart", 
           action="store", 
           default=50, 
           type=float,
           help="Float: Lowest temperature to look for phase transitions"
       )
       tempGroup.add_argument(
           "--TRangeEnd", 
           action="store", 
           default=200, 
           type=float,
           help="Float: Highest temperature to look for phase transitions"
       )
       tempGroup.add_argument(
           "--TRangeStepSize",  
           action="store", 
           default=1, 
           type=float,
           help="Float: Temperature step size for looking for phase transitions"
       )
       
       ########################################################################
       outputGroup = self.add_argument_group("Output Options")
       outputGroup.add_argument = self.addArgumentNoMetaVar(outputGroup)
       outputGroup.add_argument(
           "--resultsDirectory",
           action="store",
           default="Results",
           help="Str: Path (relative to Run) to directory to store output files",
       )      
       outputGroup.add_argument(
           "--bSave",
           action="store_true",
           default=False,
           help="Bool: If activated the results of the minimisation will be saved to --resultsDirectory",
       )
       outputGroup.add_argument(
           "--bPlot",
           action="store_true",
           default=False,
           help="Bool: If activated plotting code (--plotDataModule) is imported and used to generate plots ",
       )
       outputGroup.add_argument(
           "--plotDataModule",
           action="store",
           default="PlotData",
           help="Str: Module name of python module (living in Source) to generate plots, invoked by --bPlot (don't include the .py extension here)"
       )

       outputGroup.add_argument(
           "--scanResultsName",
           action="store",
           default="ScanResults",
           help="Str: File name for the scan results (lives inside --resultsDirectory)",
       )
       outputGroup.add_argument(
           "--strengthCutOff",
           action="store",
           default=0.6,
           type=float,
           help="float: Lowest strength of phase transition which we will label as strong",
       )
       outputGroup.add_argument(
           "--ignoreEFTBreak",
           action="store_true",
           default=False,
           help="Bool: If activated include phase transitions where the validity of the EFT is in question (particle masses above the hard scale or non-neligable imaginary part of effective potential)",
       )
       ########################################################################
       filesGroup = self.add_argument_group('Model File Paths', 'Give the path for your model directory (relative to Build), then all other files are relative to the model directory')
       filesGroup.add_argument = self.addArgumentNoMetaVar(filesGroup)
       
       filesGroup.add_argument(
            "--modelDirectory",
            action="store",
       )      
       filesGroup.add_argument(
           "--boundedConditionsFilePath",
           action="store",
       )
       filesGroup.add_argument(
           "--allSymbolsFilePath",
           action="store",
       )
       filesGroup.add_argument(
           "--veffLOFilePath",
           action="store",
       )
       filesGroup.add_argument(
           "--veffNLOFilePath",
           action="store",
       )
       filesGroup.add_argument(
           "--veffNNLOFilePath",
           action="store",
       )
       filesGroup.add_argument(
           "--betaFunctions4DFilePath",
           action="store",
       )
       filesGroup.add_argument(
           "--vectorMassesSquaredFilePath",
           action="store",
       )
       filesGroup.add_argument(
           "--vectorShortHandsFilePath",
           action="store",
       )
       filesGroup.add_argument(
           "--hardToSoftFilePath",
           action="store",
       )
       filesGroup.add_argument(
           "--hardScaleFilePath",
           action="store",
       )
       filesGroup.add_argument(
           "--softScaleRGEFilePath",
           action="store",
       )
       filesGroup.add_argument(
           "--softToUltraSoftFilePath",
           action="store",
           help="Set to none if working at the soft scale (don't worry about the ultrasoft scale RGE)"
       )
       filesGroup.add_argument(
           "--ultraSoftScaleRGEFilePath",
           action="store",
       )
       filesGroup.add_argument(
           "--scalarPermutationMatrixFilePath",
           action="store",
           help="Set to none if no permutation matrix used"
       )
       filesGroup.add_argument(
           "--scalarRotationMatrixFilePath",
           action="store",
       )
       filesGroup.add_argument(
           "--scalarMassMatrixFilePath",
           action="store",
       )
       filesGroup.add_argument(
           "--lagranianVariablesFilePath",
           action="store",
       )
       filesGroup.add_argument(
           "--scalarMassNamesFilePath",
           action="store",
       )
       filesGroup.add_argument(
           "--pythonisedExpressionsFilePath",
           action="store",
           default="PythonisedExpressionsFile.json",
       )

       argcomplete.autocomplete(self)
       
    noMetaVar = {"store_true", "store_false", "help", "version"}
    
    ## Magic claude monkey patch to remove the metaVar that clutters --help
    def addArgumentNoMetaVar(self, group):
        original = group.add_argument
        def customAddArgument(*args, **kwargs):
            if args and args[0].startswith("-") and kwargs.get("action") not in self.noMetaVar:
                kwargs["metavar"] = ""
            return original(*args, **kwargs)
        return customAddArgument

    def parse(self):
        userArg = super().parse_args()
        if userArg.configFilePath:
            with open(super().parse_args().configFilePath, "r") as fp:
                userConfig = json.load(fp)
            unexpectedKeys = [
                userKey
                for userKey in userConfig.keys()
                if userKey not in set(vars(userArg).keys())
            ]
            if len(unexpectedKeys) > 0:
                print(
                    f"User config file has unexpected key(s):\n {unexpectedKeys},\nExiting"
                )
                exit(-1)
            self.set_defaults(**userConfig)
        return super().parse_args()
