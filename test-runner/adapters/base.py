"""
Abstract Benchmark Adapter Interface
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseBenchmarkAdapter(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def connect(self) -> bool:
        pass

    @abstractmethod
    def warmup(self, start_id: int):
        pass

    @abstractmethod
    def run_multi_hop(self, start_id: int, target_id: int, depth: int, mode: str = "path_trace") -> Dict[str, Any]:
        """
        Executes multi-hop traversal at depth k (1 to 100).
        Returns dict with:
          - success: bool
          - latency_ms: float
          - result_count: int
          - error: Optional[str]
        """
        pass

    @abstractmethod
    def run_complex_read(self, query_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def close(self):
        pass
