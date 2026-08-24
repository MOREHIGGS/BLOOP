from importlib import import_module

from pythonise_DRalgo import pythonise_DRalgo

from LoopBenchmarks import loopBenchmarks
from MetaData import writeMetaData
from user_input import UserInput


def main():
    args = UserInput().parse()
   
    if args.verbose: print("Meta data stage started")
    writeMetaData(args)
    
    if args.verbose: print("Pythonise DRalgo stage started")
    pythonise_DRalgo(args)
    
    if args.verbose: print("Benchmark generation stage started")
    import_module(args.bmGeneratorModule).generateBenchmarks(args)
    
    if args.verbose: print("Minimization stage stage started")
    loopBenchmarks(args)
    
    if args.verbose: print("Summarise Results stage started")
    import_module(args.summariseModule).summariseResults(args)

if __name__ == "__main__":
    main()
