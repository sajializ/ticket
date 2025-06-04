from collections import deque
from typing import List
from tools import commit_capacity
from network import Network


def bfs_route(
    net: Network,
    src: str,
    dst: str,
    amount_sat: int
):
    """
    Return the shortest path as a list of (u, v, channel_id) triples,
    or None if no capacity‐compatible path exists.
    """
    # BFS queue and visitation

    second, cid = None, None
    for v, c in net.get_neighbors(src):
        channel = net.channels[c]
        if channel.get_capacity(src) > amount_sat:
            second = v
            cid = c
            break

    queue = deque([second])
    visited = set()
    visited.add(src)
    # to reconstruct: prev[node] = (prev_node, channel_id)

    hops = 0
    cltv_delay = 0
    base_fees = 0
    prev = {}
    prev[second] = (src, cid)

    while queue:
        u = queue.popleft()
        visited.add(u)
        if u == dst:
            # reconstruct path
            path = []
            cur = dst
            while cur != src:
                pu, cid = prev[cur]
                path.append((pu, cur, cid))
                cur = pu
            path.reverse()

            cpath = [src]
            
            for u, v, cid in path:
                channel = net.channels[cid]
                hops += 1
                cltv_delay += channel.get_delay(u)
                base_fees += channel.get_base_fee_msat(u, amount_sat)
                cpath.append(v)
                if channel.get_capacity(u) < amount_sat or not channel.online:
                    return False, hops, cltv_delay, base_fees

            commit_capacity(net, cpath, amount_sat)
            
            return True, hops, cltv_delay, base_fees

        for v, cid in net.get_neighbors(u):
            if v in visited:
                continue
            chan = net.channels[cid]

            if chan.total_capacity < amount_sat:
                continue

            msat = amount_sat * 1_000
            if msat < chan.get_htlc_min_msat(u) or msat > chan.get_htlc_max_msat(u):
                continue

            prev[v] = (u, cid)
            queue.append(v)
            visited.add(v)

    # no path found
    return False, hops, cltv_delay, base_fees
