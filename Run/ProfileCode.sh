#!/bin/bash

LOOPORDER="1"
OUTPUTFILE="profile"
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
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

echo "Generating 20 random benchmarks and compiling modules at loop order $LOOPORDER"
bloop --lastStage generateBenchmark --benchmarkType random --randomNum 20 --loopOrder $LOOPORDER || exit -1
echo "Profiling code"
OMP_NUM_THREADS=1 python3 -m cProfile -o $OUTPUTFILE.pstats $SCRIPT_DIR/../Source/RunStages.py --profile --firstStage doMinimization --lastStage doMinimization || exit -1
gprof2dot --colour-nodes-by-selftime -f pstats $OUTPUTFILE.pstats | \dot -Tsvg -o $OUTPUTFILE.svg || exit -1
echo "Profile success, results stored in $OUTPUTFILE.svg"
rm $OUTPUTFILE.pstats || exit -1
