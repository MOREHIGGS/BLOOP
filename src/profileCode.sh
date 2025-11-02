#!/bin/bash

LOOPORDER="1"
OUTPUTFILE="profile"

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --loopOrder"
    echo "  --outputFileName"
    echo "  -h, --help"
    exit 1
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --loopOrder)
            LOOPORDER="$2"
            shift 2
            ;;
        --outputFile)
            OUTPUTFILE="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Error: Unknown option: $1"
            usage
            ;;
    esac
done

echo "Compiling modules"
python3 runStages.py --lastStage generateBenchmark --loopOrder $LOOPORDER || exit -1
echo "Profiling code"
python3 -m cProfile -o $OUTPUTFILE.pstats runStages.py --firstStage doMinimization || exit -1
gprof2dot --colour-nodes-by-selftime -f pstats $OUTPUTFILE.pstats | \dot -Tsvg -o $OUTPUTFILE.svg || exit -1
echo "Profile success"
rm $OUTPUTFILE.pstats || exit -1
