from importlib import import_module
import ctypes
import importlib.util


from loop_benchmarks import loopBenchmarks
from meta_data import writeMetaData
from pythonise_dralgo import pythonise_DRalgo
from user_input import UserInput
from utility import printIfVerbose


def main():
    args = UserInput().parse()
   
    printIfVerbose("Meta data stage started", args.verbose)
    writeMetaData(args)
    
    printIfVerbose("Pythonise DRalgo stage started", args.verbose)
    pythonise_DRalgo(args)
    
    printIfVerbose("Benchmark generation stage started", args.verbose)
    import_module(args.bmGeneratorModule).generateBenchmarks(args)
    
    printIfVerbose("Minimization stage started", args.verbose)
    loopBenchmarks(args)
    
    printIfVerbose("Summarise Results stage started", args.verbose)
    import_module(args.summariseModule).summariseResults(args)

_REQUIRED_SYMBOLS = {"nlopt_create", "nlopt_set_lower_bounds"}

def _expose_nlopt_symbols():
    spec = importlib.util.find_spec("nlopt._nlopt")
    if spec is None or spec.origin is None:
        raise ImportError("Could not locate the nlopt._nlopt shared object")

    # RTLD_GLOBAL puts the library's exported symbols in the process-wide
    # scope, so extensions loaded later can resolve nlopt_* against it.
    lib = ctypes.CDLL(spec.origin, mode=ctypes.RTLD_GLOBAL)

    requiredNLoptFuncs = {
        "nlopt_create", 
        "nlopt_set_lower_bounds",
    }
    missing = [func for func in requiredNLoptFuncs if not hasattr(lib, func)]
    if missing:
        raise ImportError(
            f"{spec.origin} does not export {missing}; "
            "this nlopt wheel cannot be used to satisfy the Cython modules"
        )



if __name__ == "__main__":
    _expose_nlopt_symbols()
    main()
