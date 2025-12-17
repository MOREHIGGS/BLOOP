import json
from matplotlib import pylab as plt
import numpy as np
from pathlib import Path

def getData(scanResultsList):
    strengthList = []
    bmInputList = []
    TcList = []
    bmNumberList = []

    for scanResults in scanResultsList:
        with open(scanResults, "r") as fp:
            data = json.load(fp)
        
        if len(data) == 0:
            print(f"{scanResults} is empty")
            next()

        for result in data:
            if result["strong"] > 0.6:
                strengthList.append((result["strong"]))
                bmInputList.append((list(result["bmInput"].values())))
                
                Tc = 0

                ## This will just pick the largest Tc of a mutli step PT
                for jumpResults in result["fieldJumps"]:
                    Tc = jumpResults["Tc"] if jumpResults["Tc"] > Tc else Tc

                TcList.append(Tc)
                bmNumberList.append(result["bmNumber"])
    ## Sort bmInputs by order of strength, 
    ## this is so the colour of the scatter plot is set by the strong PT at that point
    ## transpose taken so each row is just on variable type (faster to plot)
    return np.transpose(sorted(zip(strengthList, bmNumberList, TcList, *np.transpose(bmInputList)))), list(result["bmInput"].keys())


data1Loop, axisLabels = getData(["results1.json", "results2.json"])
data2Loop, _ = getData(["2results1.json", "2results2.json"])
dataTotal = (data1Loop, data2Loop)

norm = plt.Normalize(0.6, max(max(dataTotal[0][0]), max(dataTotal[1][0])))

fileNames = axisLabels

## ~~~~ For nicer axis labels~~~~
axisLabels = [
    "$\\theta_{\\text{CPV}}$",
    "$g_{\\text{hDM}}$",
    "$m_{s1}$ (GeV)",
    "$\\delta_{12} \\  (GeV)$",
    "$\\delta_{1c} \\  (GeV)$",
    "$\\delta_{c} \\  (GeV)$",
    "n"
]
## ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

loopList = ["1Loop", "2Loop"]

for loopIdx, dataLoop in enumerate(dataTotal):
    fileDir = f"ScanFigures/{loopList[loopIdx]}"
    Path(fileDir).mkdir(parents=True, exist_ok=True)
    
    # Makes plots of first bm Input vs rest of bm inputs
    for inputIdx, data in enumerate(dataLoop[4:]):
        plt.scatter(dataLoop[3], data, s=4.2**2, c=dataLoop[0], marker="o", norm=norm)
        plt.xlabel(axisLabels[0], labelpad=5, fontsize=12)
        ## +1 needed to skip zeroth element
        print(inputIdx, axisLabels[inputIdx])
        plt.ylabel(axisLabels[inputIdx+1], labelpad=5, fontsize=12)
        plt.colorbar(
            ticks=(0.60, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1, 1.05, 1.10, 1.15),
            label="strength",
        )
        plt.savefig(fileDir + f"/{fileNames[inputIdx+1]}")
        plt.close()
        
    # Makes plots of bm inputs vs Tc
    for inputIdx, data in enumerate(dataLoop[3:]):
        
        plt.scatter(data, dataLoop[2], s=4.2**2, c=dataLoop[0], marker="o", norm=norm)
        plt.xlabel(axisLabels[inputIdx], labelpad=5, fontsize=12)
        plt.ylabel("$T_c$ (GeV)", labelpad=5, fontsize=12)
        plt.colorbar(
            ticks=(0.60, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1, 1.05, 1.10, 1.15),
            label="strength",
        )
        plt.savefig(fileDir + f"/Tc{fileNames[inputIdx]}")
        plt.close()
