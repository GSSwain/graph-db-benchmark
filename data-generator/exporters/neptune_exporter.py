"""
AWS Neptune Exporter: S3-Compatible Bulk Load CSV and Gremlin Ingestion
"""
import os
import csv
from typing import List, Dict, Any
from .base import BaseExporter

class NeptuneExporter(BaseExporter):
    def __init__(self, endpoint: str = None, output_dir: str = None):
        self.endpoint = endpoint or os.getenv("NEPTUNE_ENDPOINT", "ws://localhost:8182/gremlin")
        self.output_dir = output_dir or "data/neptune"
        os.makedirs(self.output_dir, exist_ok=True)
        self.client = None

    def export_vertices(self, vertex_type: str, vertices: List[Dict[str, Any]]):
        if not vertices:
            return
        path = os.path.join(self.output_dir, f"nodes_{vertex_type}.csv")
        file_exists = os.path.exists(path)
        
        # Neptune header format: ~id, ~label, property:Type...
        keys = list(vertices[0].keys())
        fieldnames = ["~id", "~label"] + [k for k in keys if k != "id"]
        
        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            for v in vertices:
                row = {"~id": f"{vertex_type}_{v['id']}", "~label": vertex_type}
                for k in keys:
                    if k != "id":
                        row[k] = v[k]
                writer.writerow(row)

    def export_edges(self, edge_type: str, edges: List[Dict[str, Any]]):
        if not edges:
            return
        path = os.path.join(self.output_dir, f"edges_{edge_type}.csv")
        file_exists = os.path.exists(path)

        src_key, dst_key = "fromId", "toId"
        src_label, dst_label = "Account", "Account"
        if edge_type == "own":
            src_key, dst_key = "ownerId", "accountId"
            src_label, dst_label = "Person", "Account"
        elif edge_type == "signIn":
            src_key, dst_key = "mediumId", "accountId"
            src_label, dst_label = "Medium", "Account"
        elif edge_type == "apply":
            src_key, dst_key = "applicantId", "loanId"
            src_label, dst_label = "Person", "Loan"
        elif edge_type == "deposit":
            src_key, dst_key = "loanId", "accountId"
            src_label, dst_label = "Loan", "Account"
        elif edge_type == "repay":
            src_key, dst_key = "accountId", "loanId"
            src_label, dst_label = "Account", "Loan"

        fieldnames = ["~id", "~from", "~to", "~label"] + [k for k in edges[0].keys() if k not in (src_key, dst_key)]
        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            for idx, e in enumerate(edges):
                row = {
                    "~id": f"e_{edge_type}_{e.get('order', idx)}_{e[src_key]}_{e[dst_key]}",
                    "~from": f"{src_label}_{e[src_key]}",
                    "~to": f"{dst_label}_{e[dst_key]}",
                    "~label": edge_type
                }
                for k, v in e.items():
                    if k not in (src_key, dst_key):
                        row[k] = v
                writer.writerow(row)

    def export_probes(self, probes: List[Dict[str, Any]]):
        import json
        with open(os.path.join(self.output_dir, "probes.json"), "w") as f:
            json.dump(probes, f, indent=2)
