from bfs import compute_rank, candidate_channels
from bloom_filter import BloomFilter
from network import Network
import config
import random
from typing import Tuple
from tools import commit_capacity



def route_subpayment(
    net: Network,
    src: str,
    dst: str,
    amount: int,
    channels,
    fath,
) -> Tuple[bool, float, int, int]:
    """
    Route a single sub-payment from src to dst, retrying alternative channels at each hop
    if a forward attempt fails, until either success or all candidates exhaust.

    Returns:
      - success: True if reached dst, False otherwise
      - latency: elapsed time in seconds
      - hops: number of hops taken
      - cltv_delay: total CLTV delay
    """
    # Initialize Bloom filter for quick membership testing

    # counter1 = set()
    # for c, val in channels.items():
    #     for neigh, v in val:
    #         counter1.add(c+neigh)
    
    bf = BloomFilter(config.BF_EXPECTED_ITEMS, config.BF_FALSE_POS_RATE)
    for c, val in channels.items():
        for nei, v in val:
            bf.add(c + nei)
    # # print(counter)
    counter2 = set()
    for c, cands in channels.items():
        neighbors = list(net.get_neighbors(c))
        # print(len(neighbors))
        for n in neighbors:
            if c + n[0] in bf and n not in cands:
                counter2.add(c + n[0])

    # bf_exclude = BloomFilter(len(counter2), config.BF_FALSE_POS_RATE)
    # for c in counter2:
    #     bf_exclude.add(c)
    
    cur = src
    hops = 0
    cltv_delay = 0
    base_fees = 0
    father = fath
    path = [src]

    while cur != dst:
        success_hop = False
        neighbors = list(net.get_neighbors(cur))
        
        while neighbors:
            adj, cid = random.choice(neighbors)

            neighbors.remove((adj, cid))
            if father == adj:
                continue

            if cur + adj not in bf:
                continue
            
            # if cur + adj in bf_exclude:
            #     continue

            channel = net.channels[cid]
            
            # Capacity check
            if not channel.online:
                continue
            if channel.get_capacity(cur) < amount:
                continue

            if amount * 1000 < channel.get_htlc_min_msat(cur) or amount * 1000 > channel.get_htlc_max_msat(cur):
                continue

            hops += 1
            cltv_delay += channel.get_delay(cur)
            base_fees += channel.get_base_fee_msat(cur, amount)
            # print("OUR FEE: ", base_fees)

            # Move to next node
            father = cur           
            cur = channel.v if channel.u == cur else channel.u
            success_hop = True
            path.append(cur)
            break

        if not success_hop:
            # no viable channel left at this hop
            return False, hops, cltv_delay, base_fees, []

    # Reached destination
    
    return True, hops, cltv_delay, base_fees, path

def our_route(net: Network, src: str, dst: str, amt: int):
    rank = compute_rank(net, dst, amt)
    F = candidate_channels(net, rank, amt, src, dst)
    routes = list(F[src])           
    success = False
    hops = 0
    cltv = 0
    base_fees = 0
    while routes:
    #for r in routes:
        r = random.choice(routes)
        chan = net.channels[r[1]]
        routes.remove(r)
        if chan.get_capacity(src) < amt:
            continue
        if amt * 1000 < chan.get_htlc_min_msat(src) or amt * 1000 > chan.get_htlc_max_msat(src):
            continue
        if not chan.online:
            continue
        # print("OUR FEE", chan.get_base_fee_msat(src, amt))
        s, hops, cltv, base_fees, path = route_subpayment(net, r[0], dst, amt, F, src)
        if s:
            success = True
            commit_capacity(net, [src] + path, amt)
            return s, hops + 1, cltv + chan.get_delay(src), base_fees + chan.get_base_fee_msat(src, amt)
        break

    if not success:
        return False, hops, cltv, base_fees
