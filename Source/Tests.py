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
        TStart = [100, 50]
        TStep = [2, 10]
        TEnd = [200,100]
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
                '--TRangeStart', f'{TStart[idx]}', 
                '--TRangeStepSize', f'{TStep[idx]}',
                '--TRangeEnd', f'{TEnd[idx]}',
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
                continue
        
            elif bm1 == pytest.approx(bm1Ref, rel=0.01):
                print(f"{loopOrder} data is within 1% of what we expect")
        
            else:
                print(f"{loopOrder} data is outside 1% of what we expect.")
            
            print(f"Please see {loopOrder}Diff.txt to see the actual diff")
            import difflib
            diff = difflib.unified_diff(
               json.dumps(bm1, indent=2).splitlines(keepends=True),
               json.dumps(bm1Ref, indent=2).splitlines(keepends=True),
               fromfile='reference',
               tofile='output'
               )
            print()
            print()
            print(''.join(diff))
    else:
        print("Unit tests failed. Skipping integration tests.")

    return

if __name__ == '__main__':
    runTests()
