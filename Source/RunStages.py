def main():
    from importlib import import_module
    from UserInput import UserInput, Stages
    args = UserInput().parse()

    if args.firstStage <= Stages.convertMathematica <= args.lastStage:
        if args.verbose:
            print("Convert Mathematica stage started")

        from PythoniseMathematica import pythoniseMathematica

        pythoniseMathematica(args)

    if args.firstStage <= Stages.generateBenchmark <= args.lastStage:
        if args.verbose:
            print("Benchmark generation stage started")
        import_module(args.bmGeneratorModule).generateBenchmarks(args)

    if args.firstStage <= Stages.doMinimization <= args.lastStage:
        if args.verbose:
            print("Minimization stage started")

        from LoopBenchmarks import loopBenchmarks

        loopBenchmarks(args)

if __name__ == "__main__":
        main()
