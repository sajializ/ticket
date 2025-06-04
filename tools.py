from network import Network, Channel
from typing import List, Tuple
import csv
import random
from collections import deque
import networkx as nx


def commit_capacity(net: Network, path: List[str], amount: int) -> None:
    """
    Commit reserved capacity along path, turning reservation into real reduction.
    """
    for i in range(len(path) - 1):
        u, v = path[i], path[i+1]
        cid = net.find_channel_id(u, v)
        if cid in net.channels:
            net.channels[cid].increase_capacity(v, amount)
            net.channels[cid].reduce_capacity(u, amount)


def load_data(path):
    rows = []
    with open(path, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        for r in reader:
            rows.append(r)
    return rows


def saturate_channels(net: Network, saturation_rate: float, mode: str):
    if saturation_rate == 0:
        return
    if mode == 'bet':
        betweenness = []
        seen = set()
        with open("./other/bet.csv", 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                betweenness.append(row)

        to_saturate = int(len(betweenness) * saturation_rate)
        c = 0
        for k in betweenness:
            if k[0] in seen:
                continue
            channel = net.channels[k[2]]
            channel.capacity_uv = channel.total_capacity
            channel.capacity_vu = 0
            c += 1
            seen.add(k[0])
            if c > to_saturate:
                break

    elif mode == 'random':
        random.seed(49)
        saturated_count = int(saturation_rate * len(net.channels))
        counter = 0
        channels = list(net.channels.values())
        while counter < saturated_count:
            channel = random.choice(channels)
            channel.capacity_uv = channel.total_capacity
            channel.capacity_vu = 0
            channels.remove(channel)
            counter += 1
    elif mode == 'per_node':
        nodes = list(net.nodes)
        for node in nodes:
            neighbors = list(net.get_neighbors(node))
            to_saturate = int(len(neighbors) * saturation_rate)
            counter = 0
            while counter < to_saturate:
                neighbor = random.choice(neighbors)
                channel = net.channels[neighbor[1]]
                channel.capacity_uv = channel.total_capacity
                channel.capacity_vu = 0
                neighbors.remove(neighbor)
                counter += 1



def is_there_really_a_path(
    net,
    src: str,
    dst: str,
    amount_sat: int
):
    # BFS queue and visitation
    queue = deque([src])
    visited = {src}
 
    prev = {}

    while queue:
        u = queue.popleft()
        if u == dst:
            # reconstruct path
            path = []
            cur = dst
            while cur != src:
                pu, cid = prev[cur]
                path.append((pu, cur, cid))
                cur = pu
            path.reverse()

            return True, path

        for v, cid in net.get_neighbors(u):
            if v in visited:
                continue

            chan = net.channels[cid]
            if not chan.online:
                continue
            # 1) capacity check
            if chan.get_capacity(u) < amount_sat:
                continue
            # 2) HTLC‐min/max (convert sats → msat)
            msat = amount_sat * 1_000
            if msat < chan.get_htlc_min_msat(u) or msat > chan.get_htlc_max_msat(u):
                continue

            visited.add(v)
            prev[v] = (u, cid)
            queue.append(v)

    # no path found
    return False, []



def make_channels_offline(net: Network, off_channels: int):
    random.seed(42)
    if off_channels == 0:
        return
    offline_count = int(off_channels * len(net.channels))
    counter = 0
    channels = list(net.channels.values())
    while counter < offline_count:
        channel = random.choice(channels)
        channel.online = False
        channels.remove(channel)
        counter += 1


def not_connected_nodes(net: Network):
    G = net.graph
    cc = list(nx.strongly_connected_components(G))
    cc = sorted(cc, key=len, reverse=True)
    cc_large = cc[0]

    blacklist = []
    for n in net.nodes:
        if n not in cc_large:
            blacklist.append(n)

    return blacklist

    