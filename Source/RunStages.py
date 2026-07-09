from importlib import import_module

from UserInput import UserInput
from PythoniseMathematica import pythoniseMathematica
from SummariseResults import summariseResults
from LoopBenchmarks import loopBenchmarks
from MetaData import writeMetaData

def main():
    args = UserInput().parse()
    
    if args.verbose:
        print("Producing meta data")
    writeMetaData(args)
    
    if args.verbose:
        print("Convert Mathematica stage started")
    pythoniseMathematica(args)
    
    if args.verbose:
        print("Benchmark generation stage started")
    # Instead of telling people in the README/help to not include .py, just remove .py 
    import_module(args.bmGeneratorModule.removesuffix(".py")).generateBenchmarks(args)
    
    if args.verbose:
        print("Minimization stage started")
    loopBenchmarks(args)
        
    if args.verbose:
        print("Summarise Results stage started")
    import_module(args.summariseModule.removesuffix(".py")).summariseResults(args)

if __name__ == "__main__":
    main()
