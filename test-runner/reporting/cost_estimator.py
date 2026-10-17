"""
LDBC FinBench - Database Infrastructure Cost Estimation Engine
Calculates dedicated database infrastructure costs (excluding test-runner client compute)
across Neo4j, Memcached, AWS Neptune, GCP Spanner, and Azure Cosmos DB.
"""

from typing import Dict, Any, List

# Infrastructure Pricing Constants (US-East / US-Central Reference Rates)
PRICING_CATALOG = {
    "neo4j": {
        "engine_name": "Self-Hosted Neo4j Enterprise HA Cluster",
        "hourly_base_per_gb_ram": 0.09,          # ~$65.70 / GB RAM / month
        "storage_per_gb_month": 0.15,            # NVMe SSD volume
        "ha_nodes": 3,
        "vcpus_per_node": 4,
        "license_cost_per_core_month": 0.0,      # Quote-based; set with --neo4j-license-usd-per-core-month
        "write_overhead_factor": 1.25,
        "pricing_unit": "3-node RAM + NVMe SSD + Enterprise license"
    },
    "memcached": {
        "engine_name": "AWS ElastiCache for Memcached",
        "hourly_base_per_gb_ram": 0.015,         # ~$10.95 / GB RAM / month (cache.r6g family)
        "storage_per_gb_month": 0.00,            # Pure In-Memory RAM
        "write_overhead_factor": 1.10,
        "pricing_unit": "In-Memory Instance (cache.r6g)"
    },
    "neptune": {
        "engine_name": "AWS Neptune Database",
        "hourly_base_per_gb_ram": 0.06,          # ~$43.80 / GB RAM / month (db.r6g family)
        "storage_per_gb_month": 0.10,            # Neptune Cluster Storage
        "io_cost_per_million": 0.20,             # $0.20 per 1M I/O requests
        "write_overhead_factor": 1.30,
        "pricing_unit": "Instance-hr + Cluster Storage + I/O"
    },
    "spanner": {
        "engine_name": "Google Cloud Spanner (Graph & SQL)",
        "hourly_per_node": 0.90,                 # $0.90 / node-hr (1,000 PUs)
        "storage_per_gb_month": 0.30,            # Spanner SSD storage ($0.30/GB/mo)
        "write_overhead_factor": 1.40,
        "pricing_unit": "Spanner Nodes (PUs) + SSD Storage"
    },
    "cosmos": {
        "engine_name": "Azure Cosmos DB (Gremlin & SQL API)",
        "ru_per_100_hourly": 0.008,              # $0.008 per 100 RU/s per hour ($0.08 / 1k RU/s-hr)
        "storage_per_gb_month": 0.25,            # Transactional storage
        "write_ru_per_op": 12.0,                 # Average RU per vertex/edge write
        "read_ru_per_hop": 2.5,                  # Average RU per single-hop read
        "pricing_unit": "Provisioned RU/s + Storage"
    }
}

SCALE_PRESETS = {
    "dev": {
        "name": "Development / CI",
        "persons": 1_000,
        "accounts": 5_000,
        "transfers": 25_000,
        "raw_data_gb": 0.01
    },
    "local": {
        "name": "Local Docker Benchmark",
        "persons": 10_000,
        "accounts": 50_000,
        "transfers": 250_000,
        "raw_data_gb": 0.10
    },
    "medium": {
        "name": "Medium Production Cluster",
        "persons": 100_000,
        "accounts": 1_000_000,
        "transfers": 10_000_000,
        "raw_data_gb": 5.0
    },
    "cloud": {
        "name": "Cloud Distributed Scale",
        "persons": 1_000_000,
        "accounts": 100_000_000,
        "transfers": 1_000_000_000,
        "raw_data_gb": 500.0
    },
    "full": {
        "name": "Full 10-Trillion Scale",
        "persons": 100_000_000,
        "accounts": 10_000_000_000,
        "transfers": 10_000_000_000_000,
        "raw_data_gb": 500_000.0  # ~500 TB raw graph data
    }
}

