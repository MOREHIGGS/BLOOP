import difflib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


def runTests():
    sourceDirectory = Path(__file__).resolve().parent
    integrationTestsDirectory = sourceDirectory/"../Share/IntegrationTests"
    unitResult = pytest.main([f"{sourceDirectory}/py_test_unit_tests.py", "-rx"])

    if unitResult != 0:
        print("Unit tests failed. Skipping integration tests.")
        sys.exit(unitResult)

    stdOut = ""
    for idx, loopOrder in enumerate(["NLO", "NNLO"]):
        print(f"Running {loopOrder} integration test:")

        loopDirectory = f'{sourceDirectory}/../TestResults/{loopOrder}/'
        Path(loopDirectory).mkdir(exist_ok=True, parents=True) 

        for file in Path(loopDirectory).glob('*'):
            os.remove(file)
        integrationTest = subprocess.run(
            [
                sys.executable,
                f'{sourceDirectory}/run_stages.py',
                '--loopOrder', f'{idx +1}', 
                '--lastBenchmark', '3',
                '--bSave',
                '--resultsDirectory', loopDirectory,
                '--TRangeStart', '90', 
                '--TRangeStepSize', '1',
                '--TRangeEnd', '200',
                '--gccFlags', "O1", "flto", "g",
                '--configFilePath', f'{sourceDirectory}/../Run/Z2_3HDMConfigFile.json',
                '--boundedConditionsFilePath', f'{sourceDirectory}/../Build/Z2_3HDM/DRalgoOutputFiles/BoundedConditions.txt',
                '--allSymbolsFilePath', f'{sourceDirectory}/../Build/Z2_3HDM/DRalgoOutputFiles/AllSymbols.txt',
                '--veffLOFilePath', f'{sourceDirectory}/../Build/Z2_3HDM/DRalgoOutputFiles/Veff_LO.txt',
                '--veffNLOFilePath', f'{sourceDirectory}/../Build/Z2_3HDM/DRalgoOutputFiles/Veff_NLO.txt',
                '--veffNNLOFilePath', f'{sourceDirectory}/../Build/Z2_3HDM/DRalgoOutputFiles/Veff_NNLO.txt',
                '--betaFunctions4DFilePath', f'{sourceDirectory}/../Build/Z2_3HDM/DRalgoOutputFiles/BetaFunctions4D.txt',
                '--vectorMassesSquaredFilePath', f'{sourceDirectory}/../Build/Z2_3HDM/DRalgoOutputFiles/VectorMasses.txt',
                '--vectorShortHandsFilePath', f'{sourceDirectory}/../Build/Z2_3HDM/DRalgoOutputFiles/VectorShorthands.txt',
                '--hardToSoftFilePath', f'{sourceDirectory}/../Build/Z2_3HDM/DRalgoOutputFiles/HardToSoft.txt',
                '--hardScaleFilePath', f'{sourceDirectory}/../Build/Z2_3HDM/DRalgoOutputFiles/HardScale.txt',
                '--softScaleRGEFilePath', f'{sourceDirectory}/../Build/Z2_3HDM/DRalgoOutputFiles/SoftScaleRGE.txt',
                '--softToUltraSoftFilePath', f'{sourceDirectory}/../Build/Z2_3HDM/DRalgoOutputFiles/SoftToUltraSoft.txt',
                '--ultraSoftScaleRGEFilePath', f'{sourceDirectory}/../Build/Z2_3HDM/DRalgoOutputFiles/UltraSoftScaleRGE.txt',
                '--scalarPermutationMatrixFilePath', f'{sourceDirectory}/../Build/Z2_3HDM/DRalgoOutputFiles/ScalarPermutationMatrix.txt',
                '--scalarRotationMatrixFilePath', f'{sourceDirectory}/../Build/Z2_3HDM/DRalgoOutputFiles/ScalarRotationMatrix.txt',
                '--scalarMassMatrixFilePath', f'{sourceDirectory}/../Build/Z2_3HDM/DRalgoOutputFiles/ScalarMassMatrix.txt',
                '--lagranianVariablesFilePath', f'{sourceDirectory}/../Build/Z2_3HDM/DRalgoOutputFiles/LagranianSymbols.json',
                '--scalarMassNamesFilePath', f'{sourceDirectory}/../Build/Z2_3HDM/DRalgoOutputFiles/ScalarMassNames.txt',
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
        with open(f"{loopDirectory}/scanResults.json", "r") as fp:
            scanResults = json.load(fp)
        with open(
            f'{sourceDirectory}/../Share/IntegrationTests/{loopOrder}/ReferenceResult/ScanResults.json', 
            "r",
        ) as fp:
            scanResultsRef = json.load(fp)
        
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
        
        if isApproxEq(scanResults, scanResultsRef, 0, 0):
            print(f"Summary of results at {loopOrder} matches references exactly")
            continue
        
        elif isApproxEq(scanResults, scanResultsRef, 1e-3, 1e-2):
            print(f"Summary of results at {loopOrder} is within tolerance of the solver")
            continue

        stdOut += f"Summary of results at {loopOrder} is outside the tolerance of the solver"  
        
        with open(sourceDirectory/f"../Run/{loopOrder}Diff.txt", "w") as fp:
            fp.write("Summary diff:")
            fp.write("".join(difflib.unified_diff(
            json.dumps(scanResults, indent=2).splitlines(keepends=True),
            json.dumps(scanResultsRef, indent=2).splitlines(keepends=True),
            fromfile='output',
            tofile='reference'
        )))

        for i in range(4):
            with open("{loopDirectory}/BM_{i}.json", "r") as fp:
                bm = json.load(fp)

            with open(
                f'{sourceDirectory}/../Share/IntegrationTests/{loopOrder}/ReferenceResult/BM_{i}.json', 
                "r",
            ) as fp:
                bmRef = json.load(fp)

            if not isApproxEq(bm, bmRef, 1e-3, 5e-2):
                stdOut += f"{loopOrder}: BM{i} is outside tol solver  \n"
    
            with open(sourceDirectory/f"../Run/{loopOrder}Diff.txt", "a") as fp:
                fp.write(f"BM{i} diff:\n")
                fp.write("".join(difflib.unified_diff(
                json.dumps(bm, indent=2).splitlines(keepends=True),
                json.dumps(bmRef, indent=2).splitlines(keepends=True),
                fromfile='output',
                tofile='reference'
            )))


    if stdOut:
        print("\nSee (N)NLODiff.txt (in Run) for further details. \n")
        sys.exit(stdOut)
    
    
if __name__ == '__main__':
    runTests()
