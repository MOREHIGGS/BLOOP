import pytest
import sys
import subprocess
import json
from pathlib import Path
import os
import difflib
import time
import shutil

def runTests():
    sourceDirectory = Path(__file__).resolve().parent
    integrationTestsDirectory = sourceDirectory/"../Share/IntegrationTests"
    unitResult = pytest.main([f"{sourceDirectory}/PyTestUnitTests.py"])
    if not unitResult == 0:
        print("Unit tests failed. Skipping integration tests.")
        return
    
    for idx, loopOrder in enumerate(["NLO", "NNLO"]):
        print(f"Running {loopOrder} integration test:")
        loopDir = integrationTestsDirectory/f'{loopOrder}/'
        for file in loopDir.glob('OutputResult/*'):
            print(file)
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
            '--TRangeStepSize', f'1',
            '--TRangeEnd', f'200',
            '--gccFlags', 'O1',
            '--lastStage', 'doMinimization',
            ], 
            capture_output=True,
            text=True,
            )
        
        if not integrationTest.returncode == 0:
            print(f"Error output: {integrationTest.stderr}")
            print(f"{loopOrder} integration test failed, exiting tests.")
            exit() 
        
        with open(loopDir/"OutputResult/ScanResults.json", "r") as fp:
            scanResults = json.load(fp)
        with open(loopDir/"ReferenceResult/ScanResults.json", "r") as fp:
            scanResultsRef = json.load(fp)


        if scanResults ==  pytest.approx(scanResultsRef, rel=0.):
            print(f"Summary of results at {loopOrder} is exactly what we expect")
            continue
        exit()
        print(f"Summary of results at {loopOrder} is not exactly what we expect")
        with open(f"{loopOrder}Diff.txt", "w") as fp:
            fp.write("Summary diff:")
            fp.write("".join(difflib.unified_diff(
            json.dumps(scanResults, indent=2).splitlines(keepends=True),
            json.dumps(scanResultsRef, indent=2).splitlines(keepends=True),
            fromfile='output',
            tofile='reference'
        )))

        for i in range(4):
            with open(f"{integrationTestsDirectory}/{loopOrder}/OutputResult/BM_{i}.json", "r") as fp:
                bm = json.load(fp)
            with open(f"{integrationTestsDirectory}/{loopOrder}/ReferenceResult/BM_{i}.json", "r") as fp:
                bmRef = json.load(fp)
        
            if bm == pytest.approx(bmRef, rel=0.): 
                print(f"BM{i} data is exactly what we expect")

            elif bm == pytest.approx(bmRef, rel=0.01, abs = 0.1):
                print(f"BM{i} is within 1% of what we expect")

            else:
                print(f"BM{i} is outside 1% of what we expect")
    
            with open(f"{loopOrder}Diff.txt", "a") as fp:
                fp.write(f"BM{i} diff:\n")
                fp.write("".join(difflib.unified_diff(
                json.dumps(bm, indent=2).splitlines(keepends=True),
                json.dumps(bmRef, indent=2).splitlines(keepends=True),
                fromfile='output',
                tofile='reference'
            )))

        print(f"See {loopOrder}Diff.txt for further details.")

    return

if __name__ == '__main__':
    runTests()
