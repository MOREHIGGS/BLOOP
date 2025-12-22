import pytest
import sys
import subprocess
import json
import glob
import os

def runTests():
    unit_result = pytest.main(["PyTestUnitTests.py"])
    
    if unit_result == 0:
        loopOrderList = ["NLO", "NNLO"]
        for idx, loopOrder in enumerate(loopOrderList):
            print(f"Running {loopOrder} integration test:")
            for file in glob.glob(f"../Share/IntegrationTests/{loopOrder}/OutputResult/*"):
                os.remove(file)
            
            subprocess.run([
                sys.executable,
                'RunStages.py',
                '--loopOrder', f'{idx +1}', 
                '--firstBenchmark', '1',
                '--lastBenchmark', '1',
                '--bSave',
                '--resultsDirectory', f'../Share/IntegrationTests/{loopOrder}/OutputResult/',
                '--benchmarkFile', '../Share/IntegrationTests/Benchmarks',
                '--TRangeStart', '100', 
                '--TRangeStepSize', '2',
                '--gccFlags', 'O1',
                '--lastStage', 'doMinimization',
            ])

           
            with open(f"../Share/IntegrationTests/{loopOrder}/OutputResult/ScanResults.json", "r") as fp:
                scanResults = json.load(fp)
            with open(f"../Share/IntegrationTests/{loopOrder}/ReferenceResult/ScanResults.json", "r") as fp:
                scanResultsRef = json.load(fp)

            with open(f"../Share/IntegrationTests/{loopOrder}/OutputResult/BM_1.json", "r") as fp:
                bm1 = json.load(fp)
            with open(f"../Share/IntegrationTests/{loopOrder}/ReferenceResult/BM_1.json", "r") as fp:
                bm1Ref = json.load(fp)
        
            if bm1 == pytest.approx(bm1Ref, rel=0.) and scanResults ==  pytest.approx(scanResultsRef, rel=0.):
                print(f"{loopOrder} data is exactly what we expect")
        
            elif bm1 == pytest.approx(bm1Ref, rel=0.01):
                print(f"{loopOrder} data is within 1% of what we expect")
        
            else:
                print(f"""{loopOrder} data is outside 1% of what we expect. \n 
                       Please do a diff for further deatils""")

    else:
        print("Unit tests failed. Skipping integration tests.")

    return

if __name__ == '__main__':
    runTests()
