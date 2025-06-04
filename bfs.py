import heapq
import math
from collections import deque, defaultdict
from typing import Dict, List, Tuple

import config
from network import Network


def compute_rank(
    net: Network,
    dst: str,
    amount_sat: int
) -> Dict[str, float]:
    """
    Compute the "rank" (distance or cost) from each node to the destination.
    Uses reverse-BFS for hop-based routing or reverse-Dijkstra for fee-based routing,
    respecting directed channel capacity and HTLC bounds.
    """
    # Initialize ranks
    rank: Dict[str, float] = {node: math.inf for node in sorted(net.nodes)}
    rank[dst] = 0

    dq = deque([dst])
    amt_msat = amount_sat * 1000
    while dq:
        cur = dq.popleft()
        dcur = rank[cur] + 1
        for prev, cid in net.rev_adj.get(cur, []):
           
            chan = net.channels[cid]
            if chan.total_capacity < amount_sat:
                continue
            if amt_msat < chan.get_htlc_min_msat(prev) or amt_msat > chan.get_htlc_max_msat(prev):
                continue

            # we can change the cost
            if dcur < rank[prev]:
                rank[prev] = dcur
                dq.append(prev)

    return rank

def forward_reachable(net, rank, src, amount_sat):
    seen = {src}
    amt_msat = amount_sat * 1000
    q = deque([src])
    while q:
        u = q.popleft()
        if u in seen:
            continue
        for v, cid in net.get_neighbors(u):
            chan = net.channels[cid]
            if chan.total_capacity < amount_sat:
                continue
            if amt_msat < chan.get_htlc_min_msat(u) or amt_msat > chan.get_htlc_max_msat(u):
                continue

            if u not in seen:
                seen.add(v)
                q.append(v)
    return seen

def candidate_channels(
    net: Network,
    rank: Dict[str, float],
    amount_sat: int,
    src: str,
    dst: str,
) -> Dict[str, List[str]]:
    """
    For each node, select up to K outgoing channels that reach dst without loops.
    1) Gather strict-closer hops (rank[v] < rank[u]).
    3) Sort selection by rank(v) ascending and truncate to K.
    """
    F: Dict[str, List[str]] = {}
    amt_msat = amount_sat * 1000
    K = config.MAX_CANDIDATES

    q = list()
    q.append(src)
    seen = set()
    while q:
        strict: List[Tuple[str, str]] = []
        u = q.pop(0)
        if u in seen:
            continue
        seen.add(u)
        if u == dst:
            F[u] = []
            break
        for v, cid in net.get_neighbors(u):
            chan = net.channels[cid]
            if chan.total_capacity < amount_sat:
                continue
            if amt_msat < chan.get_htlc_min_msat(u) or amt_msat > chan.get_htlc_max_msat(u):
                continue
            r_u = rank.get(u, math.inf)
            r_v = rank.get(v, math.inf)
            if r_v < r_u:
                strict.append((v, cid))
                q.append(v)

        chosen = heapq.nsmallest(K, strict, key=lambda x: rank[x[0]])

        F[u] = chosen

    return F
