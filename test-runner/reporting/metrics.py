"""
Statistical Metrics Calculations for Benchmark Execution
"""
import math
from typing import List, Dict, Any

class BenchmarkMetrics:
    @staticmethod
    def calculate(latencies_ms: List[float], total_duration_sec: float, error_count: int = 0) -> Dict[str, Any]:
        if not latencies_ms:
            return {
                "count": 0,
                "success_count": 0,
                "error_count": error_count,
                "error_rate_pct": 100.0 if error_count > 0 else 0.0,
                "qps": 0.0,
                "min_ms": 0.0,
                "p50_ms": 0.0,
                "p90_ms": 0.0,
                "p95_ms": 0.0,
                "p99_ms": 0.0,
                "p999_ms": 0.0,
                "max_ms": 0.0,
                "mean_ms": 0.0,
                "stddev_ms": 0.0
            }

        sorted_lat = sorted(latencies_ms)
        n = len(sorted_lat)
        total_ops = n + error_count
        qps = n / max(0.001, total_duration_sec)

        def pct(p: float) -> float:
            idx = int(math.ceil(p * n) - 1)
            return sorted_lat[max(0, min(idx, n - 1))]

        mean_val = sum(sorted_lat) / n
        variance = sum((x - mean_val) ** 2 for x in sorted_lat) / max(1, n - 1)
        stddev = math.sqrt(variance)

        return {
            "count": total_ops,
            "success_count": n,
            "error_count": error_count,
            "error_rate_pct": (error_count / total_ops) * 100.0,
            "qps": round(qps, 2),
            "min_ms": round(sorted_lat[0], 3),
            "p50_ms": round(pct(0.50), 3),
            "p90_ms": round(pct(0.90), 3),
            "p95_ms": round(pct(0.95), 3),
            "p99_ms": round(pct(0.99), 3),
            "p999_ms": round(pct(0.999), 3),
            "max_ms": round(sorted_lat[-1], 3),
            "mean_ms": round(mean_val, 3),
            "stddev_ms": round(stddev, 3)
        }
