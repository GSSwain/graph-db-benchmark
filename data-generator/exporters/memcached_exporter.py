"""
Memcached Exporter: Graph-to-Adjacency-List Ingestion
"""
import os
import json
from collections import defaultdict
from typing import List, Dict, Any
from .base import BaseExporter

class MemcachedExporter(BaseExporter):
    def __init__(self, host: str = None, port: int = None, dump_dir: str = None, direct_ingest: bool = True):
        self.host = host or os.getenv("MEMCACHED_HOST", "localhost")
        self.port = int(port or os.getenv("MEMCACHED_PORT", "11211"))
        self.dump_dir = dump_dir
        self.direct_ingest = direct_ingest
        self.client = None

        if self.direct_ingest:
            try:
                from pymemcache.client.base import Client
                self.client = Client((self.host, self.port), connect_timeout=5, timeout=5)
                self.client.version()
                print(f"[MemcachedExporter] Connected directly to Memcached at {self.host}:{self.port}")
            except Exception as e:
                print(f"[MemcachedExporter] Direct connection warning: {e}. Writing dumps.")

        if self.dump_dir:
            os.makedirs(self.dump_dir, exist_ok=True)

    def export_vertices(self, vertex_type: str, vertices: List[Dict[str, Any]]):
        if not vertices:
            return
        records = {}
        for v in vertices:
            key = f"v:{vertex_type}:{v['id']}"
            records[key] = json.dumps(v)

        if self.client:
            self._set_multi_batched(records)
        if self.dump_dir:
            self._append_json_dump(f"vertices_{vertex_type}.jsonl", records)

    def export_edges(self, edge_type: str, edges: List[Dict[str, Any]]):
        if not edges:
            return
        src_key = "fromId"
        src_type = "Account"
        if edge_type == "own":
            src_key = "ownerId"
            src_type = "Person"
        elif edge_type == "signIn":
            src_key = "mediumId"
            src_type = "Medium"
        elif edge_type == "apply":
            src_key = "applicantId"
            src_type = "Person"
        elif edge_type == "deposit":
            src_key = "loanId"
            src_type = "Loan"

        grouped = defaultdict(list)
        for e in edges:
            s_id = e[src_key]
            grouped[s_id].append(e)

        records = {}
        for s_id, edge_list in grouped.items():
            key = f"adj:out:{src_type}:{s_id}:{edge_type}"
            records[key] = json.dumps(edge_list)

        if self.client:
            self._set_multi_batched(records)
        if self.dump_dir:
            self._append_json_dump(f"adj_{edge_type}.jsonl", records)

    def export_probes(self, probes: List[Dict[str, Any]]):
        target_dir = self.dump_dir or "."
        with open(os.path.join(target_dir, "probes.json"), "w") as f:
            json.dump(probes, f, indent=2)
        if self.client:
            try:
                self.client.set("finbench:probes", json.dumps(probes))
            except Exception:
                pass

    def _set_multi_batched(self, records: Dict[str, str], batch_size: int = 500):
        items = list(records.items())
        for i in range(0, len(items), batch_size):
            chunk = dict(items[i:i + batch_size])
            try:
                self.client.set_many(chunk)
            except Exception as e:
                print(f"[MemcachedExporter] set_many error: {e}")

    def _append_json_dump(self, filename: str, records: Dict[str, str]):
        path = os.path.join(self.dump_dir, filename)
        with open(path, "a", encoding="utf-8") as f:
            for k, val in records.items():
                f.write(json.dumps({"key": k, "value": val}) + "\n")

    def close(self):
        if self.client:
            self.client.close()
