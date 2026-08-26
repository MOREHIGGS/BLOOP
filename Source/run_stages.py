from importlib import import_module

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

if __name__ == "__main__":
    main()
