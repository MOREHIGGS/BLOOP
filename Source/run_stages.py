from importlib import import_module

from user_input import UserInput

from LoopBenchmarks import loopBenchmarks
from MetaData import writeMetaData
from PythoniseMathematica import pythoniseMathematica


def main():
    args = UserInput().parse()
   
    if args.verbose: print("Meta data stage started")
    writeMetaData(args)
    
    if args.verbose: print("Convert Mathematica stage started")
    pythoniseMathematica(args)
    
    if args.verbose: print("Benchmark generation stage started")
    import_module(args.bmGeneratorModule).generateBenchmarks(args)
    
    if args.verbose: print("Minimization stage stage started")
    loopBenchmarks(args)
    
    if args.verbose: print("Summarise Results stage started")
    import_module(args.summariseModule).summariseResults(args)

if __name__ == "__main__":
    main()
