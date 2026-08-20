import sys
from collections import defaultdict
from json import load
from matplotlib import pylab as plt
plt.rcParams.update({"font.size": 12})
import numpy as np
from pathlib import Path
from textwrap import dedent

import numpy as np
from matplotlib import pylab as plt


def summariseResults(args):
    multiStepCount = 0
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
        sys.exit()

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
                    if not args.includeEFTBreak:
                        continue

                if subResult["strength"] > strength:
                    strength = subResult["strength"]
                    Tc = subResult["Tc"]
            
            if strength:
                TcList.append(Tc)
                strengthList.append(strength)
                bmNumberList.append(result["bmNumber"])
                
                bmInputList.append(list(result["bmInput"].values()))
                if result["steps"] > 1:
                    multiStepCount += 1 
    
    ## Sort bmInputs by order of strength, 
    ## this is so the colour of the scatter plot is set by the strong PT at that point
    dataSorted =  np.transpose(np.asarray(sorted(zip(strengthList, bmNumberList, TcList, *np.transpose(bmInputList))))) 
    strengthSorted, bmNumberSorted, TcSorted = dataSorted[:3]
    bmInputsSorted = dataSorted[3:]
    
    if len(dataSorted) > 0:
        with open(resultsDir/"Summary.txt", "w") as fp:
            fp.writelines(dedent(f"""\
                Summary of the results: 
                The total number of benchmarks is: {len(data)}, {len(strengthSorted)} of which are strong 
                Of the strong phase transitions {multiStepCount} are mutli step
                The strongest BM is {int(bmNumberSorted[-1])} with strength {strengthSorted[-1]} 
                Tc min/max is: {min(TcSorted)}, {max(TcSorted)} 
                Failure summary: {failDict.items()} 
                EFT break down summary: {EFTBreakDict.items()} 
                """))
        
        axisLabels = list(result["bmInput"].keys())

        
        ## Heat map of first benchmark input vs rest of inputs, and benchmark inputs vs Tc with strength colour bar
        ## first input vs Tc needs to be outside for loop or you'd get first input vs first input plot

        saveHeatMap(
            bmInputsSorted[0], 
            TcSorted, 
            strengthSorted, 
            axisLabels[0], 
            "$T_c$", 
            resultsDir/f"{axisLabels[0]}"
        )
        
        for idx, bmInput in enumerate(bmInputsSorted[1:], 1):
            saveHeatMap(
                bmInputsSorted[0], 
                bmInput, 
                strengthSorted, 
                axisLabels[0], 
                axisLabels[idx], 
                resultsDir/f"{axisLabels[idx]}"
            )
        
            saveHeatMap(
                bmInput, 
                TcSorted, 
                strengthSorted, 
                axisLabels[idx], 
                "$T_c$", 
                resultsDir/f"{axisLabels[idx]}-Tc"
           )

def saveHeatMap(x, y, c, xLabel, yLabel, fileName, norm=None):
    #plt.scatter(x, y, c=c, s=50, marker =".", norm = norm)
    plt.hexbin(x, y, C=c, gridsize=50, reduce_C_function=np.max)
    plt.xlabel(xLabel, labelpad=5)
    plt.ylabel(yLabel, labelpad=0)
    plt.colorbar(label="strength")
    plt.savefig(fileName)
    plt.close()

