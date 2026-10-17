"""
Benchmark Configuration & Default Parameters
"""
import os
from typing import List

# Default hop progression testing depth 1 to 100
DEFAULT_HOPS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 30, 40, 50, 75, 100]

class BenchmarkConfig:
    def __init__(
        self,
        engines: List[str] = None,
        hops: List[int] = None,
        concurrency: int = 1,
        iterations: int = 10,
        warmup_runs: int = 3,
        timeout_sec: float = 30.0,
        probes_file: str = "data/probes.json",
        report_dir: str = "reports"
    ):
        self.engines = engines or ["neo4j", "memcached"]
        self.hops = sorted(hops or DEFAULT_HOPS)
        self.concurrency = concurrency
        self.iterations = iterations
        self.warmup_runs = warmup_runs
        self.timeout_sec = timeout_sec
        self.probes_file = probes_file
        self.report_dir = report_dir

        # Connection settings from environment
        self.neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "benchmarkpassword")

        self.memcached_host = os.getenv("MEMCACHED_HOST", "localhost")
        self.memcached_port = int(os.getenv("MEMCACHED_PORT", "11211"))

        self.neptune_endpoint = os.getenv("NEPTUNE_ENDPOINT", "ws://localhost:8182/gremlin")
        self.spanner_instance = os.getenv("SPANNER_INSTANCE", "finbench-instance")
        self.spanner_database = os.getenv("SPANNER_DATABASE", "finbench-db")
        self.cosmos_endpoint = os.getenv("COSMOS_ENDPOINT", "ws://localhost:8182/gremlin")
