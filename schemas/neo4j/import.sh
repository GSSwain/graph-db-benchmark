#!/bin/bash
set -e
NEO4J_HOST=${NEO4J_HOST:-localhost}
NEO4J_PORT=${NEO4J_PORT:-7687}
NEO4J_USER=${NEO4J_USER:-neo4j}
NEO4J_PASSWORD=${NEO4J_PASSWORD:-benchmarkpassword}

echo "==> Applying Neo4j LDBC FinBench Schema & Constraints..."
if command -v cypher-shell &> /dev/null; then
    cypher-shell -a "bolt://${NEO4J_HOST}:${NEO4J_PORT}" -u "${NEO4J_USER}" -p "${NEO4J_PASSWORD}" < $(dirname "$0")/schema.cypher
else
    docker exec -i neo4j cypher-shell -u "${NEO4J_USER}" -p "${NEO4J_PASSWORD}" < $(dirname "$0")/schema.cypher
fi
echo "==> Schema applied successfully."