class CostEstimator:
    def __init__(self, neo4j_license_usd_per_core_month: float = 0.0):
        self.catalog = PRICING_CATALOG
        self.presets = SCALE_PRESETS
        self.neo4j_license_usd_per_core_month = neo4j_license_usd_per_core_month

    def estimate_data_footprint(self, preset_key: str = "dev") -> Dict[str, float]:
        preset = self.presets.get(preset_key, self.presets["dev"])
        raw_gb = preset["raw_data_gb"]
        
        # Sizing with engine-specific indexing and internal structure overhead
        return {
            "raw_gb": raw_gb,
            "neo4j_storage_gb": max(1.0, round(raw_gb * 1.5, 2)),
            "neo4j_ram_gb": max(2.0, round(raw_gb * 0.75, 2)),
            "memcached_ram_gb": max(1.0, round(raw_gb * 1.2, 2)),
            "neptune_storage_gb": max(1.0, round(raw_gb * 1.6, 2)),
            "neptune_ram_gb": max(4.0, round(raw_gb * 0.6, 2)),
            "spanner_storage_gb": max(1.0, round(raw_gb * 1.4, 2)),
            "cosmos_storage_gb": max(1.0, round(raw_gb * 1.5, 2))
        }

    def estimate_monthly_infra_cost(self, preset_key: str = "dev", target_qps: float = 500.0) -> Dict[str, Any]:
        """Calculates 24/7 monthly database infrastructure cost for a given scale preset and target QPS."""
        footprint = self.estimate_data_footprint(preset_key)
        hours_per_month = 730.0
        
        estimates = {}

        # 1. Self-hosted Neo4j Enterprise (three-node HA cluster)
        neo_ram = footprint["neo4j_ram_gb"]
        neo_storage = footprint["neo4j_storage_gb"]
        neo_nodes = self.catalog["neo4j"]["ha_nodes"]
        neo_cores = neo_nodes * self.catalog["neo4j"]["vcpus_per_node"]
        neo_compute_hourly = neo_ram * self.catalog["neo4j"]["hourly_base_per_gb_ram"] * neo_nodes
        neo_infra_monthly = (neo_compute_hourly * hours_per_month) + (
            neo_storage * self.catalog["neo4j"]["storage_per_gb_month"] * neo_nodes
        )
        neo_license_monthly = neo_cores * self.neo4j_license_usd_per_core_month
        neo_monthly = neo_infra_monthly + neo_license_monthly
        estimates["Neo4j"] = {
            "monthly_cost_usd": round(neo_monthly, 2),
            "hourly_cost_usd": round(neo_monthly / hours_per_month, 4),
            "infrastructure_monthly_usd": round(neo_infra_monthly, 2),
            "license_monthly_usd": round(neo_license_monthly, 2),
            "license_usd_per_core_month": self.neo4j_license_usd_per_core_month,
            "licensed_cores": neo_cores,
            "cluster_nodes": neo_nodes,
            "spec": (
                f"{neo_nodes} nodes x {neo_ram:,.1f} GB RAM, {neo_storage:,.1f} GB NVMe each; "
                f"{neo_cores} licensed cores"
            ),
            "pricing_model": "Self-hosted Neo4j Enterprise 3-node HA; license rate is quote-based"
        }

        # 2. Memcached (AWS ElastiCache Memory Nodes)
        mem_ram = footprint["memcached_ram_gb"]
        mem_hourly = mem_ram * self.catalog["memcached"]["hourly_base_per_gb_ram"]
        mem_monthly = mem_hourly * hours_per_month
        estimates["Memcached"] = {
            "monthly_cost_usd": round(mem_monthly, 2),
            "hourly_cost_usd": round(mem_hourly, 4),
            "spec": f"{mem_ram:,.1f} GB RAM (ElastiCache cache.r6g)",
            "pricing_model": "AWS ElastiCache for Memcached"
        }

        # 3. AWS Neptune (Instance + Storage + Read/Write I/O)
        nep_ram = footprint["neptune_ram_gb"]
        nep_storage = footprint["neptune_storage_gb"]
        nep_compute_hourly = nep_ram * self.catalog["neptune"]["hourly_base_per_gb_ram"]
        monthly_queries = target_qps * 3600 * hours_per_month
        monthly_io_cost = (monthly_queries * 2.0 / 1_000_000) * self.catalog["neptune"]["io_cost_per_million"]
        nep_monthly = (nep_compute_hourly * hours_per_month) + (nep_storage * self.catalog["neptune"]["storage_per_gb_month"]) + monthly_io_cost
        estimates["Neptune"] = {
            "monthly_cost_usd": round(nep_monthly, 2),
            "hourly_cost_usd": round(nep_monthly / hours_per_month, 4),
            "spec": f"{nep_ram:,.1f} GB RAM, {nep_storage:,.1f} GB Cluster Storage",
            "pricing_model": "AWS Neptune Multi-AZ"
        }

        # 4. GCP Spanner (Nodes/PUs + SSD Storage)
        span_storage = footprint["spanner_storage_gb"]
        needed_nodes = max(1, int(max(target_qps / 8000.0, span_storage / 2000.0) + 0.99))
        span_hourly = needed_nodes * self.catalog["spanner"]["hourly_per_node"]
        span_monthly = (span_hourly * hours_per_month) + (span_storage * self.catalog["spanner"]["storage_per_gb_month"])
        estimates["Spanner"] = {
            "monthly_cost_usd": round(span_monthly, 2),
            "hourly_cost_usd": round(span_hourly + (span_storage * self.catalog["spanner"]["storage_per_gb_month"] / hours_per_month), 4),
            "spec": f"{needed_nodes:,} Spanner Node(s) ({needed_nodes * 1000:,} PUs), {span_storage:,.1f} GB SSD",
            "pricing_model": "GCP Cloud Spanner"
        }

        # 5. Azure Cosmos DB (RU/s + Storage)
        cos_storage = footprint["cosmos_storage_gb"]
        needed_ru = max(400, int(target_qps * 15))
        ru_hourly = (needed_ru / 100.0) * self.catalog["cosmos"]["ru_per_100_hourly"]
        cos_monthly = (ru_hourly * hours_per_month) + (cos_storage * self.catalog["cosmos"]["storage_per_gb_month"])
        estimates["CosmosDB"] = {
            "monthly_cost_usd": round(cos_monthly, 2),
            "hourly_cost_usd": round(ru_hourly + (cos_storage * self.catalog["cosmos"]["storage_per_gb_month"] / hours_per_month), 4),
            "spec": f"{needed_ru:,} Provisioned RU/s, {cos_storage:,.1f} GB Storage",
            "pricing_model": "Azure Cosmos DB Gremlin API"
        }

        return estimates

    def calculate_workload_run_cost(
        self,
        engine: str,
        duration_seconds: float,
        total_queries: int,
        preset_key: str = "dev"
    ) -> Dict[str, Any]:
        """Calculates exact DB infrastructure cost for running a specific benchmark workload session."""
        eng_key = engine.lower().split("-")[0]
        monthly = self.estimate_monthly_infra_cost(preset_key)
        
        matching_eng = "Neo4j"
        for k in monthly:
            if k.lower() in eng_key:
                matching_eng = k
                break

        hourly_rate = monthly[matching_eng]["hourly_cost_usd"]
        duration_hours = max(duration_seconds, 0.01) / 3600.0
        infra_run_cost = hourly_rate * duration_hours

        cost_per_million = (infra_run_cost / max(1, total_queries)) * 1_000_000 if total_queries > 0 else 0.0

        return {
            "engine": engine,
            "duration_sec": round(duration_seconds, 2),
            "total_queries": total_queries,
            "hourly_rate_usd": round(hourly_rate, 4),
            "workload_run_cost_usd": round(infra_run_cost, 6),
            "cost_per_million_queries_usd": round(cost_per_million, 4)
        }

    def compute_cost_per_hop_matrix(
        self,
        results: Dict[str, Dict[int, Dict[str, Any]]],
        preset_key: str = "dev"
    ) -> Dict[str, Dict[int, float]]:
        """Maps measured QPS and latency into cost ($) per 1 Million queries across hop depths."""
        monthly = self.estimate_monthly_infra_cost(preset_key)
        matrix = {}

        for engine, hop_data in results.items():
            matrix[engine] = {}
            hourly_rate = 0.50
            for k, val in monthly.items():
                if k.lower() in engine.lower():
                    hourly_rate = val["hourly_cost_usd"]
                    break

            for hop, m in hop_data.items():
                qps = max(m.get("qps", 1.0), 0.1)
                cost_per_1m = (hourly_rate / (3600.0 * qps)) * 1_000_000.0
                matrix[engine][hop] = round(cost_per_1m, 3)

        return matrix
