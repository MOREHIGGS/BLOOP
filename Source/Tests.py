import pytest
import sys
import subprocess
import json
from pathlib import Path
import os
import difflib

def runTests():
    sourceDirectory = Path(__file__).resolve().parent
    integrationTestsDirectory = sourceDirectory/"../Share/IntegrationTests"
    unitResult = pytest.main([f"{sourceDirectory}/PyTestUnitTests.py", "-rx"])

    if not unitResult == 0:
        print("Unit tests failed. Skipping integration tests.")
        sys.exit(unitResult)

    stdOut = ""
    for idx, loopOrder in enumerate(["NLO", "NNLO"]):
        print(f"Running {loopOrder} integration test:")
        loopDir = integrationTestsDirectory/f'{loopOrder}/'
        for file in loopDir.glob('OutputResult/*'):
            os.remove(file)
        integrationTest = subprocess.run([
            sys.executable,
            f'{sourceDirectory}/RunStages.py',
            '--loopOrder', f'{idx +1}', 
            '--lastBenchmark', '3',
            '--bSave',
            '--resultsDirectory', f'../Share/IntegrationTests/{loopOrder}/OutputResult',
            '--benchmarkFile', "../../Share/IntegrationTests/benchmarks.json",
            '--TRangeStart', '90', 
            '--TRangeStepSize', '1',
            '--TRangeEnd', '200',
            '--gccFlags', "O1", "flto", "g",
            '--configFilePath', f'{sourceDirectory}/../Run/Z2_3HDMConfigFile.json'
            ], 
            capture_output=True,
            text=True,
            )
        if not integrationTest.returncode == 0:
            sys.exit(
                f"{loopOrder} integration test failed\n"
                f"Error:\n{integrationTest.stderr}"
                f"Error code: {integrationTest.returncode}\n"
            )
        with open(loopDir/"OutputResult/ScanResults.json", "r") as fp:
            scanResults = json.load(fp)
        with open(loopDir/"ReferenceResult/ScanResults.json", "r") as fp:
            scanResultsRef = json.load(fp)
        
        ## pytest.approx doesn't work with nested dicts so here's a partly AI
        ## written function to unpack the nested dicts and do the comparisons
        def isApproxEq(actual, expected, relTol, absTol):
            if isinstance(expected, dict):
                if actual.keys() != expected.keys():
                    return False
                return all(isApproxEq(actual[k], expected[k], relTol, absTol) for k in expected)
            
            elif isinstance(expected, (list, tuple)):
                if len(actual) != len(expected):
                    return False
                return all(isApproxEq(a, e, relTol, absTol) for a, e in zip(actual, expected))
            
            else:
                return actual == pytest.approx(expected, relTol, absTol)
        
        ## These tolerances are hard coded to 0.1*default nlopt local tolerances
        if isApproxEq(scanResults, scanResultsRef, 1e-4, 1e-3):
            print(f"Summary of results at {loopOrder} is within tolerance of the solver")
            continue
        
        print(f"Summary of results at {loopOrder} is outside the tolerance of the solver")
        
        with open(sourceDirectory/f"../Run/{loopOrder}Diff.txt", "w") as fp:
            fp.write("Summary diff:")
            fp.write("".join(difflib.unified_diff(
            json.dumps(scanResults, indent=2).splitlines(keepends=True),
            json.dumps(scanResultsRef, indent=2).splitlines(keepends=True),
            fromfile='output',
            tofile='reference'
        )))

        for i in range(4):
            with open(loopDir/f"OutputResult/BM_{i}.json", "r") as fp:
                bm = json.load(fp)
            with open(loopDir/f"ReferenceResult/BM_{i}.json", "r") as fp:
                bmRef = json.load(fp)

            if isApproxEq(bm, bmRef, 1e-4, 1e-3):
                stdOut += f"{loopOrder}: BM{i} is within tol of solver \n"

            else:
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
        print(f"\nSee (N)NLODiff.txt (in Run) for further details. \n")
        sys.exit(stdOut)
    
    return None
    
if __name__ == '__main__':
    runTests()
