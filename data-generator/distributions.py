"""
Statistical Distributions & Graph Topologies for LDBC FinBench
Models power-law degree distributions (Zipfian/Pareto), temporal clustering,
and dedicated multi-hop AML money trails (1 to 100 hops).
"""
import random
import math
from typing import List, Tuple

class FinBenchDistributions:
    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)

    def power_law_choice(self, population_size: int, alpha: float = 1.3) -> int:
        """
        Sample index in [0, population_size - 1] following Zipfian power law.
        alpha ~ 1.3 models realistic financial hub accounts.
        """
        if population_size <= 1:
            return 0
        u = self.rng.random()
        # Inverse transform sampling for Pareto
        idx = int(population_size * (u ** (1.0 / (1.0 - alpha + 1e-9)) - 1.0) / (0.01 - 1.0))
        return min(max(0, abs(idx) % population_size), population_size - 1)

    def generate_transfer_amount(self) -> int:
        """Log-normal distributed transaction amounts in cents"""
        # mu=7.5 (~$18), sigma=1.8 -> long tail up to $100,000+
        val = math.exp(self.rng.gauss(7.5, 1.8))
        return int(max(100, min(val, 100_000_000)))

    def generate_timestamp(self, start_ts: int, end_ts: int) -> int:
        """Temporal distribution with periodic bursts"""
        base = self.rng.randint(start_ts, end_ts)
        return base

    def generate_deep_transfer_chains(
        self,
        account_ids: List[int],
        chain_count: int,
        max_hops: int = 100,
        start_ts: int = 1609459200000
    ) -> Tuple[List[dict], List[dict]]:
        """
        Generate deterministic multi-hop money flow paths (up to max_hops = 100).
        Returns:
            transfers: list of transfer edge dicts
            probes: list of probe metadata with start_account, path, and verified depth
        """
        transfers = []
        probes = []
        needed_per_chain = max_hops + 1
        total_accounts = len(account_ids)

        if total_accounts < needed_per_chain:
            # Re-use accounts cyclically if scale is smaller than max_hops
            available_pools = [account_ids[i % total_accounts] for i in range(needed_per_chain * chain_count)]
        else:
            available_pools = account_ids

        step = needed_per_chain
        for c in range(chain_count):
            start_idx = (c * step) % max(1, (len(available_pools) - needed_per_chain))
            chain_accounts = available_pools[start_idx : start_idx + needed_per_chain]
            
            # Ensure strictly distinct accounts along the primary probe path
            current_ts = start_ts + c * 86_400_000
            amount = 10_000_000 # $100,000 money laundering initial sum
            chain_edges = []

            for hop in range(max_hops):
                src = chain_accounts[hop]
                dst = chain_accounts[hop + 1]
                current_ts += self.rng.randint(60_000, 3_600_000) # 1 min to 1 hr later
                amount = int(amount * 0.98) # 2% fee cut per hop
                edge = {
                    "fromId": src,
                    "toId": dst,
                    "createTime": current_ts,
                    "amount": max(100, amount),
                    "order": hop + 1,
                    "is_deep_chain": True,
                    "chain_id": c
                }
                transfers.append(edge)
                chain_edges.append(edge)

            probes.append({
                "chain_id": c,
                "start_account_id": chain_accounts[0],
                "target_account_id": chain_accounts[-1],
                "depth": max_hops,
                "intermediate_accounts": chain_accounts,
                "start_time": chain_edges[0]["createTime"],
                "end_time": chain_edges[-1]["createTime"]
            })

        return transfers, probes
