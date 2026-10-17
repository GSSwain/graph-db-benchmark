import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
"""
Main Benchmark Orchestrator & CLI Runner supporting Multiple Query Languages
"""
import os
import sys
import argparse
from typing import List, Dict, Any

from config import BenchmarkConfig, DEFAULT_HOPS
from adapters.neo4j_adapter import Neo4jBenchmarkAdapter
from adapters.memcached_adapter import MemcachedBenchmarkAdapter
from adapters.neptune_adapter import NeptuneBenchmarkAdapter
from adapters.spanner_adapter import SpannerBenchmarkAdapter
from adapters.cosmos_adapter import CosmosBenchmarkAdapter
from workloads.multi_hop import MultiHopWorkload
from workloads.complex_reads import ComplexReadsWorkload
from reporting.reporter import BenchmarkReporter

# Mapping of engine alias to query language variants
ENGINE_VARIANTS = {
    "neo4j": ["neo4j-cypher", "neo4j-trail"],
    "memcached": ["memcached-multiget", "memcached-dfs"],
    "neptune": ["neptune-gremlin", "neptune-opencypher"],
    "spanner": ["spanner-gql", "spanner-sql"],
    "cosmos": ["cosmos-gremlin", "cosmos-sql"]
}

def parse_args():
    parser = argparse.ArgumentParser(description="LDBC FinBench Multi-Engine & Multi-Language Graph Benchmark Runner")
    parser.add_argument("--engines", type=str, default="neo4j,memcached", help="Target engines & query languages: neo4j (cypher, apoc), memcached (multiget, dfs), neptune (gremlin, opencypher), spanner (gql, sql), cosmos (gremlin, sql), all")
    parser.add_argument("--hops", type=str, default=None, help="Comma-separated hop depths (e.g. 1,2,3,5,10,20,50,100)")
    parser.add_argument("--hop-range", type=int, nargs=2, default=None, help="Start and End hop depth (e.g. --hop-range 1 100)")
    parser.add_argument("--hop-step", type=int, default=1, help="Step for hop range (e.g. 1, 5, 10)")
    parser.add_argument("--iterations", type=int, default=10, help="Number of query iterations per hop depth")
    parser.add_argument("--warmup", type=int, default=3, help="Warmup iterations per engine")
    parser.add_argument("--concurrency", type=int, default=1, help="Concurrent client threads")
    parser.add_argument("--mode", type=str, default="path_trace", choices=["path_trace", "reachability", "shortest_path"], help="Traversal query pattern")
    parser.add_argument("--probes", type=str, default="data/probes.json", help="Path to probes.json containing ground truth deep chains")
    parser.add_argument("--output-dir", type=str, default="reports", help="Output directory for reports")
    parser.add_argument("--html-output-dir", type=str, default="docs", help="Output directory for GitHub Pages HTML reports")
    parser.add_argument("--preset", type=str, default="dev", choices=["dev", "local", "medium", "cloud", "full"], help="Data scale preset for database infrastructure cost estimation")
    parser.add_argument(
        "--neo4j-license-usd-per-core-month", type=float, default=0.0,
        help="Quoted Neo4j Enterprise license price per core per month (default: 0, not priced)"
    )
    return parser.parse_args()

def expand_engine_targets(requested_tokens: List[str]) -> List[str]:
    expanded = []
    for token in requested_tokens:
        t = token.lower().strip()
        if t == "all":
            for variants in ENGINE_VARIANTS.values():
                expanded.extend(variants)
        elif t in ENGINE_VARIANTS:
            expanded.extend(ENGINE_VARIANTS[t])
        else:
            expanded.append(t)
    # Deduplicate while preserving order
    seen = set()
    result = []
    for x in expanded:
        if x not in seen:
            seen.add(x)
            result.append(x)
    return result

