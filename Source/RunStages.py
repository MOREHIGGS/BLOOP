from importlib import import_module
from UserInput import UserInput, Stages

from PythoniseMathematica import pythoniseMathematica
from SummariseResults import summariseResults

def main():
    args = UserInput().parse()

    if args.firstStage <= Stages.convertMathematica <= args.lastStage:
        if args.verbose:
            print("Convert Mathematica stage started")

        pythoniseMathematica(args)
    
    
    if args.firstStage <= Stages.generateBenchmarks <= args.lastStage:
        if args.verbose:
            print("Benchmark generation stage started")
        import_module(args.bmGeneratorModule).generateBenchmarks(args)
    
    if args.firstStage <= Stages.doMinimization <= args.lastStage:
        if args.verbose:
            print("Minimization stage started")
        ##importing this before pythoniseMathematica fails integration test        
        from LoopBenchmarks import loopBenchmarks
        loopBenchmarks(args)
    if args.firstStage <= Stages.summariseResults <= args.lastStage:
        if args.verbose:
            print("Summarise Results stage started")

        summariseResults(args)


    if args.firstStage <= Stages.summariseResults <= args.lastStage:
        if args.verbose:
            print("Summarise Results stage started")

        summariseResults(args)


if __name__ == "__main__":
        main()
