#!/usr/bin/env bash
# Connectivity Verification Probe for all 5 Target Engines
set -euo pipefail

echo "======================================================================="
echo "  FinBench Database Engines Connectivity Diagnostics"
echo "======================================================================="

# Neo4j
echo -n "  Neo4j (bolt://localhost:7687)             : "
if nc -z 127.0.0.1 7687 2>/dev/null; then echo "[AVAILABLE]"; else echo "[NOT DETECTED]"; fi

# Memcached
echo -n "  Memcached (localhost:11211)               : "
if nc -z 127.0.0.1 11211 2>/dev/null; then echo "[AVAILABLE]"; else echo "[NOT DETECTED]"; fi

# AWS Neptune Emulator / Gremlin Server
echo -n "  AWS Neptune Gremlin (localhost:8182)      : "
if nc -z 127.0.0.1 8182 2>/dev/null; then echo "[AVAILABLE]"; else echo "[NOT DETECTED]"; fi

# GCP Spanner Emulator
echo -n "  GCP Spanner Emulator (localhost:9010)     : "
if nc -z 127.0.0.1 9010 2>/dev/null; then echo "[AVAILABLE]"; else echo "[NOT DETECTED]"; fi

# Azure Cosmos DB Emulator
echo -n "  Azure Cosmos DB Emulator (localhost:8081) : "
if nc -z 127.0.0.1 8081 2>/dev/null; then echo "[AVAILABLE]"; else echo "[NOT DETECTED]"; fi

echo "======================================================================="
