import json
import decimal
from pathlib import Path
from pathos.multiprocessing import Pool
from importlib import import_module
from functools import partial
from tqdm import tqdm
import numpy as np

from TrackVEV import TrackVEV, cNlopt
from PythoniseMathematica import replaceGreekSymbols
from ParsedExpression import ParsedExpressionSystemArray, ParsedExpressionArray


def loopBenchmarks(args):
    trackVEV, fieldNames = setUpTrackVEV(args)
    doBenchmarkWrapper = partial(doBenchmark, trackVEV, args, fieldNames)
    
    with open(args.benchmarkFilePath, "r") as benchmarkFile:
        benchmarkData = [benchmark for benchmark in json.load(benchmarkFile) 
                         if args.firstBenchmark <= benchmark["bmNumber"] <= args.lastBenchmark]
    if args.workers >1:
        with Pool(args.workers) as pool:
            scanResults = list(tqdm(pool.imap_unordered(
                    doBenchmarkWrapper,
                    benchmarkData
                ), 
                total = len(benchmarkData)
                ))
    else:
        scanResults = [doBenchmarkWrapper(benchmark) for benchmark in tqdm(benchmarkData)]
        
    with open(f"{args.resultsDirectory}/{args.scanResultsName}.json","w") as fp:
         json.dump(
         scanResults, 
         fp,
         indent=2)


def doBenchmark(
    trackVEV, 
    args, 
    fieldNames, 
    benchmark
):
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

    return processData(
                minimizationResult,
                benchmark["bmNumber"],
                benchmark["bmInput"],
                fieldNames,
                args.strengthCutOff,
            )


def processData(
    result, 
    bmNumber, 
    bmInput, 
    fieldNames, 
    strengthCutOff
):
    processedResult = {
        "bmNumber": bmNumber,
        "bmInput": bmInput,
        "failureReason": result["failureReason"],
        "PTData": None,
        "strong": False,
        "steps": 0
    }

    if result["failureReason"]:
        return processedResult 

    processedResult |= {"isPerturbative": bool(np.all(result["bIsPerturbative"])),
                        "complex": bool(np.any(
                                 np.abs( np.array(result["vevDepthImag"]) / np.array(result["vevDepthReal"])
                                        ) > 1e-8
                                        ))
                        }
      
    allFieldValues = result["vevLocation"] / np.sqrt(result["T"])
    allFieldValuesD = np.diff(allFieldValues)
    allFieldValuesT = allFieldValues.transpose() 
    
    fieldLengthDiff = np.array([ np.linalg.norm(allFieldValuesT[idx]) 
                       - np.linalg.norm(allFieldValuesT[idx+1]) 
                       for idx in range(len(allFieldValuesT)-1) ])  
    
    PTIndices = (fieldLengthDiff >= strengthCutOff).nonzero()[0]
    if len(PTIndices) > 0:
        processedResult["steps"] = len(fieldLengthDiff[PTIndices])
        processedResult["strong"] = True
        results = []
        
        for idx in PTIndices:
            resultDic = {
                "Tc": result["T"][idx], 
                "strength": fieldLengthDiff[idx]
            }
            
            for fieldNameIdx, fieldJumps in enumerate(allFieldValuesD):
                if abs(fieldJumps[idx]) > 0.1:
                    resultDic[fieldNames[fieldNameIdx]] = float(fieldJumps[idx])
            results.append(resultDic)
        
        processedResult["PTData"] = results
    
    return processedResult


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
    
    return (TrackVEV(tuple(_drange(args.TRangeStart, args.TRangeEnd, str(args.TRangeStepSize))),
                 set(fourPointSymbols + yukawaSymbols + gaugeSymbols),
                 args.initialGuesses,
                 nloptInst,
                 ParsedExpressionSystemArray(
                     pythonisedExpressions["hardToSoft"]["expressions"],
                     allSymbols,
                     pythonisedExpressions["hardToSoft"]["filePath"],
                 ),
                 ParsedExpressionArray(
                     pythonisedExpressions["hardScale"]["expressions"],
                     pythonisedExpressions["hardScale"]["filePath"],
                 ),
                 ParsedExpressionSystemArray(
                     pythonisedExpressions["softScaleRGE"]["expressions"],
                     allSymbols,
                     pythonisedExpressions["softScaleRGE"]["filePath"],
                 ),
                 ParsedExpressionSystemArray(
                     pythonisedExpressions["softToUltraSoft"]["expressions"],
                     allSymbols,
                     pythonisedExpressions["softToUltraSoft"]["filePath"],
                 ),
                 ParsedExpressionSystemArray(
                     pythonisedExpressions["betaFunctions4D"]["expressions"],
                     allSymbols,
                     pythonisedExpressions["betaFunctions4D"]["filePath"],
                 ),
                 ParsedExpressionSystemArray(
                     pythonisedExpressions["bounded"]["expressions"],
                     allSymbols,
                     pythonisedExpressions["bounded"]["filePath"],
                 ),
                 args.verbose,
                 allSymbols
                 ),
        ##Saves loading parsed expression a second time
        lagranianVariables["fieldSymbols"],
        )

## This (sometimes) avoids floating point error in T gotten by np.arange or linspace
## However one must be careful as 1 = decimal.Decimal(1.000000000000001)
def _drange(start, end, jump):
    start = decimal.Decimal(start)
    while start <= end:
        yield float(start)
        start += decimal.Decimal(jump)


