import time
from typing import Dict, Any
from .base import BaseBenchmarkAdapter

class Neo4jBenchmarkAdapter(BaseBenchmarkAdapter):
    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        auth: tuple = ("neo4j", "benchmarkpassword"),
        language: str = "cypher"
    ):
        self.language = language.lower()
        if self.language in ("trail", "directed_trail", "reachability"):
            self.name = "Neo4j-DirectedTrail"
        else:
            self.name = "Neo4j-Cypher"
        super().__init__(self.name)
        self.uri = uri
        self.auth = auth
        self.driver = None

    def connect(self) -> bool:
        try:
            from neo4j import GraphDatabase
            self.driver = GraphDatabase.driver(self.uri, auth=self.auth)
            with self.driver.session() as s:
                s.run("RETURN 1").single()
            return True
        except Exception as e:
            print("[" + self.name + "] Connection failed: " + str(e))
            return False

    def warmup(self, start_id: int):
        if not self.driver:
            return
        try:
            with self.driver.session() as s:
                s.run("MATCH (a:Account {id: $id})-[:transfer]->(b:Account) RETURN b.id LIMIT 5", id=start_id).consume()
        except Exception:
            pass

    def run_multi_hop(self, start_id: int, target_id: int, depth: int, mode: str = "path_trace") -> Dict[str, Any]:
        if not self.driver:
            return {"success": False, "latency_ms": 0.0, "result_count": 0, "error": "Not connected"}

        t0 = time.perf_counter_ns()
        try:
            with self.driver.session() as s:
                if self.language in ("trail", "directed_trail") or mode == "reachability":
                    t_target = target_id if target_id else start_id + depth
                    query = (
                        "MATCH p = (a:Account {id: $start_id})-[:transfer*" + str(depth) + "]->(b:Account {id: $target_id}) "
                        "RETURN length(p) AS hops LIMIT 1"
                    )
                    res = s.run(query, start_id=start_id, target_id=t_target)
                else:
                    query = (
                        "MATCH (a:Account {id: $start_id})-[:transfer*" + str(depth) + "]->(b:Account) "
                        "RETURN b.id AS target_id LIMIT 10"
                    )
                    res = s.run(query, start_id=start_id)

                records = list(res)
                cnt = len(records)
                lat_ms = (time.perf_counter_ns() - t0) / 1000000.0
                return {"success": True, "latency_ms": lat_ms, "result_count": cnt, "error": None}
        except Exception as e:
            lat_ms = (time.perf_counter_ns() - t0) / 1000000.0
            return {"success": False, "latency_ms": lat_ms, "result_count": 0, "error": str(e)}

    def run_complex_read(self, query_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if not self.driver:
            return {"success": False, "latency_ms": 0.0, "result_count": 0, "error": "Not connected"}
        t0 = time.perf_counter_ns()
        try:
            with self.driver.session() as s:
                if query_id == "CR1":
                    query = "MATCH (m:Medium {id: $medium_id})-[:signIn]->(a:Account) MATCH (a)-[:transfer]->(b:Account)-[:transfer]->(c:Account) WHERE c.isBlocked = true RETURN c.id, count(*) AS cnt LIMIT 20"
                    res = list(s.run(query, medium_id=params.get("medium_id", 1)))
                elif query_id == "CR2":
                    query = "MATCH (p:Person {id: $person_id})-[:guarantee]->(friend:Person)-[:apply]->(l:Loan) RETURN friend.id, l.loanAmount LIMIT 20"
                    res = list(s.run(query, person_id=params.get("person_id", 1)))
                elif query_id == "CR3":
                    query = "MATCH (a:Account {id: $account_id})-[:transfer]->(b:Account)-[:transfer]->(c:Account)-[:transfer]->(a) RETURN b.id, c.id LIMIT 20"
                    res = list(s.run(query, account_id=params.get("account_id", 1)))
                else:
                    query = "MATCH (a:Account {id: $account_id})-[:transfer]->(b:Account) RETURN b.id LIMIT 10"
                    res = list(s.run(query, account_id=params.get("account_id", 1)))
                lat_ms = (time.perf_counter_ns() - t0) / 1000000.0
                return {"success": True, "latency_ms": lat_ms, "result_count": len(res), "error": None}
        except Exception as e:
            lat_ms = (time.perf_counter_ns() - t0) / 1000000.0
            return {"success": False, "latency_ms": lat_ms, "result_count": 0, "error": str(e)}

    def close(self):
        if self.driver:
            self.driver.close()
