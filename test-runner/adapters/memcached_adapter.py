import time
import json
from typing import Dict, Any, List
from .base import BaseBenchmarkAdapter

class MemcachedBenchmarkAdapter(BaseBenchmarkAdapter):
    def __init__(self, host: str = "localhost", port: int = 11211, mode: str = "multiget", beam_width: int = 5):
        self.mode = mode.lower() # "multiget" or "dfs"
        name = "Memcached-MultiGet" if self.mode == "multiget" else "Memcached-DFS"
        super().__init__(name)
        self.host = host
        self.port = port
        self.beam_width = beam_width
        self.client = None

    def connect(self) -> bool:
        try:
            from pymemcache.client.base import Client
            self.client = Client((self.host, self.port), connect_timeout=5, timeout=5)
            self.client.version()
            return True
        except Exception as e:
            print("[" + self.name + "] Connection failed: " + str(e))
            return False

    def warmup(self, start_id: int):
        if not self.client:
            return
        try:
            self.client.get("adj:out:Account:" + str(start_id) + ":transfer")
        except Exception:
            pass

    def run_multi_hop(self, start_id: int, target_id: int, depth: int, mode: str = "path_trace") -> Dict[str, Any]:
        if not self.client:
            return {"success": False, "latency_ms": 0.0, "result_count": 0, "error": "Not connected"}

        t0 = time.perf_counter_ns()
        try:
            if self.mode == "dfs":
                # Single-Key Recursive DFS Path Tracing
                current = start_id
                visited = [current]
                for hop in range(depth):
                    val = self.client.get("adj:out:Account:" + str(current) + ":transfer")
                    if not val:
                        break
                    if isinstance(val, bytes):
                        val = val.decode("utf-8")
                    edge_list = json.loads(val)
                    if not edge_list:
                        break
                    next_node = edge_list[0].get("toId") or edge_list[0].get("dst")
                    visited.append(next_node)
                    current = next_node

                lat_ms = (time.perf_counter_ns() - t0) / 1000000.0
                return {"success": True, "latency_ms": lat_ms, "result_count": len(visited), "error": None}

            else:
                # Pipelined BFS Multi-Get
                frontier = [start_id]
                visited = set(frontier)
                found_target = False

                for hop in range(depth):
                    batch_keys = ["adj:out:Account:" + str(aid) + ":transfer" for aid in frontier]
                    raw_results = self.client.get_many(batch_keys)

                    next_frontier = []
                    for val in raw_results.values():
                        if not val:
                            continue
                        if isinstance(val, bytes):
                            val = val.decode("utf-8")
                        edge_list = json.loads(val)
                        for edge in edge_list[:self.beam_width]:
                            dst = edge.get("toId") or edge.get("dst")
                            if dst == target_id:
                                found_target = True
                            if dst not in visited:
                                visited.add(dst)
                                next_frontier.append(dst)

                    if not next_frontier:
                        break
                    frontier = next_frontier

                lat_ms = (time.perf_counter_ns() - t0) / 1000000.0
                cnt = 1 if (mode == "reachability" and found_target) else len(frontier)
                return {"success": True, "latency_ms": lat_ms, "result_count": cnt, "error": None}
        except Exception as e:
            lat_ms = (time.perf_counter_ns() - t0) / 1000000.0
            return {"success": False, "latency_ms": lat_ms, "result_count": 0, "error": str(e)}

    def run_complex_read(self, query_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if not self.client:
            return {"success": False, "latency_ms": 0.0, "result_count": 0, "error": "Not connected"}
        t0 = time.perf_counter_ns()
        try:
            account_id = params.get("account_id", 1)
            raw = self.client.get("adj:out:Account:" + str(account_id) + ":transfer")
            cnt = 0
            if raw:
                if isinstance(raw, bytes):
                    raw = raw.decode("utf-8")
                edges = json.loads(raw)
                cnt = len(edges)
            lat_ms = (time.perf_counter_ns() - t0) / 1000000.0
            return {"success": True, "latency_ms": lat_ms, "result_count": cnt, "error": None}
        except Exception as e:
            lat_ms = (time.perf_counter_ns() - t0) / 1000000.0
            return {"success": False, "latency_ms": lat_ms, "result_count": 0, "error": str(e)}

    def close(self):
        if self.client:
            self.client.close()
