import difflib
import json
import subprocess
import sys
from pathlib import Path
from shutil import rmtree

import pytest


def runTests():
    sourceDirectory = Path(__file__).resolve().parent
    unitResult = pytest.main([f"{sourceDirectory}/py_test_unit_tests.py", "-rx"])

    if unitResult != 0:
        print("Unit tests failed. Skipping integration tests.")
        sys.exit(unitResult)

    stdOut = ""
    for idx, loopOrder in enumerate(["NLO", "NNLO"]):
        print(f"Running {loopOrder} integration test:")

        loopOutDirectory = f'{sourceDirectory}/../Share/IntegrationTests/{loopOrder}-Out/'
        loopRefDirectory = f'{sourceDirectory}/../Share/IntegrationTests/{loopOrder}-Ref/'
        Path(loopOutDirectory).mkdir(exist_ok=True, parents=True) 

        rmtree(loopOutDirectory)
        
        modelDir = f"{sourceDirectory}/../Build/Z2_3HDM/DRalgoOutputFiles"
        integrationTest = subprocess.run(
            [
                sys.executable,
                f'{sourceDirectory}/run_stages.py',
                '--loopOrder', f'{idx +1}', 
                '--lastBenchmark', '3',
                '--bSave',
                '--resultsDirectory', loopOutDirectory,
                '--TRangeStart', '90', 
                '--TRangeStepSize', '1',
                '--TRangeEnd', '200',
                '--gccFlags', "O1", "flto", "g",
                '--configFilePath', f'{sourceDirectory}/../Run/Z2_3HDMConfigFile.json',
                '--boundedConditionsFilePath', f'{modelDir}/BoundedConditions.txt',
                '--allSymbolsFilePath', f'{modelDir}/AllSymbols.txt',
                '--veffLOFilePath', f'{modelDir}/Veff_LO.txt',
                '--veffNLOFilePath', f'{modelDir}/Veff_NLO.txt',
                '--veffNNLOFilePath', f'{modelDir}/Veff_NNLO.txt',
                '--betaFunctions4DFilePath', f'{modelDir}/BetaFunctions4D.txt',
                '--vectorMassesSquaredFilePath', f'{modelDir}/VectorMasses.txt',
                '--vectorShortHandsFilePath', f'{modelDir}/VectorShorthands.txt',
                '--hardToSoftFilePath', f'{modelDir}/HardToSoft.txt',
                '--hardScaleFilePath', f'{modelDir}/HardScale.txt',
                '--softScaleRGEFilePath', f'{modelDir}/SoftScaleRGE.txt',
                '--softToUltraSoftFilePath', f'{modelDir}/SoftToUltraSoft.txt',
                '--ultraSoftScaleRGEFilePath', f'{modelDir}/UltraSoftScaleRGE.txt',
                '--scalarPermutationMatrixFilePath', f'{modelDir}/ScalarPermutationMatrix.txt',
                '--scalarRotationMatrixFilePath', f'{modelDir}/ScalarRotationMatrix.txt',
                '--scalarMassMatrixFilePath', f'{modelDir}/ScalarMassMatrix.txt',
                '--lagranianVariablesFilePath', f'{modelDir}/LagranianSymbols.json',
                '--scalarMassNamesFilePath', f'{modelDir}/ScalarMassNames.txt',
            ],
            capture_output=True,
            check=False,
            text=True,
        )

        if integrationTest.returncode != 0:
            sys.exit(
                f"{loopOrder} integration test failed\n"
                f"Error:\n{integrationTest.stderr}"
                f"Error code: {integrationTest.returncode}\n"
            )
        with open(f"{loopOutDirectory}/ScanResults.json", "r") as file:
            scanResults = json.load(file)

        with open(f'{loopRefDirectory}/ScanResults.json', "r") as file:
            scanResultsRef = json.load(file)
        
        if isApproxEq(scanResults, scanResultsRef, 0, 0):
            print(f"Summary of results at {loopOrder} matches references exactly")
            continue
        
        elif isApproxEq(scanResults, scanResultsRef, 1e-3, 1e-2):
            print(f"Summary of results at {loopOrder} is within tolerance of the solver")
            continue

        stdOut += f"Summary of results at {loopOrder} is outside the tolerance of the solver"  
        
        with open(sourceDirectory/f"../Run/{loopOrder}Diff.txt", "w") as file:
            file.write("Summary diff:")
            file.write("".join(difflib.unified_diff(
            json.dumps(scanResults, indent=2).splitlines(keepends=True),
            json.dumps(scanResultsRef, indent=2).splitlines(keepends=True),
            fromfile='output',
            tofile='reference'
        )))

        for i in range(4):
            with open("{loopOutDirectory}/BM_{i}.json", "r") as file:
                bm = json.load(file)

            with open(
                f'{loopRefDirectory}/BM_{i}.json', 
                "r",
            ) as file:
                bmRef = json.load(file)

            if not isApproxEq(bm, bmRef, 1e-3, 5e-2):
                stdOut += f"{loopOrder}: BM{i} is outside tol solver  \n"
    
            with open(sourceDirectory/f"../Run/{loopOrder}Diff.txt", "a") as file:
                file.write(f"BM{i} diff:\n")
                file.write("".join(difflib.unified_diff(
                json.dumps(bm, indent=2).splitlines(keepends=True),
                json.dumps(bmRef, indent=2).splitlines(keepends=True),
                fromfile='output',
                tofile='reference'
            )))


    if stdOut:
        print("\nSee (N)NLODiff.txt (in Run) for further details. \n")
        sys.exit(stdOut)
    
## pytest.approx doesn't work with nested dicts so here's a partly AI
## written function to unpack the nested dicts and do the comparisons
def isApproxEq(data, ref, relTol, absTol):
    if isinstance(ref, dict):
        if data.keys() != ref.keys():
            return False
        return all(isApproxEq(data[k], ref[k], relTol, absTol) for k in ref)
    
    elif isinstance(ref, (list, tuple)):
        if len(data) != len(ref):
            return False
        return all(isApproxEq(a, e, relTol, absTol) for a, e in zip(data, ref))
    
    else:
        return data == pytest.approx(ref, relTol, absTol)
    
if __name__ == '__main__':
    runTests()
