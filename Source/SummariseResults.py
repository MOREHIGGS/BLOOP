from json import load
from textwrap import dedent
from collections import defaultdict
from matplotlib import pylab as plt
import numpy as np
from pathlib import Path
def summariseResults(args):
    multiStepCount = 0
    complexCount = 0
    nonPertCount = 0
    failDict = defaultdict(int)
    
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
        
        else:
            if result["steps"] > 1:
                    multiStepCount += 1
    
            if result["complex"]:
                complexCount += 1

            if result["strong"]:
                bmInputList.append((list(result["bmInput"].values())))
                strength = 0
                ## Get the strongest PT (and assiocated Tc) of a potential mutli step PT
                for idk in result["PTData"]:
                    if idk["strength"] > strength:
                        strength = idk["strength"]
                        Tc = idk["Tc"]

                TcList.append(Tc)
                strengthList.append(strength)
                bmNumberList.append(result["bmNumber"])
    
    ## Sort bmInputs by order of strength, 
    ## this is so the colour of the scatter plot is set by the strong PT at that point
    ## transpose taken so each row is just on variable type (faster to plot)
    dataSorted =  np.transpose(np.asarray(sorted(zip(strengthList, bmNumberList, TcList, *np.transpose(bmInputList))))) 
    
    if len(dataSorted) > 0:
        with open(resultsDir/"summary.txt", "w") as fp:
            fp.writelines(dedent(f"""\
                Summary of the results: 
                Tc min/max is: {min(dataSorted[2])}, {max(dataSorted[2])} 
                The strongest BM is: {dataSorted[0][-1]} (strength), {dataSorted[1][-1]} (bmNumber) 
                The total number of benchmarks is: {len(data)}, {len(dataSorted[0])} of which are strong 
                and {multiStepCount} of which are mutli step PT
                The number of failed benchmarks is: {failDict.items()} 
                The number of benchmarks with a complex min is: {complexCount} 
                """))
        # Is this still needed?
        norm = plt.Normalize(dataSorted[0][0], dataSorted[0][-1])
        fileNames = list(result["bmInput"].keys())
        axisLabels = list(result["bmInput"].keys())

        ## ~~~~ For nicer axis labels~~~~
        #axisLabels = [
        #    "$\\theta_{\\text{CPV}}$",
        #    "$g_{\\text{hDM}}$",
        #    "$m_{s1}$ (GeV)",
        #    "$\\delta_{12} \\  (GeV)$",
        #    "$\\delta_{1c} \\  (GeV)$",
        #    "$\\delta_{c} \\  (GeV)$",
        #    "n"
        #]
        ## ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # Makes plots of first bm Input vs rest of bm inputs
        for inputIdx, data in enumerate(dataSorted[4:]):
            plt.scatter(dataSorted[3], data, s=4.2**2, c=dataSorted[0], marker="o", norm=norm)
            plt.xlabel(axisLabels[0], labelpad=5, fontsize=12)
            ## +1 needed to skip zeroth element
            plt.ylabel(axisLabels[inputIdx+1], labelpad=5, fontsize=12)
            plt.colorbar(label="strength")
            plt.savefig(resultsDir/f"{fileNames[inputIdx+1]}")
            plt.close()
        
        # Makes plots of bm inputs vs Tc
        for inputIdx, data in enumerate(dataSorted[3:]):
            plt.scatter(data, dataSorted[2], s=4.2**2, c=dataSorted[0], marker="o", norm=norm)
            plt.xlabel(axisLabels[inputIdx], labelpad=5, fontsize=12)
            plt.ylabel("$T_c$ (GeV)", labelpad=5, fontsize=12)
            plt.colorbar(label="strength")
            plt.savefig(resultsDir/f"Tc{fileNames[inputIdx]}")
            plt.close()

