import pytest
import sys
import subprocess
import json

def runTests():
    unit_result = pytest.main(["PyTestUnitTests.py"])
    
    if unit_result == 0: 
        print("Unit tests passed. Running integration tests...")
        subprocess.run([
            sys.executable,
            'RunStages.py',
            '--loopOrder', '1', 
            '--firstBenchmark', '1',
            '--lastBenchmark', '1',
            '--bSave',
            '--resultsDirectory', '../Share/IntegrationTests/NLO/OutputResult/',
            '--benchmarkFile', '../Share/IntegrationTests/Benchmarks',
            '--TRangeStart', '100', 
            '--TRangeStepSize', '2',
            '--gccFlags', 'O1',
        ])
        with open("../Share/IntegrationTests/NLO/OutputResult/BM_1.json", "r") as fp:
            data = json.load(fp)
        with open("../Share/IntegrationTests/NLO/ReferenceResult/BM_1.json", "r") as fp:
            reference = json.load(fp)
        print( data == pytest.approx(reference, rel=0.01) )
    else:
        print("Unit tests failed. Skipping integration tests.")

    return

if __name__ == '__main__':
    runTests()