def instantiate_adapter(target_name: str, config: BenchmarkConfig) -> Any:
    t = target_name.lower().strip()
    # Neo4j variants
    if t == "neo4j-cypher" or t == "neo4j":
        return Neo4jBenchmarkAdapter(uri=config.neo4j_uri, auth=(config.neo4j_user, config.neo4j_password), language="cypher")
    elif t in ("neo4j-trail", "neo4j-directedtrail"):
        return Neo4jBenchmarkAdapter(uri=config.neo4j_uri, auth=(config.neo4j_user, config.neo4j_password), language="trail")
    elif t == "neo4j-apoc":
        return Neo4jBenchmarkAdapter(uri=config.neo4j_uri, auth=(config.neo4j_user, config.neo4j_password), language="apoc")
    elif t == "neo4j-shortestpath":
        return Neo4jBenchmarkAdapter(uri=config.neo4j_uri, auth=(config.neo4j_user, config.neo4j_password), language="shortestpath")

    # Memcached variants
    elif t == "memcached-multiget" or t == "memcached":
        return MemcachedBenchmarkAdapter(host=config.memcached_host, port=config.memcached_port, mode="multiget")
    elif t == "memcached-dfs":
        return MemcachedBenchmarkAdapter(host=config.memcached_host, port=config.memcached_port, mode="dfs")

    # Neptune variants
    elif t == "neptune-gremlin" or t == "neptune":
        return NeptuneBenchmarkAdapter(endpoint=config.neptune_endpoint, language="gremlin")
    elif t == "neptune-opencypher":
        return NeptuneBenchmarkAdapter(endpoint=config.neptune_endpoint, language="opencypher")
    elif t == "neptune-sparql":
        return NeptuneBenchmarkAdapter(endpoint=config.neptune_endpoint, language="sparql")

    # Spanner variants
    elif t == "spanner-gql" or t == "spanner":
        return SpannerBenchmarkAdapter(instance_id=config.spanner_instance, database_id=config.spanner_database, language="gql")
    elif t == "spanner-sql":
        return SpannerBenchmarkAdapter(instance_id=config.spanner_instance, database_id=config.spanner_database, language="sql")

    # Cosmos variants
    elif t == "cosmos-gremlin" or t == "cosmos":
        return CosmosBenchmarkAdapter(endpoint=config.cosmos_endpoint, language="gremlin")
    elif t == "cosmos-sql":
        return CosmosBenchmarkAdapter(endpoint=config.cosmos_endpoint, language="sql")

    return None

def main():
    args = parse_args()

    # Determine hops list
    if args.hops:
        hops = [int(h.strip()) for h in args.hops.split(",")]
    elif args.hop_range:
        start_h, end_h = args.hop_range
        hops = list(range(start_h, end_h + 1, args.hop_step))
        if end_h not in hops:
            hops.append(end_h)
    else:
        hops = DEFAULT_HOPS

    raw_tokens = [e.strip() for e in args.engines.split(",")]
    target_languages = expand_engine_targets(raw_tokens)

    config = BenchmarkConfig(
        engines=target_languages,
        hops=hops,
        concurrency=args.concurrency,
        iterations=args.iterations,
        warmup_runs=args.warmup,
        probes_file=args.probes,
        report_dir=args.output_dir
    )

    print("===================================================================================")
    print("      LDBC FINBENCH MULTI-ENGINE & MULTI-QUERY-LANGUAGE GRAPH BENCHMARK            ")
    print(" Target Query Paradigms : " + ", ".join(target_languages))
    print(" Hop Depths Tested      : " + str(len(hops)) + " levels -> " + str(hops))
    print(" Concurrency            : " + str(config.concurrency) + " thread(s)")
    print(" Iterations             : " + str(config.iterations) + " per hop depth (warmup: " + str(config.warmup_runs) + ")")
    print(" Traversal Mode         : " + args.mode)
    print("===================================================================================")

    # Initialize Adapters
    adapters = []
    for tgt in target_languages:
        ad = instantiate_adapter(tgt, config)
        if ad:
            adapters.append(ad)

    # Connect and filter active adapters
    active_adapters = []
    for ad in adapters:
        print("--> Testing connection to [" + ad.name + "]...")
        if ad.connect():
            print("    [OK] Connected to [" + ad.name + "] successfully.")
            active_adapters.append(ad)
        else:
            print("    [SKIP] Could not connect to [" + ad.name + "]. Ensure container/cloud instance is active.")

    if not active_adapters:
        print("\n[!] No database engines were reachable. Please start the target containers:")
        print("    docker compose up -d neo4j memcached")
        print("    or run: ./scripts/quickstart.sh")
        sys.exit(1)

    workload = MultiHopWorkload(probes_file=config.probes_file)
    results = {}

    for ad in active_adapters:
        print("\n===================================================================================")
        print(" Running Multi-Hop Benchmark (1 to 100 Hops) on [" + ad.name + "]...")
        print("===================================================================================")
        hop_results = workload.execute(
            adapter=ad,
            hops=config.hops,
            iterations=config.iterations,
            warmup_runs=config.warmup_runs,
            concurrency=config.concurrency,
            mode=args.mode
        )
        results[ad.name] = hop_results

    # Generate Reports
    reporter = BenchmarkReporter(
        output_dir=config.report_dir,
        neo4j_license_usd_per_core_month=args.neo4j_license_usd_per_core_month,
        html_output_dir=args.html_output_dir
    )
    reporter.print_terminal_summary(results)
    reporter.generate_reports(results, config, scale_preset=args.preset)

    # Close adapters
    for ad in active_adapters:
        ad.close()

    print("\n==> Multi-Language Benchmark completed successfully!")

if __name__ == "__main__":
    main()
