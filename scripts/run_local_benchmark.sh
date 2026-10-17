#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENGINES=${1:-"neo4j,memcached"}
HOPS=${2:-"1,2,3,4,5,10,20,50,100"}
ITERATIONS=${3:-10}

echo "--> Executing benchmark on: $ENGINES across hops: $HOPS"
python3 test-runner/runner.py --engines "$ENGINES" --hops "$HOPS" --iterations "$ITERATIONS" --output-dir reports
