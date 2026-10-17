"""
GCP Spanner Graph Exporter: CSV staging and DML mutations
"""
import os
import csv
from typing import List, Dict, Any
from .base import BaseExporter

class SpannerExporter(BaseExporter):
    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or "data/spanner"
        os.makedirs(self.output_dir, exist_ok=True)

    def export_vertices(self, vertex_type: str, vertices: List[Dict[str, Any]]):
        if not vertices:
            return
        path = os.path.join(self.output_dir, f"{vertex_type}.csv")
        file_exists = os.path.exists(path)
        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(vertices[0].keys()))
            if not file_exists:
                writer.writeheader()
            writer.writerows(vertices)

    def export_edges(self, edge_type: str, edges: List[Dict[str, Any]]):
        if not edges:
            return
        path = os.path.join(self.output_dir, f"{edge_type}.csv")
        file_exists = os.path.exists(path)
        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(edges[0].keys()))
            if not file_exists:
                writer.writeheader()
            writer.writerows(edges)

    def export_probes(self, probes: List[Dict[str, Any]]):
        import json
        with open(os.path.join(self.output_dir, "probes.json"), "w") as f:
            json.dump(probes, f, indent=2)
