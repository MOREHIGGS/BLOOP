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
        self.add_argument(
            "--configFile",
            action="store",
            type=str,
            help="Str: Load cmd line args from json",
        )
        
        self.add_argument(
            "--cython",
            action="store_true",
            default= False,
            help="Bool: If activated cython is used to compile parts of the code base"
        )

        self.add_argument(
            "--loopOrder",
            action="store",
            default=1,
            type=int,
            choices=[1, 2],
            help="Int: Specify the order to compute the effective potential to",
        )

        self.add_argument(
            "--verbose",
            action="store_true",
            default=False,
            help="Bool: If activated code will print as it progresses",
        )

        self.add_argument(
            "--bPool",
            action="store_true",
            default=False,
            help="Bool: If activated code will run in parallel using number of threads set by --threads",
        )

        self.add_argument(
            "--threads",
            action="store",
            default=1,
            choices=list(range(1, multiprocessing.cpu_count() + 1)),
            type=int,
            help="Int: Specify how many thread pool uses to compute benchmarks (needs bPool)",
        )

        self.add_argument(
            "--bSave",
            action="store_true",
            default=False,
            help="Bool: If activated the results of the minimisation will be saved to --results directory",
        )

        self.add_argument(
            "--bPlot",
            action="store_true",
            default=False,
            help="Bool: If activated plotting code (--plotDataFile) is imported and used to generate plots ",
        )
        
        self.add_argument(
            "--plotDataFile",
            action="store",
            default="Bloop.PlotData",
            help="Str: File name of python file to generate plots, invoked by --bPlot (don't include .py extension)"
        )

        self.add_argument(
            "--bProcessMin",
            action="store_true",
            default=False,
            help="Bool: If activated ProcessMinimization.py is used to try to find phase transitions from the raw data",
        )

        self.add_argument(
            "--resultsDirectory",
            action="store",
            default="Results",
            help="Str: Directory to save files to",
        )

        self.add_argument(
            "--absGlobalTolerance", 
            action="store", 
            default=0.5, 
            type=float,
            help= "Float: Sets the absolute tolerance for global minimisation routine in NLOPT"
        )

        self.add_argument(
            "--relGlobalTolerance", 
            action="store", 
            default=0.5, 
            type=float,
            help= "Float: Sets the relative tolerance for global minimisation routine in NLOPT"
        )

        self.add_argument(
            "--absLocalTolerance", 
            action="store", 
            default=1e-2, 
            type=float,
            help= "Float: Sets the absolute tolerance for local minimisation routine in NLOPT"
        )

        self.add_argument(
            "--relLocalTolerance", 
            action="store", 
            default=1e-3, 
            type=float,
            help= "Float: Sets the relative tolerance for local minimisation routine in NLOPT"
        )

        self.add_argument(
            "--varLowerBounds",
            nargs="*",
            action="store",
            default=[-60, 1e-4, 1e-4],
            type=float,
            help="List[float]: Sets the lower bound on background fields for NLOPT. Bounds are in the same order as field names"
        )

        self.add_argument(
            "--varUpperBounds",
            nargs="*",
            action="store",
            default=[60, 60, 60],
            type=list,
            help="List[float]: Sets the upper bound on background fields for NLOPT. Bounds are in the same order as field names",
        )

        self.add_argument(
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
            help="List[List[float]]: Initial values of background fields to be given to local minimisation routine in NLOPT"
        )

        self.add_argument(
            "--TRangeStart", 
            action="store", 
            default=50, 
            type=float,
            help="Float: Lowest temperature to look for phase transitions"
        )

        self.add_argument(
            "--TRangeEnd", 
            action="store", 
            default=200, 
            type=float,
            help="Float: Highest temperature to look for phase transitions"
                          
        )

        self.add_argument(
            "--TRangeStepSize",  
            action="store", 
            default=1, 
            type=float,
            help="Float: Temperature step size for looking for phase transitions"
        )

        self.add_argument(
            "--firstStage", 
            default="convertMathematica", 
            type=Stages.fromString,
            help="Str: What stage of the code to start from. Useful to skip convertMathematica mostly"
        )

        self.add_argument(
            "--lastStage", 
            default="doMinimization", 
            type=Stages.fromString,
            help="Str: What stage of the code to end on"
        )

        self.add_argument(
            "--benchmarkFile",
            action="store",
            default="Bloop/Data/Z2_3HDM/Benchmarks/handPicked.json",
            help="Str: Relative (to src) name to where benchmarks are saved to"
        )

        self.add_argument(
            "--benchmarkType",
            action="store",
            default="handPicked",
            choices=["load", "handPicked", "random", "randomSSS"],
            help="Str: Specify the mode to generate bm with.",
        )

        self.add_argument(
            "--randomNum",
            type=int,
            action="store",
            help="Int: Specify how many random bm to generate.",
        )

        self.add_argument(
            "--prevResultDir",
            action="store",
            help="str: SLoad previous results to do a strong sub set with.",
        )

        self.add_argument(
            "--firstBenchmark", 
            default=0, 
            type=int,
            help="Int: First benchmark to do computations with"
        )

        self.add_argument(
            "--lastBenchmark", 
            default=maxsize, 
            type=int,
            help="Int: Last benchmark to do computations with"
        )

        self.add_argument(
            "--bmGeneratorFile",
            action="store",
            default="Bloop.Z2_ThreeHiggsBmGenerator",
            help="Str: Name of py file that lives in Bloop which generates benchmarks. Needs a function called generateBenchmarks."
        )

        self.add_argument(
            "--boundedConditions",
            action="store",
            default="Data/Z2_3HDM/ModelFiles/Misc/bounded.txt",
            help="Str: Relative (to bloop) file name to a txt that contains expressions for bounded from below checks."
        )

        self.add_argument(
            "--allSymbolsFile",
            action="store",
            default="Data/Z2_3HDM/ModelFiles/Variables/allSymbols.json",
        )

        self.add_argument(
            "--loFile",
            action="store",
            default="Data/Z2_3HDM/ModelFiles/EffectivePotential/Veff_LO.txt",
        )

        self.add_argument(
            "--nloFile",
            action="store",
            default="Data/Z2_3HDM/ModelFiles/EffectivePotential/Veff_NLO.txt",
        )

        self.add_argument(
            "--nnloFile",
            action="store",
            default="Data/Z2_3HDM/ModelFiles/EffectivePotential/Veff_NNLO.txt",
        )

        self.add_argument(
            "--betaFunctions4DFile",
            action="store",
            default="Data/Z2_3HDM/ModelFiles/HardToSoft/BetaFunctions4D.txt",
        )

        self.add_argument(
            "--vectorMassesSquaredFile",
            action="store",
            default="Data/Z2_3HDM/ModelFiles/EffectivePotential/vectorMasses.txt",
        )

        self.add_argument(
            "--vectorShortHandsFile",
            action="store",
            default="Data/Z2_3HDM/ModelFiles/EffectivePotential/vectorShorthands.txt",
        )

        self.add_argument(
            "--hardToSoftFile",
            action="store",
            default="Data/Z2_3HDM/ModelFiles/HardToSoft/softScaleParams_NLO.txt",
        )

        self.add_argument(
            "--softScaleRGEFile",
            action="store",
            default="Data/Z2_3HDM/ModelFiles/HardToSoft/softScaleRGE.txt",
        )

        self.add_argument(
            "--softToUltraSoftFile",
            action="store",
            default="Data/Z2_3HDM/ModelFiles/SoftToUltraSoft/ultrasoftScaleParams_NLO.txt",
        )

        self.add_argument(
            "--scalarPermutationMatrixFile",
            action="store",
            default="Data/Z2_3HDM/ModelFiles/EffectivePotential/scalarPermutationMatrix.txt",
        )

        self.add_argument(
            "--scalarRotationMatrixFile",
            action="store",
            default="Data/Z2_3HDM/ModelFiles/EffectivePotential/scalarRotationMatrix.json",
        )
        
        self.add_argument(
            "--scalarMassMatrixFile",
            action="store",
            default="Data/Z2_3HDM/ModelFiles/EffectivePotential/scalarMassMatrix.txt",
        )

        self.add_argument(
            "--lagranianVariablesFile",
            action="store",
            default="Data/Z2_3HDM/ModelFiles/Variables/LagranianSymbols.json",
        )
        
        self.add_argument(
            "--scalarMassNamesFile",
            action="store",
            default="Data/Z2_3HDM/ModelFiles/Variables/ScalarMassNames.json",
        )

        self.add_argument(
            "--pythonisedExpressionsFile",
            action="store",
            default="Bloop/Data/Z2_3HDM/pythonisedExpressionsFile.json",
        )

    noMetaVar = {"store_true", "store_false", "help", "version"}

    def add_argument(self, *args, **kwargs):
        if args[0].startswith("-") and kwargs.get("action") not in self.noMetaVar:
            kwargs["metavar"] = ""
        return super().add_argument(*args, **kwargs)

    def parse(self):
        userArg = super().parse_args()
        if userArg.config:
            with open(super().parse_args().config, "r") as fp:
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
