import json
import decimal
from pathlib import Path
from pathos.multiprocessing import Pool
from ijson import items
from importlib import import_module
from functools import partial
from tqdm import tqdm

from TrackVEV import TrackVEV, cNlopt
from ProcessMinimization import interpretData
from PythoniseMathematica import replaceGreekSymbols
from ParsedExpression import ParsedExpressionSystemArray


## This (sometimes) avoids floating point error in T gotten by np.arange or linspace
## However one must be careful as 1 = decimal.Decimal(1.000000000000001)
def _drange(start, end, jump):
    start = decimal.Decimal(start)
    while start <= end:
        yield float(start)
        start += decimal.Decimal(jump)


def doBenchmark(trackVEV, args, fieldNames,benchmark):
    if not args.firstBenchmark <= benchmark["bmNumber"] <= args.lastBenchmark:
        return

    if args.verbose:
        print(f"Starting benchmark: {benchmark['bmNumber']}")

    minimizationResult = trackVEV.trackVEV(benchmark)

    filename = f"{args.resultsDirectory}/BM_{benchmark['bmNumber']}"

    Path(args.resultsDirectory).mkdir(parents=True, exist_ok=True)
    if args.bSave:
        if args.verbose:
            print(f"Saving raw data of {benchmark['bmNumber']} to {filename}.json")
        with open(f"{filename}.json", "w") as fp:
            fp.write(json.dumps(minimizationResult, indent=4))
            
    if args.bPlot:
        if args.verbose:
            print(f"Plotting {benchmark['bmNumber']}")

        import_module(args.plotDataModule).plotData(minimizationResult, filename, fieldNames)

    return interpretData(
                minimizationResult,
                benchmark["bmNumber"],
                benchmark["bmInput"],
                fieldNames,
            )

def loopBenchmarks(args):
    trackVEV, fieldNames = setUpTrackVEV(args)
    doBenchmarkWrapper = partial(doBenchmark, trackVEV, args, fieldNames)
    with open(args.benchmarkFilePath) as benchmarkFile:
        benchmarkData = json.load(benchmarkFile)
        if args.workers >1:
            with Pool(args.workers) as pool:
                scanResults = list(tqdm(pool.imap_unordered(
                    doBenchmarkWrapper,
                    benchmarkData
                    ), 
                    total = len(benchmarkData)
                ))
        else:
            scanResults = [doBenchmarkWrapper(benchmark) for benchmark in benchmarkData]
        
        with open(f"{args.resultsDirectory}/ScanResults.json","w") as fp:
             json.dump(
             scanResults, 
             fp)

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
    return (
        TrackVEV(
            config={
                "nloptInst": nloptInst,
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
        ##Saves loading parsed expression a second time
        lagranianVariables["fieldSymbols"],
    )
