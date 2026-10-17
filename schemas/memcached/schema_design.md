# Memcached Graph Representation for LDBC FinBench

Memcached is an ultra-low-latency in-memory key-value cache. In large-scale financial platforms (e.g., Meta TAO, high-frequency banking), graph queries leverage an in-memory graph cache tier.

## 1. Key Modeling Architecture

### Vertices (Nodes)
- Key Pattern: `v:{EntityType}:{EntityId}`
- Value: JSON string of node properties
- Example: `v:Account:10001` -> `{"id":10001,"isBlocked":false,"createTime":1609459200000,"type":"debit","accountLevel":"gold"}`

### Directed Adjacency Lists (Edges)
Edges are maintained as indexed adjacency lists:
- Outgoing Adjacency: `adj:out:{EntityType}:{EntityId}:{EdgeType}`
- Value: Compact JSON array of outgoing edge records:
  `[{"dst": 10002, "amount": 5000, "createTime": 1609459210000, "order": 1}, ...]`
- Incoming Adjacency: `adj:in:{EntityType}:{EntityId}:{EdgeType}`
- Value: Compact JSON array of incoming edge records:
  `[{"src": 9999, "amount": 2500, "createTime": 1609459205000, "order": 0}, ...]`

### Edge Multiplicity & Temporal Ordering
FinBench allows multiple edges of the same type between the same pair of vertices (e.g., repeated transfers). The adjacency list maintains individual transactions sorted by `createTime` or `order`, facilitating temporal window filtering.

## 2. Multi-Hop Traversal Execution (1 to 100 Hops)

Traversals across k hops are executed using pipelined BFS/DFS with batch multi-gets (`get_multi`):
1. Hop 1: Issue `get("adj:out:Account:" + start_id + ":transfer")`. Extract target node IDs.
2. Hop 2: Construct batch keys `["adj:out:Account:" + id + ":transfer" for id in frontier]`. Issue a single `get_multi(batch_keys)`.
3. Hop k (up to 100): Repeat batch frontier expansion.
   - For beam search / directed path tracing, select top transactions (or highest amount / chronological transfers) to prevent exponential frontier explosion.
   - All lookups benefit from O(1) memory hashing, providing an extreme-throughput baseline comparison against native graph database pointer-chasing engines.
