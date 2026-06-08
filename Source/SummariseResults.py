from json import load
from textwrap import dedent
from collections import defaultdict
from matplotlib import pylab as plt
import numpy as np
from pathlib import Path

def summariseResults(args):
    multiStepCount = 0
    nonPertCount = 0
    failDict = defaultdict(int)
    EFTBreakDict = defaultdict(int)
    
    strengthList = []
    bmInputList = []
    TcList = []
    bmNumberList = []
    resultsDir = Path(__file__).resolve().parent/f"../Run/{args.resultsDirectory}"

    with open(resultsDir/f"{args.scanResultsName}.json","r") as fp:
        data = load(fp)

    if len(data) == 0:
        print(resultsDir/f"{args.scanResultsName} contains no data, exiting")
        exit()

    for result in data:

        if result["failureReason"]:
            failDict[result["failureReason"]] += 1
            continue

        if result["strong"]:
            strength = 0

            ## Get the strongest PT (and assiocated Tc) of a potential mutli step PT
            for subResult in result["PTData"]:
                EFTBreak = subResult["EFTBreak"]
                if EFTBreak:
                    EFTBreakDict[EFTBreak] +=1

                if EFTBreak and not args.includeEFTBreak:
                    continue
                
                if subResult["strength"] > strength:
                    strength = subResult["strength"]
                    Tc = subResult["Tc"]
            
            if strength:
                axisLabels = list(result["bmInput"].keys())
                TcList.append(Tc)
                strengthList.append(strength)
                bmNumberList.append(result["bmNumber"])
                
                bmInputList.append((list(result["bmInput"].values())))
                if result["steps"] > 1:
                    multiStepCount += 1 
    ## Sort bmInputs by order of strength, 
    ## this is so the colour of the scatter plot is set by the strong PT at that point
    ## transpose taken so each row is just on variable type (faster to plot)
    dataSorted =  np.transpose(np.asarray(sorted(zip(strengthList, bmNumberList, TcList, *np.transpose(bmInputList))))) 
    
    if len(dataSorted) > 0:
        with open(resultsDir/"Summary.txt", "w") as fp:
            fp.writelines(dedent(f"""\
                Summary of the results: 
                The total number of benchmarks is: {len(data)}, {len(dataSorted[0])} of which are strong 
                Of the strong phase transitions {multiStepCount} are mutli step
                The strongest BM is {int(dataSorted[0][-1])} with strength {dataSorted[0][-1]} 
                Tc min/max is: {min(dataSorted[2])}, {max(dataSorted[2])} 
                Failure summary: {failDict.items()} 
                EFT break down summary: {EFTBreakDict.items()} 
                """))

        # Makes plots of first bm Input vs rest of bm inputs
        for inputIdx, data in enumerate(dataSorted[4:]):
            plt.scatter(dataSorted[3], data, s=4.2**2, c=dataSorted[0], marker="o")
            plt.xlabel(axisLabels[0], labelpad=5, fontsize=12)
            ## +1 needed to skip zeroth element
            plt.ylabel(axisLabels[inputIdx+1], labelpad=5, fontsize=12)
            plt.colorbar(label="strength")
            plt.savefig(resultsDir/f"{axisLabels[inputIdx+1]}")
            plt.close()
        
        # Makes plots of bm inputs vs Tc
        for inputIdx, data in enumerate(dataSorted[3:]):
            plt.scatter(data, dataSorted[2], s=4.2**2, c=dataSorted[0], marker="o")
            plt.xlabel(axisLabels[inputIdx], labelpad=5, fontsize=12)
            plt.ylabel("$T_c$ (GeV)", labelpad=5, fontsize=12)
            plt.colorbar(label="strength")
            plt.savefig(resultsDir/f"Tc{axisLabels[inputIdx]}")
            plt.close()

