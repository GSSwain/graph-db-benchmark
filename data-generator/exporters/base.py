"""
Base Exporter Interface for FinBench Data Generation
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseExporter(ABC):
    @abstractmethod
    def export_vertices(self, vertex_type: str, vertices: List[Dict[str, Any]]):
        pass

    @abstractmethod
    def export_edges(self, edge_type: str, edges: List[Dict[str, Any]]):
        pass

    @abstractmethod
    def export_probes(self, probes: List[Dict[str, Any]]):
        pass

    def close(self):
        pass
