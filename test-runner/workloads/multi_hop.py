"""
Multi-Hop Read Traversal Workload (1 to 100 Hops)
Evaluates latency degradation, tail percentiles, and throughput scaling
across variable path lengths.
"""
import os
import json
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
from reporting.metrics import BenchmarkMetrics

class MultiHopWorkload:
    def __init__(self, probes_file: str = "data/probes.json"):
        self.probes = self._load_probes(probes_file)

    def _load_probes(self, path: str) -> List[Dict[str, Any]]:
        # Search candidate probe locations
        candidates = [path, "test_data/neo4j/probes.json", "test_data/memcached/probes.json", "data/neo4j/probes.json"]
        for p in candidates:
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    pass
        # Default fallback probes if file not found
        return [
            {"start_account_id": 1, "target_account_id": 101, "depth": 100, "intermediate_accounts": list(range(1, 102))},
            {"start_account_id": 2, "target_account_id": 102, "depth": 100, "intermediate_accounts": list(range(2, 103))}
        ]

    def execute(
        self,
        adapter: Any,
        hops: List[int],
        iterations: int = 10,
        warmup_runs: int = 3,
        concurrency: int = 1,
        mode: str = "path_trace"
    ) -> Dict[int, Dict[str, Any]]:
        results = {}

        # 1. Warmup
        warmup_start = self.probes[0]["start_account_id"]
        for _ in range(warmup_runs):
            adapter.warmup(warmup_start)

        # 2. Iterate through each hop depth k
        for k in hops:
            latencies = []
            error_count = 0
            t_start = time.time()

            def run_single(idx: int):
                probe = self.probes[idx % len(self.probes)]
                s_id = probe["start_account_id"]
                # If probe has intermediate accounts, pick exact target at depth k
                inter = probe.get("intermediate_accounts", [])
                t_id = inter[min(k, len(inter) - 1)] if inter else probe.get("target_account_id", s_id + k)
                return adapter.run_multi_hop(start_id=s_id, target_id=t_id, depth=k, mode=mode)

            if concurrency <= 1:
                for i in range(iterations):
                    res = run_single(i)
                    if res.get("success", False):
                        latencies.append(res["latency_ms"])
                    else:
                        error_count += 1
            else:
                with ThreadPoolExecutor(max_workers=concurrency) as pool:
                    futures = [pool.submit(run_single, i) for i in range(iterations)]
                    for fut in futures:
                        try:
                            res = fut.result()
                            if res.get("success", False):
                                latencies.append(res["latency_ms"])
                            else:
                                error_count += 1
                        except Exception:
                            error_count += 1

            total_duration = time.time() - t_start
            m = BenchmarkMetrics.calculate(latencies, total_duration, error_count)
            results[k] = m
            print(f"  [{adapter.name}] Depth {k:3d} Hops -> p50: {m['p50_ms']:7.2f} ms | p99: {m['p99_ms']:7.2f} ms | QPS: {m['qps']:6.1f} | Errors: {m['error_count']}")

        return results
