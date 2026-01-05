import argcomplete
import argparse
import multiprocessing
from enum import IntEnum
import json
from sys import maxsize


class Stages(IntEnum):
    convertMathematica = 0
    generateBenchmark = 1
    doMinimization = 2
    summariseResults = 3 

    @staticmethod
    def fromString(*args, **kwargs):
        if args:
            return Stages[args[0]]

        if kwargs:
            return Stages[kwargs["default"]]


class UserInput(argparse.ArgumentParser):
    def __init__(self):
       super().__init__()

       configGroup = self.add_argument_group('Configuration options')
       configGroup.add_argument = self.addArgumentNoMetaVar(configGroup)
       
       configGroup.add_argument(
           "--configFilePath",
           action="store",
           type=str,
           help="Str: Load cmd line args from json",
       )
       configGroup.add_argument(
           "--gccFlags",
           nargs="*",
           action="store",
           default=[],
           help="List[str]: Flags to pass to gcc. Recommended flags for perfomance 'O3 march=native'. Note native compiles it for your cpu and so the excutable is non-transferable.  To reduce memory 'O1'. Don't include the - or flags"
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
           help="Int: Specify how many workers pool uses to compute benchmarks (needs to be >1 for pool to be invoked)",
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
       stageGroup = self.add_argument_group('Stage control', 'Str:')
       stageGroup.add_argument = self.addArgumentNoMetaVar(stageGroup)
       
       stageGroup.add_argument(
           "--firstStage", 
           default="convertMathematica", 
           type=Stages.fromString,
           help="What stage of the code to start from"
       )
       stageGroup.add_argument(
           "--lastStage", 
           default="summariseResults", 
           type=Stages.fromString,
           help="What stage of the code to end on"
       )
       
       ########################################################################
       benchmarkGroup = self.add_argument_group('Benchmark Options')
       benchmarkGroup.add_argument = self.addArgumentNoMetaVar(benchmarkGroup)
       
       benchmarkGroup.add_argument(
           "--benchmarkFilePath",
           action="store",
           default="../Build/Z2_3HDM/handPickedBenchmarks.json",
           help="Str: Relative (to src) name to where benchmarks are saved to"
       )
       benchmarkGroup.add_argument(
           "--benchmarkType",
           action="store",
           default="handPicked",
           choices=["load", "handPicked", "random", "randomSSS"],
           help="Str: Specify the mode to generate bm with.",
       )
       benchmarkGroup.add_argument(
           "--randomNum",
           type=int,
           action="store",
           help="Int: Specify how many random bm to generate.",
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
           default="Z2_ThreeHiggsBmGenerator",
           help="Str: Module name to generate benchmarks with. Needs a function called generateBenchmarks."
       )
       benchmarkGroup.add_argument(
           "--previousResultDirectory",
           action="store",
           help="str: Load previous results to do a strong sub set with.",
       )
       
       ########################################################################
       nloptGroup = self.add_argument_group('NLOPT controls')
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
           "--varLowerBounds",
           nargs="*",
           action="store",
           default=[-60, 1e-4, 1e-4],
           type=float,
           help="List[float]: Sets the lower bound on background fields for NLOPT. Bounds are in the same order as field names"
       )
       nloptGroup.add_argument(
           "--varUpperBounds",
           nargs="*",
           action="store",
           default=[60, 60, 60],
           type=list,
           help="List[float]: Sets the upper bound on background fields for NLOPT. Bounds are in the same order as field names",
       )
       nloptGroup.add_argument(
           "--initialGuesses",
           nargs="*",
           action="store",
           default=[
               [0.1, 0.1, 0.1],
               [5, 5, 5],
               [-5, 5, 5],
               [0.1, 0.1, 10],
               [0.1, 0.1, 20],
               [40, 40, 40],
               [-40, 40, 40],
               [59, 59, 59],
               [-59, 59, 59],
           ],
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
       outputGroup = self.add_argument_group('Output Options')
       outputGroup.add_argument = self.addArgumentNoMetaVar(outputGroup)
       
       outputGroup.add_argument(
           "--bSave",
           action="store_true",
           default=False,
           help="Bool: If activated the results of the minimisation will be saved to --results directory",
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
           help="Str: Module name of python module to generate plots, invoked by --bPlot (don't include the .py extension here)"
       )
       outputGroup.add_argument(
           "--resultsDirectory",
           action="store",
           default="Results",
           help="Str: Directory to save files to",
       )
       outputGroup.add_argument(
           "--scanResultsName",
           action="store",
           default="ScanResults",
           help="Str: File name to save interpreted to",
       )
       outputGroup.add_argument(
           "--strengthCutOff",
           action="store",
           default=0.6,
           type=float,
           help="float: Lowest strength of phase transition which we will label as strong",
       )
       ########################################################################
       filesGroup = self.add_argument_group('Model File Paths', 'These paths are all relative to Source (See config for example path)')
       filesGroup.add_argument = self.addArgumentNoMetaVar(filesGroup)
       
       filesGroup.add_argument(
           "--boundedConditionsFilePath",
           action="store",
           default="../Build/Z2_3HDM/DRalgoOutputFiles/BoundedConditions.txt",
       )
       filesGroup.add_argument(
           "--allSymbolsFilePath",
           action="store",
           default="../Build/Z2_3HDM/DRalgoOutputFiles/AllSymbols.json",
       )
       filesGroup.add_argument(
           "--loFilePath",
           action="store",
           default="../Build/Z2_3HDM/DRalgoOutputFiles/Veff_LO.txt",
       )
       filesGroup.add_argument(
           "--nloFilePath",
           action="store",
           default="../Build/Z2_3HDM/DRalgoOutputFiles/Veff_NLO.txt",
       )
       filesGroup.add_argument(
           "--nnloFilePath",
           action="store",
           default="../Build/Z2_3HDM/DRalgoOutputFiles/Veff_NNLO.txt",
       )
       filesGroup.add_argument(
           "--betaFunctions4DFilePath",
           action="store",
           default="../Build/Z2_3HDM/DRalgoOutputFiles/BetaFunctions4D.txt",
       )
       filesGroup.add_argument(
           "--vectorMassesSquaredFilePath",
           action="store",
           default="../Build/Z2_3HDM/DRalgoOutputFiles/VectorMasses.txt",
       )
       filesGroup.add_argument(
           "--vectorShortHandsFilePath",
           action="store",
           default="../Build/Z2_3HDM/DRalgoOutputFiles/VectorShorthands.txt",
       )
       filesGroup.add_argument(
           "--hardToSoftFilePath",
           action="store",
           default="../Build/Z2_3HDM/DRalgoOutputFiles/SoftScaleParams_NLO.txt",
       )
       filesGroup.add_argument(
           "--softScaleRGEFilePath",
           action="store",
           default="../Build/Z2_3HDM/DRalgoOutputFiles/SoftScaleRGE.txt",
       )
       filesGroup.add_argument(
           "--softToUltraSoftFilePath",
           action="store",
           default="../Build/Z2_3HDM/DRalgoOutputFiles/UltrasoftScaleParams_NLO.txt",
       )
       filesGroup.add_argument(
           "--scalarPermutationMatrixFilePath",
           action="store",
           default="../Build/Z2_3HDM/DRalgoOutputFiles/ScalarPermutationMatrix.txt",
       )
       filesGroup.add_argument(
           "--scalarRotationMatrixFilePath",
           action="store",
           default="../Build/Z2_3HDM/DRalgoOutputFiles/ScalarRotationMatrix.json",
       )
       filesGroup.add_argument(
           "--scalarMassMatrixFilePath",
           action="store",
           default="../Build/Z2_3HDM/DRalgoOutputFiles/ScalarMassMatrix.txt",
       )
       filesGroup.add_argument(
           "--lagranianVariablesFilePath",
           action="store",
           default="../Build/Z2_3HDM/DRalgoOutputFiles/LagranianSymbols.json",
       )
       filesGroup.add_argument(
           "--scalarMassNamesFilePath",
           action="store",
           default="../Build/Z2_3HDM/DRalgoOutputFiles/ScalarMassNames.json",
       )
       filesGroup.add_argument(
           "--pythonisedExpressionsFilePath",
           action="store",
           default="../Build/Z2_3HDM/DRalgoOutputFiles/PythonisedExpressionsFile.json",
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
