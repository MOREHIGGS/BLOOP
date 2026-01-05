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

echo "Compiling modules at loop order $LOOPORDER"
bloop --lastStage generateBenchmark --loopOrder $LOOPORDER || exit -1
echo "Profiling code"
python3 -m cProfile -o $OUTPUTFILE.pstats ../Source/RunStages.py --firstStage doMinimization || exit -1
gprof2dot --colour-nodes-by-selftime -f pstats $OUTPUTFILE.pstats | \dot -Tsvg -o $OUTPUTFILE.svg || exit -1
echo "Profile success, results stored in $OUTPUTFILE.svg"
rm $OUTPUTFILE.pstats || exit -1
