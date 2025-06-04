from typing import List, Tuple
import config
from network import Network
from speedy_setup import random_partition
import random


def route_payment(net: Network, src: str, dst: str, amount: int) -> Tuple[bool, int, int, List[List[str]]]:
    """
    Perform a multi-path payment by splitting `amount` into shares,
    routing each share along each of the NUM_TREES embeddings,
    reserving capacity, and committing or releasing on success/failure.
    Returns (overall_success, num_successful, total_parts, paths).
    """
    num_trees = config.NUM_TREES
    # shares = random_partition(amount, num_trees)
    shares = [amount]
    paths: List[List[str]] = []
    success_count = 0
    hops = 0
    cltv_delay = 0
    base_fees = 0
    for tree_id in range(num_trees):
        #tree_id = random.randint(0, num_trees-1)
        path, success, hops, cltv_delay, base_fees = _route_share(net, src, dst, amount, tree_id)
        if success:
            _commit_capacity(net, path, amount)
            return True, hops, cltv_delay, base_fees

    return False, hops, cltv_delay, base_fees


def _route_share(net: Network, src: str, dst: str, amount: int, tree_id: int) -> Tuple[List[str], bool]:
    """
    Route a single share `amount` from `src` to `dst` on embedding `tree_id`.
    Returns (path, success), where path is the sequence of node IDs.
    """
    path = [src]
    visited = {src}
    current = src
    hops = 0
    cltv_delay = 0
    base_fees = 0
    amt_msat = amount * 1000

    while current != dst:
        # fetch destination coordinate
        coord_dst = net.get_coordinate(dst, tree_id)
        coord_cur = net.get_coordinate(current, tree_id)
        best = None
        best_dist = float("inf")

        # inspect each neighbor
        for nbr, cid in net.get_neighbors(current):
            chan = net.channels[cid]
            # ensure sufficient guaranteed available capacity
            if not chan.online:
                continue
            if chan.get_capacity(current) < amount:
                continue
            if amt_msat < chan.get_htlc_min_msat(current) or amt_msat > chan.get_htlc_max_msat(current):
                continue
  
            # compute embedding distance
            coord_nbr = net.get_coordinate(nbr, tree_id)
            
            dist_nbr = _coordinate_distance(coord_nbr, coord_dst)
            dist_cur = _coordinate_distance(coord_cur, coord_dst)

            # pick strictly closer neighbor
            if dist_nbr < dist_cur and dist_nbr < best_dist:
                best = (nbr, cid)
                best_dist = dist_nbr
   
        if not best:
            # no viable next hop
            return path, False, hops, cltv_delay, base_fees

        nbr, cid = best
        path.append(nbr)
        visited.add(nbr)

        hops += 1
        cltv_delay += net.channels[cid].get_delay(current)
        base_fees += net.channels[cid].get_base_fee_msat(current, amount)
        current = nbr

    return path, True, hops, cltv_delay, base_fees


def _release_capacity(net: Network, path: List[str], amount: int) -> None:
    """
    Release any reserved capacity along path back to available.
    """
    for i in range(len(path) - 1):
        u, v = path[i], path[i+1]
        cid = net.find_channel_id(u, v)
        if cid in net.channels:
            net.channels[cid].release_available(u, amount)


def _commit_capacity(net: Network, path: List[str], amount: int) -> None:
    """
    Commit reserved capacity along path, turning reservation into real reduction.
    """
    for i in range(len(path) - 1):
        u, v = path[i], path[i+1]
        cid = net.find_channel_id(u, v)
        if cid in net.channels:
            net.channels[cid].increase_capacity(v, amount)
            net.channels[cid].reduce_capacity(u, amount)


def _coordinate_distance(coord1: List[int], coord2: List[int]) -> int:
    """
    Compute tree-based prefix embedding distance between two coordinates.
    """
    i = 0
    while i < len(coord1) and i < len(coord2) and coord1[i] == coord2[i]:
        i += 1
    return (len(coord1) - i) + (len(coord2) - i)
