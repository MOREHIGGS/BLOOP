import json
import decimal
from pathlib import Path
from pathos.multiprocessing import Pool
from ijson import items
from importlib import import_module

from Bloop.TrackVEV import TrackVEV, cNlopt
from Bloop.ProcessMinimization import interpretData
from Bloop.PythoniseMathematica import replaceGreekSymbols
from Bloop.ParsedExpression import ParsedExpressionSystemArray


## This (sometimes) avoids floating point error in T gotten by np.arange or linspace
## However one must be careful as 1 = decimal.Decimal(1.000000000000001)
def _drange(start, end, jump):
    start = decimal.Decimal(start)
    while start <= end:
        yield float(start)
        start += decimal.Decimal(jump)


def doBenchmark(trackVEV, args, benchmark, fieldNames):
    if not args.firstBenchmark <= benchmark["bmNumber"] <= args.lastBenchmark:
        return

    if args.verbose:
        print(f"Starting benchmark: {benchmark['bmNumber']}")

    minimizationResult = trackVEV.trackVEV(benchmark)

    filename = f"{args.resultsDirectory}/BM_{benchmark['bmNumber']}"

    Path(args.resultsDirectory).mkdir(parents=True, exist_ok=True)
    if args.bSave:
        if args.verbose:
            print(f"Saving {benchmark['bmNumber']} to {filename}.json")
        with open(f"{filename}.json", "w") as fp:
            fp.write(json.dumps(minimizationResult, indent=4))
            
    if args.bPlot:
        if args.verbose:
            print(f"Plotting {benchmark['bmNumber']}")

        import_module(args.plotDataFile).plotData(minimizationResult, filename, fieldNames)

    if args.bProcessMin:
        if args.verbose:
            print(f"Processing {benchmark['bmNumber']} to {filename + '_interp'}.json")
        with open(f"{filename}_interp.json", "w") as fp :
            fp.write(
                json.dumps(
                    interpretData(
                        minimizationResult,
                        benchmark["bmNumber"],
                        benchmark["bmInput"],
                        fieldNames,
                    ),
                    indent=4,
                )
            )


def loopBenchmarks(args):
    trackVEV, fieldNames = setUpTrackVEV(args)

    with open(args.benchmarkFile) as benchmarkFile:
        if args.workers >1:
            with Pool(args.workers) as pool:
                ## Apply might be better suited to avoid this lambda function side step
                def doBenchmarkWrap(benchmark):
                    return doBenchmark(
                                    trackVEV, args, benchmark, fieldNames
                                )
                pool.map(
                    doBenchmarkWrap,
                    (
                        benchmark
                        for benchmark in items(benchmarkFile, "item", use_float=True)
                    ),
                )
        else:
            for benchmark in json.load(benchmarkFile):
                doBenchmark(trackVEV, args, benchmark, fieldNames)


def setUpTrackVEV(args):
    with open(args.pythonisedExpressionsFilePath, "r") as fp:
        pythonisedExpressions = json.load(fp)

    allSymbols = pythonisedExpressions["allSymbols"]["allSymbols"]
    lagranianVariables = pythonisedExpressions["lagranianVariables"]["lagranianVariables"]

    nloptInst = cNlopt(
        config={
            "nbrVars": len(lagranianVariables["fieldSymbols"]),
            "absGlobalTol": args.absGlobalTolerance,
            "relGlobalTol": args.relGlobalTolerance,
            "absLocalTol": args.absLocalTolerance,
            "relLocalTol": args.relLocalTolerance,
            "varLowerBounds": args.varLowerBounds,
            "varUpperBounds": args.varUpperBounds,
        }
    )

    fourPointSymbols = [
        replaceGreekSymbols(item) for item in lagranianVariables["fourPointSymbols"]
    ]
    yukawaSymbols = [
        replaceGreekSymbols(item) for item in lagranianVariables["yukawaSymbols"]
    ]
    gaugeSymbols = [
        replaceGreekSymbols(item) for item in lagranianVariables["gaugeSymbols"]
    ]
    ##Saves loading parsed expression a second time
    fieldNames = lagranianVariables["fieldSymbols"] 
    return (
        TrackVEV(
            config={
                "nloptInst": nloptInst,
                "fieldNames": fieldNames,
                "hardToSoft": ParsedExpressionSystemArray(
                    pythonisedExpressions["hardToSoft"]["expressions"],
                    allSymbols,
                    pythonisedExpressions["hardToSoft"]["filePath"],
                ),
                "softScaleRGE": ParsedExpressionSystemArray(
                    pythonisedExpressions["softScaleRGE"]["expressions"],
                    allSymbols,
                    pythonisedExpressions["softScaleRGE"]["filePath"],
                ),
                "softToUltraSoft": ParsedExpressionSystemArray(
                    pythonisedExpressions["softToUltraSoft"]["expressions"],
                    allSymbols,
                    pythonisedExpressions["softToUltraSoft"]["filePath"],
                ),
                "betaFunction4DExpression": ParsedExpressionSystemArray(
                    pythonisedExpressions["betaFunctions4D"]["expressions"],
                    allSymbols,
                    pythonisedExpressions["betaFunctions4D"]["filePath"],
                ),
                "bounded": ParsedExpressionSystemArray(
                    pythonisedExpressions["bounded"]["expressions"],
                    allSymbols,
                    pythonisedExpressions["bounded"]["filePath"],
                ),
                "TRange": tuple(
                    _drange(args.TRangeStart, args.TRangeEnd, str(args.TRangeStepSize))
                ),
                "pertSymbols": frozenset(
                    fourPointSymbols + yukawaSymbols + gaugeSymbols
                ),
                "verbose": args.verbose,
                "initialGuesses": args.initialGuesses,
                "allSymbols": allSymbols,
            }
        ),
        fieldNames,
    )
