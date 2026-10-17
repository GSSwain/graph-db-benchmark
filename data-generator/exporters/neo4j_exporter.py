"""
Neo4j Exporter: Direct Bolt Ingestion and CSV Bulk Export
"""
import os
import csv
from typing import List, Dict, Any
from .base import BaseExporter

class Neo4jExporter(BaseExporter):
    def __init__(self, uri: str = None, auth: tuple = None, csv_dir: str = None, direct_ingest: bool = True):
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = (auth[0] if auth else None) or os.getenv("NEO4J_USER", "neo4j")
        password = (auth[1] if auth else None) or os.getenv("NEO4J_PASSWORD", "benchmarkpassword")
        self.auth = (user, password)
        self.csv_dir = csv_dir
        self.direct_ingest = direct_ingest
        self.driver = None

        if self.direct_ingest:
            try:
                from neo4j import GraphDatabase
                self.driver = GraphDatabase.driver(self.uri, auth=self.auth)
                with self.driver.session() as s:
                    s.run("RETURN 1").single()
                print(f"[Neo4jExporter] Connected directly to Neo4j at {self.uri}")
            except Exception as e:
                print(f"[Neo4jExporter] Direct Bolt connection warning: {e}. Writing CSV files.")

        if self.csv_dir:
            os.makedirs(self.csv_dir, exist_ok=True)

    def export_vertices(self, vertex_type: str, vertices: List[Dict[str, Any]]):
        if not vertices:
            return
        if self.csv_dir:
            self._write_csv(f"{vertex_type}.csv", vertices)
        if self.driver:
            self._direct_insert_vertices(vertex_type, vertices)

    def export_edges(self, edge_type: str, edges: List[Dict[str, Any]]):
        if not edges:
            return
        if self.csv_dir:
            self._write_csv(f"{edge_type}.csv", edges)
        if self.driver:
            self._direct_insert_edges(edge_type, edges)

    def export_probes(self, probes: List[Dict[str, Any]]):
        import json
        target_dir = self.csv_dir or "."
        with open(os.path.join(target_dir, "probes.json"), "w") as f:
            json.dump(probes, f, indent=2)

    def _write_csv(self, filename: str, records: List[Dict[str, Any]]):
        path = os.path.join(self.csv_dir, filename)
        file_exists = os.path.exists(path)
        keys = list(records[0].keys())
        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            if not file_exists:
                writer.writeheader()
            writer.writerows(records)

    def _direct_insert_vertices(self, vertex_type: str, vertices: List[Dict[str, Any]], batch_size: int = 5000):
        query = f"""
        UNWIND $batch AS row
        MERGE (n:{vertex_type} {{id: row.id}})
        SET n += row
        """
        with self.driver.session() as session:
            for i in range(0, len(vertices), batch_size):
                batch = vertices[i:i + batch_size]
                session.run(query, batch=batch)

    def _direct_insert_edges(self, edge_type: str, edges: List[Dict[str, Any]], batch_size: int = 5000):
        src_label, dst_label = "Account", "Account"
        src_key, dst_key = "fromId", "toId"
        if edge_type == "own":
            src_label, dst_label = "Person", "Account"
            src_key, dst_key = "ownerId", "accountId"
        elif edge_type == "signIn":
            src_label, dst_label = "Medium", "Account"
            src_key, dst_key = "mediumId", "accountId"
        elif edge_type == "apply":
            src_label, dst_label = "Person", "Loan"
            src_key, dst_key = "applicantId", "loanId"
        elif edge_type == "repay":
            src_label, dst_label = "Account", "Loan"
            src_key, dst_key = "accountId", "loanId"
        elif edge_type == "deposit":
            src_label, dst_label = "Loan", "Account"
            src_key, dst_key = "loanId", "accountId"
        elif edge_type == "guarantee":
            src_label, dst_label = "Person", "Person"
            src_key, dst_key = "fromId", "toId"

        query = f"""
        UNWIND $batch AS row
        MATCH (src:{src_label} {{id: row.{src_key}}})
        MATCH (dst:{dst_label} {{id: row.{dst_key}}})
        CREATE (src)-[r:{edge_type}]->(dst)
        SET r += row
        """
        with self.driver.session() as session:
            for i in range(0, len(edges), batch_size):
                batch = edges[i:i + batch_size]
                session.run(query, batch=batch)

    def close(self):
        if self.driver:
            self.driver.close()
