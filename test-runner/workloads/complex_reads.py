"""
LDBC FinBench Transaction Complex Reads (CR1 to CR3) Workload
"""
import time
from typing import Dict, Any, List
from reporting.metrics import BenchmarkMetrics

class ComplexReadsWorkload:
    def __init__(self):
        self.queries = ["CR1", "CR2", "CR3"]

    def execute(self, adapter: Any, iterations: int = 5) -> Dict[str, Dict[str, Any]]:
        results = {}
        for q in self.queries:
            latencies = []
            errors = 0
            t_start = time.time()
            for i in range(iterations):
                res = adapter.run_complex_read(q, {"account_id": 1, "person_id": 1, "medium_id": 1})
                if res.get("success", False):
                    latencies.append(res["latency_ms"])
                else:
                    errors += 1
            dur = time.time() - t_start
            results[q] = BenchmarkMetrics.calculate(latencies, dur, errors)
        return results
