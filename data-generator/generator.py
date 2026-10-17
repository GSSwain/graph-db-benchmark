import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
"""
LDBC FinBench Synthetic Graph Data Generator
Supports parametric scale factors (from dev preset up to 100M users, 10B accounts, 10T transactions),
distributed deterministic partitioning (Kubernetes / Spark / Ray sharding),
and dedicated 1-to-100-hop ground-truth AML transfer trails.
"""
import os
import sys
import time
import json
import argparse
from typing import List, Dict, Any

from models import Person, Account, Company, Loan, Medium, Transfer
from distributions import FinBenchDistributions
from exporters.neo4j_exporter import Neo4jExporter
from exporters.memcached_exporter import MemcachedExporter
from exporters.neptune_exporter import NeptuneExporter
from exporters.spanner_exporter import SpannerExporter

PRESETS = {
    "dev": {
        "users": 1_000,
        "accounts": 5_000,
        "transactions": 25_000,
        "companies": 50,
        "loans": 100,
        "mediums": 200,
        "description": "Dev/CI/Quick test (sub-second generation)"
    },
    "local": {
        "users": 10_000,
        "accounts": 50_000,
        "transactions": 250_000,
        "companies": 500,
        "loans": 1_000,
        "mediums": 2_000,
        "description": "Standard local container benchmark"
    },
    "medium": {
        "users": 100_000,
        "accounts": 1_000_000,
        "transactions": 10_000_000,
        "companies": 10_000,
        "loans": 50_000,
        "mediums": 100_000,
        "description": "Medium cluster benchmark"
    },
    "cloud": {
        "users": 1_000_000,
        "accounts": 100_000_000,
        "transactions": 1_000_000_000,
        "companies": 100_000,
        "loans": 500_000,
        "mediums": 1_000_000,
        "description": "Large-scale cloud benchmark"
    },
    "full": {
        "users": 100_000_000,         # 100 Million Users
        "accounts": 10_000_000_000,   # 10 Billion Accounts
        "transactions": 10_000_000_000_000, # 10 Trillion Transactions
        "companies": 10_000_000,
        "loans": 50_000_000,
        "mediums": 200_000_000,
        "description": "Full FinBench 10-Trillion scale (distributed shards)"
    }
}

