#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Fine tests providing partial coverage
echo Unit tests...
python3 -m Source.UnitTests

echo Intergration tests...
# Super coarse test providing full coverage
echo Running code at NLO...
rm -f $SCRIPT_DIR/IntegrationTests/Pool/OutputResult/* 
rm -f $SCRIPT_DIR/IntegrationTests/Benchmarks/*

bloop --loopOrder 1 \
      --firstBenchmark 1 \
      --lastBenchmark 1 \
      --bSave \
      --resultsDirectory $SCRIPT_DIR/IntegrationTests/Pool/OutputResult/  \
      --benchmarkFile $SCRIPT_DIR/IntegrationTests/Benchmarks \
      --benchmarkType handPicked \
      --TRangeStart 100 \
      --TRangeEnd 200 \
      --TRangeStepSize 2 \
      --gccFlags O1
diff $SCRIPT_DIR/IntegrationTests/Pool/OutputResult/BM_1.json $SCRIPT_DIR/IntegrationTests/Pool/ReferenceResult/BM_1.json

echo Running code at NLO using 2 workers...
rm -f  $SCRIPT_DIR/IntegrationTests/Pool2/OutputResult/* 
rm -f  $SCRIPT_DIR/IntegrationTests/Benchmarks/*

bloop --loopOrder 1 \
      --firstBenchmark 0 \
      --lastBenchmark 3 \
      --bSave \
      --resultsDirectory $SCRIPT_DIR/IntegrationTests/Pool2/OutputResult/  \
      --benchmarkFile $SCRIPT_DIR/IntegrationTests/Benchmarks \
      --benchmarkType handPicked \
      --TRangeStart 100 \
      --TRangeEnd 200 \
      --TRangeStepSize 2 \
      --workers 2 \
      --gccFlags O1

diff $SCRIPT_DIR/IntegrationTests/Pool2/OutputResult/BM_0.json $SCRIPT_DIR/IntegrationTests/Pool2/ReferenceResult/BM_0.json
diff $SCRIPT_DIR/IntegrationTests/Pool2/OutputResult/BM_1.json $SCRIPT_DIR/IntegrationTests/Pool2/ReferenceResult/BM_1.json
diff $SCRIPT_DIR/IntegrationTests/Pool2/OutputResult/BM_2.json $SCRIPT_DIR/IntegrationTests/Pool2/ReferenceResult/BM_2.json
diff $SCRIPT_DIR/IntegrationTests/Pool2/OutputResult/BM_3.json $SCRIPT_DIR/IntegrationTests/Pool2/ReferenceResult/BM_3.json

echo Running code at NNLO...
rm -f  $SCRIPT_DIR/IntegrationTests/NNLO/OutputResult/* 
rm -f  $SCRIPT_DIR/IntegrationTests/Benchmarks/*

bloop --loopOrder 2 \
      --firstBenchmark 1 \
      --lastBenchmark 1 \
      --bSave \
      --resultsDirectory $SCRIPT_DIR/IntegrationTests/NNLO/OutputResult/ \
      --benchmarkFile $SCRIPT_DIR/IntegrationTests/Benchmarks \
      --benchmarkType handPicked \
      --TRangeStart 50 \
      --TRangeEnd 100 \
      --TRangeStepSize 10 \
      --bProcessMin \
      --gccFlags O1

diff $SCRIPT_DIR/IntegrationTests/NNLO/OutputResult/BM_1.json $SCRIPT_DIR/IntegrationTests/NNLO/ReferenceResult/BM_1.json
diff $SCRIPT_DIR/IntegrationTests/NNLO/OutputResult/BM_1_interp.json $SCRIPT_DIR/IntegrationTests/NNLO/ReferenceResult/BM_1_interp.json

