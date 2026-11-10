#!/usr/bin/env bash
if [ "$1" == "--V6" ]; then
    bloop --benchmarkType load --benchmarkFilePath dim6Benchmarks 
    --configFilePath Z2xZ2_3HDMConfigFile  --V6FilePath DRalgoOutputFiles/V6.txt \
    --bmGeneratorModule Z2xZ2_3HDMBmGenerator \
    --resultsDirectory Dim6 \
    --workers 5 --chunkSize 1 --loopOrder 2\
    --strengthCutOff 0.2  --bPlot \
    --TRangeStart 100 --TRangeStepSize 0.5 

else
    bloop --benchmarkType load --benchmarkFilePath dim6Benchmarks 
    --configFilePath Z2xZ2_3HDMConfigFile \
    --bmGeneratorModule Z2xZ2_3HDMBmGenerator \
    --resultsDirectory Dim6 \
    --workers 5 --chunkSize 1 --loopOrder 2\
    --strengthCutOff 0.2  --bPlot \
    --TRangeStart 100 --TRangeStepSize 0.5 
fi
