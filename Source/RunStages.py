from importlib import import_module

from UserInput import UserInput
from PythoniseMathematica import pythoniseMathematica
from SummariseResults import summariseResults
from LoopBenchmarks import loopBenchmarks

def main():
    args = UserInput().parse()

    if args.verbose:
        print("Convert Mathematica stage started")
    pythoniseMathematica(args)
    
    if args.verbose:
        print("Benchmark generation stage started")
    import_module(args.bmGeneratorModule).generateBenchmarks(args)
    
    if args.verbose:
        print("Minimization stage started")
    loopBenchmarks(args)
        
    if args.verbose:
        print("Summarise Results stage started")
    summariseResults(args)

if __name__ == "__main__":
    main()