class FinBenchGenerator:
    def __init__(
        self,
        preset: str = "dev",
        scale_factor: float = None,
        partitions: int = 1,
        partition_id: int = 0,
        seed: int = 42,
        deep_chain_hops: int = 100,
        deep_chain_count: int = 10
    ):
        self.preset_name = preset
        self.partitions = max(1, partitions)
        self.partition_id = partition_id
        self.seed = seed + partition_id * 10007
        self.dist = FinBenchDistributions(self.seed)
        self.deep_chain_hops = deep_chain_hops
        self.deep_chain_count = deep_chain_count

        if scale_factor is not None:
            # Custom scale factor relative to full 10T spec (SF=100)
            full_ref = PRESETS["full"]
            ratio = scale_factor / 100.0
            self.total_users = max(10, int(full_ref["users"] * ratio))
            self.total_accounts = max(50, int(full_ref["accounts"] * ratio))
            self.total_trans = max(100, int(full_ref["transactions"] * ratio))
            self.total_companies = max(5, int(full_ref["companies"] * ratio))
            self.total_loans = max(5, int(full_ref["loans"] * ratio))
            self.total_mediums = max(10, int(full_ref["mediums"] * ratio))
        else:
            cfg = PRESETS.get(preset, PRESETS["dev"])
            self.total_users = cfg["users"]
            self.total_accounts = cfg["accounts"]
            self.total_trans = cfg["transactions"]
            self.total_companies = cfg["companies"]
            self.total_loans = cfg["loans"]
            self.total_mediums = cfg["mediums"]

        # Compute partitioned slices
        self.user_start = (self.total_users // self.partitions) * self.partition_id
        self.user_count = self.total_users // self.partitions
        self.account_start = (self.total_accounts // self.partitions) * self.partition_id
        self.account_count = self.total_accounts // self.partitions
        self.trans_count = self.total_trans // self.partitions

    def run(self, exporters: List[Any]):
        print(f"============================================================")
        print(f" LDBC FinBench Data Generator - Partition {self.partition_id + 1}/{self.partitions}")
        print(f" Preset: {self.preset_name} (Users: {self.total_users:,}, Accounts: {self.total_accounts:,}, Transactions: {self.total_trans:,})")
        print(f" Partition Slice: {self.account_count:,} accounts, {self.trans_count:,} transactions")
        print(f" Ground Truth Deep Hops: {self.deep_chain_hops} hops across {self.deep_chain_count} chains")
        print(f"============================================================")

        t0 = time.time()

        # 1. Generate Vertices: Persons
        print(f"--> Generating Persons...")
        persons = []
        for i in range(self.user_count):
            uid = self.user_start + i + 1
            persons.append({
                "id": uid,
                "name": f"Person_{uid}",
                "isBlocked": (uid % 50 == 0),
                "createTime": 1577836800000 + (uid * 3600000) % 63072000000,
                "gender": "male" if uid % 2 == 0 else "female",
                "birthday": 631152000000 + (uid * 86400000) % 946080000000,
                "country": ["US", "UK", "DE", "SG", "JP"][uid % 5],
                "city": ["NewYork", "London", "Berlin", "Singapore", "Tokyo"][uid % 5]
            })
            if len(persons) >= 5000:
                for exp in exporters:
                    exp.export_vertices("Person", persons)
                persons = []
        for exp in exporters:
            exp.export_vertices("Person", persons)

        # 2. Generate Vertices: Accounts
        print(f"--> Generating Accounts...")
        accounts = []
        account_ids = []
        for i in range(self.account_count):
            aid = self.account_start + i + 1
            account_ids.append(aid)
            accounts.append({
                "id": aid,
                "createTime": 1580000000000 + (aid * 600000) % 63072000000,
                "isBlocked": (aid % 100 == 0),
                "type": ["checking", "savings", "credit", "business"][aid % 4],
                "nickname": f"acc_{aid}",
                "phonenum": f"+1555{aid:07d}",
                "freqLoginType": ["mobile", "web", "pos"][aid % 3],
                "lastLoginTime": 1640995200000,
                "accountLevel": ["bronze", "silver", "gold", "platinum"][aid % 4]
            })
            if len(accounts) >= 5000:
                for exp in exporters:
                    exp.export_vertices("Account", accounts)
                accounts = []
        for exp in exporters:
            exp.export_vertices("Account", accounts)

        # 3. Generate Vertices: Companies & Loans & Mediums
        print(f"--> Generating Companies, Loans, Mediums...")
        companies = [{
            "id": i + 1,
            "name": f"Company_{i+1}",
            "isBlocked": (i % 80 == 0),
            "createTime": 1577836800000,
            "country": "US",
            "city": "NewYork",
            "business": "Fintech",
            "description": f"Corp {i+1}"
        } for i in range(min(500, self.total_companies))]
        for exp in exporters:
            exp.export_vertices("Company", companies)

        loans = [{
            "id": i + 1,
            "loanAmount": 1000000,
            "balance": 800000,
            "createTime": 1585000000000,
            "usage": "mortgage",
            "interestRate": 0.045
        } for i in range(min(1000, self.total_loans))]
        for exp in exporters:
            exp.export_vertices("Loan", loans)

        mediums = [{
            "id": i + 1,
            "medType": ["smartphone", "browser", "tablet"][i % 3],
            "isBlocked": (i % 120 == 0),
            "createTime": 1582000000000,
            "lastLogin": 1640000000000
        } for i in range(min(2000, self.total_mediums))]
        for exp in exporters:
            exp.export_vertices("Medium", mediums)

        # 4. Generate Dedicated Deep Multi-Hop Transfer Trails (1 to 100 hops)
        print(f"--> Generating Ground-Truth {self.deep_chain_hops}-Hop AML Transfer Chains...")
        deep_transfers, probes = self.dist.generate_deep_transfer_chains(
            account_ids=account_ids,
            chain_count=self.deep_chain_count,
            max_hops=self.deep_chain_hops
        )
        for exp in exporters:
            exp.export_edges("transfer", deep_transfers)
            exp.export_probes(probes)

        # 5. Generate Power-Law Background Financial Transactions
        print(f"--> Generating Background Transactions ({self.trans_count:,} transfers)...")
        bg_transfers = []
        acc_len = len(account_ids)
        for i in range(self.trans_count):
            src_idx = self.dist.power_law_choice(acc_len)
            dst_idx = self.dist.power_law_choice(acc_len)
            while dst_idx == src_idx:
                dst_idx = (dst_idx + 1) % acc_len
            
            src_id = account_ids[src_idx]
            dst_id = account_ids[dst_idx]
            bg_transfers.append({
                "fromId": src_id,
                "toId": dst_id,
                "createTime": 1609459200000 + (i * 30000) % 31536000000,
                "amount": self.dist.generate_transfer_amount(),
                "order": i + 1
            })
            if len(bg_transfers) >= 5000:
                for exp in exporters:
                    exp.export_edges("transfer", bg_transfers)
                bg_transfers = []
        for exp in exporters:
            exp.export_edges("transfer", bg_transfers)

        # 6. Generate Structural Edges: Own, SignIn, Guarantee
        print(f"--> Generating Ownership, SignIns, and Guarantees...")
        own_edges = []
        for i, aid in enumerate(account_ids):
            pid = self.user_start + (i % max(1, self.user_count)) + 1
            own_edges.append({
                "ownerId": pid,
                "ownerType": "Person",
                "accountId": aid,
                "createTime": 1580000000000
            })
        for exp in exporters:
            exp.export_edges("own", own_edges)

        signin_edges = []
        for i in range(min(5000, len(account_ids))):
            signin_edges.append({
                "mediumId": (i % 1000) + 1,
                "accountId": account_ids[i],
                "createTime": 1600000000000 + i * 10000
            })
        for exp in exporters:
            exp.export_edges("signIn", signin_edges)

        guarantee_edges = []
        for i in range(min(1000, self.user_count - 1)):
            guarantee_edges.append({
                "fromId": self.user_start + i + 1,
                "toId": self.user_start + i + 2,
                "entityType": "Person",
                "createTime": 1590000000000,
                "relation": "family" if i % 2 == 0 else "friend"
            })
        for exp in exporters:
            exp.export_edges("guarantee", guarantee_edges)

        duration = time.time() - t0
        print(f"==> Partition {self.partition_id + 1} completed in {duration:.2f}s!")

def main():
    parser = argparse.ArgumentParser(description="LDBC FinBench Parametric Data Generator")
    parser.add_argument("--preset", type=str, default="dev", choices=list(PRESETS.keys()), help="Scale preset: dev, local, medium, cloud, full")
    parser.add_argument("--scale-factor", type=float, default=None, help="Custom Scale Factor (relative to 100=full 10T scale)")
    parser.add_argument("--partitions", type=int, default=1, help="Total number of parallel partitions/shards")
    parser.add_argument("--partition-id", type=int, default=0, help="Current partition ID [0..partitions-1]")
    parser.add_argument("--target", type=str, default="neo4j,memcached", help="Target databases: neo4j,memcached,neptune,spanner,all")
    parser.add_argument("--export-dir", type=str, default="data", help="Output directory for CSV/JSON files")
    parser.add_argument("--deep-hops", type=int, default=100, help="Max hops for ground-truth transfer chains (default: 100)")
    parser.add_argument("--chains", type=int, default=10, help="Number of dedicated ground-truth multi-hop chains")
    parser.add_argument("--seed", type=int, default=42, help="Random PRNG seed")
    args = parser.parse_args()

    targets = [t.strip().lower() for t in args.target.split(",")]
    exporters = []

    if "neo4j" in targets or "all" in targets:
        exporters.append(Neo4jExporter(csv_dir=os.path.join(args.export_dir, "neo4j")))
    if "memcached" in targets or "all" in targets:
        exporters.append(MemcachedExporter(dump_dir=os.path.join(args.export_dir, "memcached")))
    if "neptune" in targets or "all" in targets:
        exporters.append(NeptuneExporter(output_dir=os.path.join(args.export_dir, "neptune")))
    if "spanner" in targets or "all" in targets:
        exporters.append(SpannerExporter(output_dir=os.path.join(args.export_dir, "spanner")))

    gen = FinBenchGenerator(
        preset=args.preset,
        scale_factor=args.scale_factor,
        partitions=args.partitions,
        partition_id=args.partition_id,
        seed=args.seed,
        deep_chain_hops=args.deep_hops,
        deep_chain_count=args.chains
    )
    gen.run(exporters)

    for exp in exporters:
        exp.close()

if __name__ == "__main__":
    main()
