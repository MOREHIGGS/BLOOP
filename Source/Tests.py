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
            
            subprocess.run([
                sys.executable,
                f'{sourceDirectory}/RunStages.py',
                '--loopOrder', f'{idx +1}', 
                '--firstBenchmark', '1',
                '--lastBenchmark', '1',
                '--bSave',
                '--resultsDirectory', f'{integrationTestsDirectory}/{loopOrder}/OutputResult/',
                '--benchmarkFile', 'integrationTestsDirectory/Benchmarks',
                '--TRangeStart', '90', 
                '--TRangeStepSize', f'1',
                '--TRangeEnd', f'200',
                '--gccFlags', 'O1',
                '--lastStage', 'doMinimization',
            ])

            with open(f"{integrationTestsDirectory}/{loopOrder}/OutputResult/ScanResults.json", "r") as fp:
                scanResults = json.load(fp)
            with open(f"{integrationTestsDirectory}/{loopOrder}/ReferenceResult/ScanResults.json", "r") as fp:
                scanResultsRef = json.load(fp)

            with open(f"{integrationTestsDirectory}/{loopOrder}/OutputResult/BM_1.json", "r") as fp:
                bm1 = json.load(fp)
            with open(f"{integrationTestsDirectory}/{loopOrder}/ReferenceResult/BM_1.json", "r") as fp:
                bm1Ref = json.load(fp)
            print() 
            if bm1 == pytest.approx(bm1Ref, rel=0.) and scanResults ==  pytest.approx(scanResultsRef, rel=0.):
                print(f"{loopOrder} data is exactly what we expect")
                continue
        
            elif bm1 == pytest.approx(bm1Ref, rel=0.01):
                print(f"{loopOrder} data is within 1% of what we expect")
        
            else:
                print(f"{loopOrder} data is outside 1% of what we expect.")
            
            print(f"See {loopOrder}Diff.txt for further details.\n")
            
            with open(f"{loopOrder}Diff.txt", "w") as fp:
                fp.write("BM1 diff:\n")
                fp.write("".join(difflib.unified_diff(
                    json.dumps(bm1, indent=2).splitlines(keepends=True),
                    json.dumps(bm1Ref, indent=2).splitlines(keepends=True),
                    fromfile='output',
                    tofile='reference'
                )))
                fp.write("Scan results diff:\n")
                fp.write("".join(difflib.unified_diff(
                    json.dumps(scanResults, indent=2).splitlines(keepends=True),
                    json.dumps(scanResultsRef, indent=2).splitlines(keepends=True),
                    fromfile='output',
                    tofile='reference'
                )))


                
    else:
        print("Unit tests failed. Skipping integration tests.")

    return

if __name__ == '__main__':
    runTests()
