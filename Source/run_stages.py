import ctypes
import importlib.util
import sys
from importlib import import_module
from pathlib import Path

## For reasons unknown Github PIP CI needs this
sys.path.insert(0, str(Path(__file__).parent))
from loop_benchmarks import loopBenchmarks
from meta_data import writeMetaData
from pythonise_dralgo import pythonise_DRalgo
from user_input import UserInput
from utility import printIfVerbose


def main():
    
    args = UserInput().parse()
    if args is None:
        return -1
    
    # Ensure cython build directory exists and that python modules within it are
    # importable
    Path(args.buildDirectoryFilePath).mkdir(exist_ok=True, parents=True)
    sys.path.insert(0, args.buildDirectoryFilePath)

    ## Catching common mistake
    for key, value in vars(args).items(): 
        if key.endswith("Module") and value:
            setattr(args, key,  f"{value.removesuffix('.py')}")
    
    ## Make file paths relative from BLOOP 
    BLOOPDir = str(Path(__file__).resolve().parent.parent)+"/"
    for key, value in vars(args).items(): 
        if key.endswith("FilePath") and value:
            setattr(args, key,  BLOOPDir+f"{value}") 
    
    ## AI code that puts NLopt symbols into global name space
    ## Far from ideal but the only way we could make gcc and Python 
    ## handle NLopt in Cython when BLOOP is PIP installed 
    ctypes.CDLL(importlib.util.find_spec("nlopt._nlopt").origin, mode=ctypes.RTLD_GLOBAL)
    
    printIfVerbose("Meta data stage started", args.verbose)
    writeMetaData(args)
    
    printIfVerbose("Pythonise DRalgo stage started", args.verbose)
    if (pythonise_DRalgo(args) < 0):
        return -1
    
    printIfVerbose("Benchmark generation stage started", args.verbose)
    import_module(args.bmGeneratorModule).generateBenchmarks(args)
    
    printIfVerbose("Minimization stage started", args.verbose)
    loopBenchmarks(args)
    
    printIfVerbose("Summarise Results stage started", args.verbose)
    import_module(args.summariseModule).summariseResults(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())

