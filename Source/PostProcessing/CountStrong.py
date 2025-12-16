"""---prints the number of SFOPT in a dir ---
Loads all the file names in the results directory
Strips the Results/ part of the file name
Loads the benchmark information from the file
If the benchmark is strong save the file to a subsetresult dir"""

from os.path import join
from glob import glob
from json import load
from collections import defaultdict

strongCount = 0
multiStepCount = 0
complexCount = 0
nonPertCount = 0
failDict = defaultdict(int)
strongestBM = (0, 0)
TcMin = 1e100
TcMax = 0

directory = "Results/2LoopResults/Combined01SSS"
with open(directory, "r") as fp:
    data = load(fp)

if len(data) == 0:
    print("{directory} contains no data, exiting")
    exit()

for result in data:
    if result["failureReason"]:
        failDict[result["failureReason"]] += 1
    else:
        if len(result["steps"]) > 1:
                multiStepCount += 1

        if result["strong"] > 0.6:
            strongestBM = (
                (result["strong"], result["bmNumber"])
                if result["strong"] > strongestBM[0]
                else strongestBM
                )
            strongCount += 1
                
            for jumpResults in result["fieldJumps"]:
                Tc = jumpResults["Tc"]
                Tcmax = Tc if Tc > TcMax else TcMax
                Tcmin = Tc if Tc < TcMin else TcMin 

            if result["complex"]:
                complexCount += 1

            if not result["isPerturbative"]:
                nonPertCount +=1

print(f"Summary of the results in the directory '{directory}':")
print(f"The lowest Tc min is: {TcMin}")
print(f"The strongest BM is: {strongestBM}")
print(f"The number of benchmarks is: {len(data)}")
print(f"The number of strong benchmarks is: {strongCount}")
print(f"The number of mutli step phase transitions is: {multiStepCount}")
print(f"The number of failed benchmarks is: {failDict.items()}")
print(f"The number of benchmarks with a complex min is: {complexCount}")
print(f"The number of benchmarks that become non-pert is: {nonPertCount}")
