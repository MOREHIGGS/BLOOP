#!/usr/bin/env bash
if [ "$1" == "--V6" ]; then
    bloop --benchmarkType load --benchmarkFilePath dim6Benchmarks.json\
    --configFilePath Z2xZ2_3HDMConfigFile.json  --V6FilePath DRalgoOutputFiles/V6.txt \
    --bmGeneratorModule Z2xZ2_3HDMBmGenerator \
    --resultsDirectory Dim6 \
    --workers 1 --chunkSize 1 --loopOrder 2\
    --strengthCutOff 0.2  --bPlot \
    --TRangeStart 100 --TRangeStepSize 0.5 --bPlot

else
    bloop --benchmarkType load --benchmarkFilePath dim6Benchmarks.json \
    --configFilePath Z2xZ2_3HDMConfigFile.json \
    --bmGeneratorModule Z2xZ2_3HDMBmGenerator \
    --resultsDirectory Dim6 \
    --workers 5 --chunkSize 1 --loopOrder 2\
    --strengthCutOff 0.2  --bPlot \
    --TRangeStart 100 --TRangeStepSize 0.5 --bPlot 
fi
