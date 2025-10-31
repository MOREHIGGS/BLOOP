import argparse
import multiprocessing
from enum import IntEnum
import json
from sys import maxsize


class Stages(IntEnum):
    convertMathematica = 0
    generateBenchmark = 1
    doMinimization = 2

    @staticmethod
    def fromString(*args, **kwargs):
        if args:
            return Stages[args[0]]

        if kwargs:
            return Stages[kwargs["default"]]


class UserInput(argparse.ArgumentParser):
    def __init__(self):
       super().__init__()

       config_group = self.add_argument_group('Configuration options')
       config_group.add_argument = self.addArgumentNoMetaVar(config_group)
       
       config_group.add_argument(
           "--configFilePath",
           action="store",
           type=str,
           help="Str: Load cmd line args from json",
       )
       config_group.add_argument(
           "--cython",
           action="store_true",
           default=False,
           help="Bool: If activated cython is used to compile parts of the code base"
       )
       config_group.add_argument(
           "--verbose",
           action="store_true",
           default=False,
           help="Bool: If activated code will print as it progresses",
       )
       config_group.add_argument(
           "--workers",
           action="store",
           default=1,
           choices=list(range(1, multiprocessing.cpu_count() + 1)),
           type=int,
           help="Int: Specify how many workers pool uses to compute benchmarks (needs to be >1 for pool to be invoked)",
       )
       config_group.add_argument(
           "--loopOrder",
           action="store",
           default=1,
           type=int,
           choices=[1, 2],
           help="Int: Specify the order to compute the effective potential to",
       )
       
       ########################################################################
       exec_group = self.add_argument_group('Stage control', 'Str:')
       exec_group.add_argument = self.addArgumentNoMetaVar(exec_group)
       
       exec_group.add_argument(
           "--firstStage", 
           default="convertMathematica", 
           type=Stages.fromString,
           help="What stage of the code to start from (mostly just used to skip convertMathematica)"
       )
       exec_group.add_argument(
           "--lastStage", 
           default="doMinimization", 
           type=Stages.fromString,
           help="What stage of the code to end on"
       )
       
       ########################################################################
       benchmark_group = self.add_argument_group('Benchmark Options')
       benchmark_group.add_argument = self.addArgumentNoMetaVar(benchmark_group)
       
       benchmark_group.add_argument(
           "--benchmarkFile",
           action="store",
           default="Bloop/Data/Z2_3HDM/Benchmarks/handPicked.json",
           help="Str: Relative (to src) name to where benchmarks are saved to"
       )
       benchmark_group.add_argument(
           "--benchmarkType",
           action="store",
           default="handPicked",
           choices=["load", "handPicked", "random", "randomSSS"],
           help="Str: Specify the mode to generate bm with.",
       )
       benchmark_group.add_argument(
           "--randomNum",
           type=int,
           action="store",
           help="Int: Specify how many random bm to generate.",
       )
       benchmark_group.add_argument(
           "--firstBenchmark", 
           default=0, 
           type=int,
           help="Int: First benchmark to do computations with"
       )
       benchmark_group.add_argument(
           "--lastBenchmark", 
           default=maxsize, 
           type=int,
           help="Int: Last benchmark to do computations with"
       )
       benchmark_group.add_argument(
           "--bmGeneratorModule",
           action="store",
           default="Bloop.Z2_ThreeHiggsBmGenerator",
           help="Str: Module name to generate benchmarks with. Needs a function called generateBenchmarks."
       )
       benchmark_group.add_argument(
           "--previousResultDirectory",
           action="store",
           help="str: Load previous results to do a strong sub set with.",
       )
       
       ########################################################################
       min_group = self.add_argument_group('NLOPT controls')
       min_group.add_argument = self.addArgumentNoMetaVar(min_group)
       min_group.add_argument(
           "--absGlobalTolerance", 
           action="store", 
           default=0.5, 
           type=float,
           help="Float: Sets the absolute tolerance for global minimisation routine in NLOPT"
       )
       min_group.add_argument(
           "--relGlobalTolerance", 
           action="store", 
           default=0.5, 
           type=float,
           help="Float: Sets the relative tolerance for global minimisation routine in NLOPT"
       )
       min_group.add_argument(
           "--absLocalTolerance", 
           action="store", 
           default=1e-2, 
           type=float,
           help="Float: Sets the absolute tolerance for local minimisation routine in NLOPT"
       )
       min_group.add_argument(
           "--relLocalTolerance", 
           action="store", 
           default=1e-3, 
           type=float,
           help="Float: Sets the relative tolerance for local minimisation routine in NLOPT"
       )
       min_group.add_argument(
           "--varLowerBounds",
           nargs="*",
           action="store",
           default=[-60, 1e-4, 1e-4],
           type=float,
           help="List[float]: Sets the lower bound on background fields for NLOPT. Bounds are in the same order as field names"
       )
       min_group.add_argument(
           "--varUpperBounds",
           nargs="*",
           action="store",
           default=[60, 60, 60],
           type=list,
           help="List[float]: Sets the upper bound on background fields for NLOPT. Bounds are in the same order as field names",
       )
       min_group.add_argument(
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
       temp_group = self.add_argument_group('Temperature Range')
       temp_group.add_argument = self.addArgumentNoMetaVar(temp_group)
       temp_group.add_argument(
           "--TRangeStart", 
           action="store", 
           default=50, 
           type=float,
           help="Float: Lowest temperature to look for phase transitions"
       )
       temp_group.add_argument(
           "--TRangeEnd", 
           action="store", 
           default=200, 
           type=float,
           help="Float: Highest temperature to look for phase transitions"
       )
       temp_group.add_argument(
           "--TRangeStepSize",  
           action="store", 
           default=1, 
           type=float,
           help="Float: Temperature step size for looking for phase transitions"
       )
       
       ########################################################################
       output_group = self.add_argument_group('Output Options')
       output_group.add_argument = self.addArgumentNoMetaVar(output_group)
       
       output_group.add_argument(
           "--bSave",
           action="store_true",
           default=False,
           help="Bool: If activated the results of the minimisation will be saved to --results directory",
       )
       output_group.add_argument(
           "--bPlot",
           action="store_true",
           default=False,
           help="Bool: If activated plotting code (--plotDataModule) is imported and used to generate plots ",
       )
       output_group.add_argument(
           "--plotDataModule",
           action="store",
           default="Bloop.PlotData",
           help="Str: Module name of python module to generate plots, invoked by --bPlot (don't include the .py extension here)"
       )
       output_group.add_argument(
           "--bProcessMin",
           action="store_true",
           default=False,
           help="Bool: If activated ProcessMinimization.py is used to try to find phase transitions from the raw data",
       )
       output_group.add_argument(
           "--resultsDirectory",
           action="store",
           default="Results",
           help="Str: Directory to save files to",
       )
       ########################################################################
       files_group = self.add_argument_group('Model File Paths', 'These paths are all relative to bloop/src/bloop')
       files_group.add_argument = self.addArgumentNoMetaVar(files_group)
       
       files_group.add_argument(
           "--boundedConditionsFilePath",
           action="store",
           default="Data/Z2_3HDM/ModelFiles/Misc/bounded.txt",
       )
       files_group.add_argument(
           "--allSymbolsFilePath",
           action="store",
           default="Data/Z2_3HDM/ModelFiles/Variables/allSymbols.json",
       )
       files_group.add_argument(
           "--loFilePath",
           action="store",
           default="Data/Z2_3HDM/ModelFiles/EffectivePotential/Veff_LO.txt",
       )
       files_group.add_argument(
           "--nloFilePath",
           action="store",
           default="Data/Z2_3HDM/ModelFiles/EffectivePotential/Veff_NLO.txt",
       )
       files_group.add_argument(
           "--nnloFilePath",
           action="store",
           default="Data/Z2_3HDM/ModelFiles/EffectivePotential/Veff_NNLO.txt",
       )
       files_group.add_argument(
           "--betaFunctions4DFilePath",
           action="store",
           default="Data/Z2_3HDM/ModelFiles/HardToSoft/BetaFunctions4D.txt",
       )
       files_group.add_argument(
           "--vectorMassesSquaredFilePath",
           action="store",
           default="Data/Z2_3HDM/ModelFiles/EffectivePotential/vectorMasses.txt",
       )
       files_group.add_argument(
           "--vectorShortHandsFilePath",
           action="store",
           default="Data/Z2_3HDM/ModelFiles/EffectivePotential/vectorShorthands.txt",
       )
       files_group.add_argument(
           "--hardToSoftFilePath",
           action="store",
           default="Data/Z2_3HDM/ModelFiles/HardToSoft/softScaleParams_NLO.txt",
       )
       files_group.add_argument(
           "--softScaleRGEFilePath",
           action="store",
           default="Data/Z2_3HDM/ModelFiles/HardToSoft/softScaleRGE.txt",
       )
       files_group.add_argument(
           "--softToUltraSoftFilePath",
           action="store",
           default="Data/Z2_3HDM/ModelFiles/SoftToUltraSoft/ultrasoftScaleParams_NLO.txt",
       )
       files_group.add_argument(
           "--scalarPermutationMatrixFilePath",
           action="store",
           default="Data/Z2_3HDM/ModelFiles/EffectivePotential/scalarPermutationMatrix.txt",
       )
       files_group.add_argument(
           "--scalarRotationMatrixFilePath",
           action="store",
           default="Data/Z2_3HDM/ModelFiles/EffectivePotential/scalarRotationMatrix.json",
       )
       files_group.add_argument(
           "--scalarMassMatrixFilePath",
           action="store",
           default="Data/Z2_3HDM/ModelFiles/EffectivePotential/scalarMassMatrix.txt",
       )
       files_group.add_argument(
           "--lagranianVariablesFilePath",
           action="store",
           default="Data/Z2_3HDM/ModelFiles/Variables/LagranianSymbols.json",
       )
       files_group.add_argument(
           "--scalarMassNamesFilePath",
           action="store",
           default="Data/Z2_3HDM/ModelFiles/Variables/ScalarMassNames.json",
       )
       files_group.add_argument(
           "--pythonisedExpressionsFilePath",
           action="store",
           default="Bloop/Data/Z2_3HDM/pythonisedExpressionsFile.json",
       )

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
            with open(super().parse_args().configFilepath, "r") as fp:
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
