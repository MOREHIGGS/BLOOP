import json
import ijson
import decimal
from pathlib import Path
from pathos.multiprocessing import Pool
from importlib import import_module
from functools import partial
from tqdm import tqdm
import numpy as np

from TrackVEV import TrackVEV

def loopBenchmarks(args):
    sourceDirectory = Path(__file__).resolve().parent
    moduleDirectory = sourceDirectory/"../Build"/args.modelDirectory 
    resultsDir = sourceDirectory/f"../Run/{args.resultsDirectory}"
    resultsDir.mkdir(exist_ok=True, parents=True)   
    with open(moduleDirectory/args.pythonisedExpressionsFilePath, "r") as fp:
        pythonisedExpressions = json.load(fp)
        
    fieldNames = pythonisedExpressions["lagranianVariables"]["lagranianVariables"]["fieldSymbols"]
    
    trackVEV = TrackVEV(tuple(_drange(args.TRangeStart, args.TRangeEnd, str(args.TRangeStepSize))),
                     args.initialGuesses,
                     args.verbose,
                     pythonisedExpressions,
                     args.loopOrder,
                     {"nbrVars": len(fieldNames),
                             "absGlobalTol": args.absGlobalTolerance,
                             "relGlobalTol": args.relGlobalTolerance,
                             "absLocalTol": args.absLocalTolerance,
                             "relLocalTol": args.relLocalTolerance,
                             "varLowerBounds": args.bgfLowerBounds,
                             "varUpperBounds": args.bgfUpperBounds,
                     },
                     )
    
    def streamBenchmarksIn(path, first_bm, last_bm):
        with open(path, "r") as benchmarkFile:
            for benchmark in ijson.items(benchmarkFile, "item", use_float=True):
                bm_number = benchmark["bmNumber"]
                if first_bm <= bm_number <= last_bm:
                    yield benchmark


    def streamResultsOut(resultsGenerator, outputFilePath):
        with open(outputFilePath, "w") as fp:
            fp.write("[\n")
            middle = False

            for result in resultsGenerator:
                if middle:
                    fp.write(",\n")
                json.dump(result, fp, indent=2)
                middle = True

            fp.write("\n]\n")


    doBenchmarkWrapper = partial(doBenchmark, trackVEV, args, fieldNames, resultsDir)

    benchmarkGenerator = streamBenchmarksIn(
        moduleDirectory / args.benchmarkFilePath,
        args.firstBenchmark,
        args.lastBenchmark
    )

    if args.workers > 1:
        with Pool(args.workers) as pool:
            resultsGenerator = tqdm(
                pool.imap_unordered(doBenchmarkWrapper, benchmarkGenerator, chunksize=args.chunkSize)
            )

            streamResultsOut(
                resultsGenerator,
                resultsDir / f"{args.scanResultsName}.json"
            )
    else:
        resultsGenerator = (
            doBenchmarkWrapper(benchmark)
            for benchmark in tqdm(benchmarkGenerator)
        )

        streamResultsOut(
            resultsGenerator,
            resultsDir / f"{args.scanResultsName}.json"
        )

def doBenchmark(
    trackVEV, 
    args, 
    fieldNames, 
    resultsDirectory,
    benchmark,
):
    if args.verbose:
        print(f"Starting benchmark: {benchmark['bmNumber']}")

    minimizationResult = trackVEV.trackVEV(benchmark)

    filename = resultsDirectory/f"BM_{benchmark['bmNumber']}"

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
    }

    if result["failureReason"]:
        return processedResult 

    allFieldValues = result["vevLocation"] / np.sqrt(result["T"])
    allFieldValuesD = np.diff(allFieldValues)
    allFieldValuesT = allFieldValues.transpose() 
    
    fieldLengthDiff = np.array([ np.linalg.norm(allFieldValuesT[idx]) 
                       - np.linalg.norm(allFieldValuesT[idx+1]) 
                       for idx in range(len(allFieldValuesT)-1) ])  
    
    ## Symmetric index should be the last jump above 0.1 in the length list
    PTIndices = {int(len(fieldLengthDiff) -np.argmax(fieldLengthDiff[::-1] > 0.1) -1)}
    ## Get the rest of the large jumps 
    PTIndices.update(int(idx) for idx in (fieldLengthDiff >= 0.2).nonzero()[0])
    
    processedResult["steps"] = len(PTIndices)
 
    complexList = np.abs( np.array(result["vevDepthImag"]) / np.array(result["vevDepthReal"])
                  ) > 1e-8 

    if len(PTIndices) > 0:
        results = []
         
        for idx in PTIndices:
            if not processedResult["strong"]:
                processedResult["strong"] = bool(fieldLengthDiff[idx] > strengthCutOff)
            
            EFTBreak = ""
            
            if result["violatedHardScale"][idx] or result["violatedHardScale"][idx+1]:
                EFTBreak += "violatedHardScale"
            
            if complexList[idx] or complexList[idx+1]:
                if EFTBreak:
                    EFTBreak+= "&"
                EFTBreak += "complex"

            resultDic = {
                "Tc": result["T"][idx], 
                "strength": float(fieldLengthDiff[idx]),
                "EFTBreak": EFTBreak if EFTBreak else False,
            }
            
            for fieldNameIdx, fieldJumps in enumerate(allFieldValuesD):
                if abs(fieldJumps[idx]) > 0.1:
                    resultDic[fieldNames[fieldNameIdx]] = float(fieldJumps[idx])
            results.append(resultDic)
         
        processedResult["PTData"] = results
    
    return processedResult


## This (sometimes) avoids floating point error in T gotten by np.arange or linspace
## However one must be careful as 1 = decimal.Decimal(1.000000000000001)
def _drange(start, end, jump):
    start = decimal.Decimal(start)
    while start <= end:
        yield float(start)
        start += decimal.Decimal(jump)

