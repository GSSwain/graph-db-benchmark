#!/usr/bin/env python3
"""
LDBC FinBench - Standalone Database Infrastructure Cost Estimator CLI
Calculates and compares DB infrastructure costs across Neo4j, Memcached, Neptune, Spanner, and Cosmos DB.
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "test-runner"))
from reporting.cost_estimator import CostEstimator, SCALE_PRESETS, PRICING_CATALOG

def main():
    parser = argparse.ArgumentParser(description="LDBC FinBench Database Infrastructure Cost Estimator")
    parser.add_argument("--preset", type=str, default="medium", choices=list(SCALE_PRESETS.keys()) + ["all"],
                        help="Scale preset: dev, local, medium, cloud, full, all")
    parser.add_argument("--qps", type=float, default=1000.0, help="Target read throughput (QPS)")
    parser.add_argument("--hours", type=float, default=730.0, help="Operating hours (default: 730 = 1 month)")
    parser.add_argument(
        "--neo4j-license-usd-per-core-month", type=float, default=0.0,
        help="Quoted Neo4j Enterprise license price per core per month (default: 0, not priced)"
    )
    args = parser.parse_args()

    estimator = CostEstimator(neo4j_license_usd_per_core_month=args.neo4j_license_usd_per_core_month)
    presets_to_evaluate = list(SCALE_PRESETS.keys()) if args.preset == "all" else [args.preset]

    print("=" * 105)
    print("           LDBC FINBENCH DATABASE INFRASTRUCTURE COST ESTIMATION (DB ONLY)")
    print(f" Target Sustained Throughput : {args.qps:,.0f} QPS")
    print("=" * 105)

    for p in presets_to_evaluate:
        p_info = SCALE_PRESETS[p]
        footprint = estimator.estimate_data_footprint(p)
        costs = estimator.estimate_monthly_infra_cost(p, target_qps=args.qps)

        print(f"\n[ Scale Preset: {p.upper()} - {p_info['name']} ]")
        print(f"  Graph Scale    : {p_info['persons']:,} Persons | {p_info['accounts']:,} Accounts | {p_info['transfers']:,} Transfers")
        print(f"  Raw Data Size  : {p_info['raw_data_gb']:,} GB raw CSV")
        print("-" * 105)
        print(f"{'Database Engine':<12} | {'Monthly Cost':<14} | {'Hourly Cost':<12} | {'Cost/1M Reads':<14} | {'Provisioned Sizing Specification':<45}")
        print("-" * 105)

        for eng, c in costs.items():
            cost_per_1m = (c['hourly_cost_usd'] / (3600.0 * max(1.0, args.qps))) * 1_000_000.0
            print(f"{eng:<12} | ${c['monthly_cost_usd']:>12,.2f} | ${c['hourly_cost_usd']:>10.4f} | ${cost_per_1m:>12.4f} | {c['spec']:<45}")
        print("-" * 105)

    print("\n[Pricing Models & Architectural Cost Drivers]")
    print("  * Neo4j       : 3 self-hosted HA nodes with 12 assumed vCPUs; licensing uses the supplied per-core quote.")
    if args.neo4j_license_usd_per_core_month == 0:
        print("                 License cost is not priced; provide --neo4j-license-usd-per-core-month from your Neo4j quote.")
    print("  * Memcached   : In-memory adjacency list cache (AWS ElastiCache cache.r6g) - zero disk I/O charges.")
    print("  * AWS Neptune : Multi-AZ instance compute + cluster storage ($0.10/GB) + request I/O ($0.20/1M I/O).")
    print("  * GCP Spanner : Spanner Nodes ($0.90/node-hr, 10k QPS per node) + SSD storage ($0.30/GB).")
    print("  * Cosmos DB   : Provisioned Request Units ($0.08/1k RU/s-hr, ~15 RU/hop) + transactional storage ($0.25/GB).")
    print("=" * 105)

if __name__ == "__main__":
    main()
