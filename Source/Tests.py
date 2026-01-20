import pytest
import sys
import subprocess
import json
import glob
import os
import difflib
import time
import shutil

def runTests():
    sourceDirectory = os.path.dirname(os.path.realpath(__file__))
    integrationTestsDirectory = f"{sourceDirectory}/../Share/IntegrationTests"
    unitResult = pytest.main([f"{sourceDirectory}/PyTestUnitTests.py"])
    if unitResult == 0:
        loopOrderList = ["NLO", "NNLO"]
        for idx, loopOrder in enumerate(loopOrderList):
            print(f"Running {loopOrder} integration test:")
            for file in glob.glob("integrationTestDirectory/{loopOrder}/OutputResult/*"):
                os.remove(file)

            for file in glob.glob(f"{sourceDirectory}/../Build/CythonModules/*"):
                if os.path.isdir(file):
                    shutil.rmtree(file)
                else:
                    os.remove(file)
            
            integrationTest = subprocess.run([
                sys.executable,
                f'{sourceDirectory}/RunStages.py',
                '--loopOrder', f'{idx +1}', 
                '--lastBenchmark', '3',
                '--bSave',
                '--resultsDirectory', f'{integrationTestsDirectory}/{loopOrder}/OutputResult/',
                '--benchmarkFile', f'{integrationTestsDirectory}/Benchmarks',
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
            
            with open(f"{integrationTestsDirectory}/{loopOrder}/OutputResult/ScanResults.json", "r") as fp:
                scanResults = json.load(fp)
            with open(f"{integrationTestsDirectory}/{loopOrder}/ReferenceResult/ScanResults.json", "r") as fp:
                scanResultsRef = json.load(fp)

            try:
                os.remove(f"{loopOrder}Diff.txt")
            except:
                pass

            if scanResults ==  pytest.approx(scanResultsRef, rel=0.):
                print(f"{loopOrder} data is exactly what we expect")
            
            else:
                for i in range(4):
                    with open(f"{integrationTestsDirectory}/{loopOrder}/OutputResult/BM_{i}.json", "r") as fp:
                        bm = json.load(fp)
                    with open(f"{integrationTestsDirectory}/{loopOrder}/ReferenceResult/BM_{i}.json", "r") as fp:
                        bmRef = json.load(fp)
                
                    if bm == pytest.approx(bmRef, rel=0.): 
                        print(f"BM{i} data is exactly what we expect")
        
                    elif bm == pytest.approx(bmRef, rel=0.01):
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

                
    else:
        print("Unit tests failed. Skipping integration tests.")

    return

if __name__ == '__main__':
    runTests()
