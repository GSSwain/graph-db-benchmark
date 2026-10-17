#!/usr/bin/env bash
# =====================================================================
# LDBC FinBench Quickstart: Starts Neo4j & Memcached, Generates Data,
# Benchmarks Multi-Hop Reads (1 to 100 Hops), and Generates Reports.
# =====================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

echo "======================================================================="
echo "  LDBC FINBENCH MULTI-ENGINE GRAPH BENCHMARK (1 TO 100 HOPS)"
echo "======================================================================="

# 1. Start Docker Containers for Neo4j and Memcached
echo "--> 1. Starting Neo4j and Memcached containers..."
docker compose up -d neo4j memcached

echo "--> 2. Waiting for database containers to become healthy..."
RETRIES=30
until docker compose exec -T neo4j cypher-shell -u neo4j -p benchmarkpassword "RETURN 1" >/dev/null 2>&1 || [ $RETRIES -eq 0 ]; do
  echo "    Waiting for Neo4j to be ready... ($RETRIES retries left)"
  sleep 2
  RETRIES=$((RETRIES-1))
done

if [ $RETRIES -eq 0 ]; then
  echo "[ERROR] Neo4j failed to start."
  exit 1
fi
echo "    [OK] Neo4j is ready."

# 2. Apply Schema & Constraints to Neo4j
echo "--> 3. Applying LDBC FinBench schema and constraints to Neo4j..."
docker compose exec -T neo4j cypher-shell -u neo4j -p benchmarkpassword < "$ROOT_DIR/schemas/neo4j/schema.cypher" || true
echo "    [OK] Schema applied."

# 3. Generate Synthetic FinBench Data & Ground Truth 100-Hop Chains
echo "--> 4. Generating FinBench data & 100-hop AML ground-truth trails..."
docker compose run --rm data-generator --preset dev --target neo4j,memcached --export-dir data --deep-hops 100 --chains 10

# 4. Run Benchmark Runner Container
echo "--> 5. Running Multi-Hop Benchmark (1 to 100 Hops) across Neo4j & Memcached..."
docker compose run --rm test-runner --engines neo4j,memcached --hops 1,2,3,4,5,6,7,8,9,10,15,20,30,40,50,75,100 --iterations 10 --output-dir reports

echo "======================================================================="
echo "  BENCHMARK COMPLETE!"
echo "  View the interactive HTML report at:"
echo "  file://$ROOT_DIR/reports/benchmark_report.html"
echo "======================================================================="
