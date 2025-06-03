import json
import random
from collections import defaultdict
import config
from typing import List, Tuple, Dict
import heapq
import math
from collections import deque, defaultdict
from typing import Dict, List, Tuple
import os
import pickle
import networkx as nx

class Channel:
    """
    Represents a Lightning Network channel with directed capacity split.
    """

    def __init__(self, entry: dict):
        self.u = entry['source']
        self.v = entry['destination']
        self.id = entry['short_channel_id']
        self.public = entry.get('public', False)
        self.active = entry.get('active', False)

        flags = entry.get('channel_flags', 0)
        self.disabled = bool(flags & 2)
        self.message_flags = entry.get('message_flags', 0)

        total_capacity = int(entry.get('satoshis', 0))
        self.total_capacity = total_capacity
        half = int(total_capacity * config.SPLIT_CHANNEL_PERCENT)
        self.capacity_uv = half
        self.capacity_vu = total_capacity - half

        self.base_fee_msat_u = int(entry.get('base_fee_millisatoshi', 0))
        self.base_fee_msat_v = 0
        self.fee_proportional_millionths_u = int(entry.get('fee_per_millionth', 0))
        self.fee_proportional_millionths_v = 0

        min_msat_str = entry.get('htlc_minimum_msat', '0msat')
        self.htlc_min_msat_u = int(min_msat_str.replace('msat', ''))
        self.htlc_min_msat_v = 0

        max_msat_str = entry.get('htlc_maximum_msat', '0msat')
        self.htlc_max_msat_u = int(max_msat_str.replace('msat', ''))
        self.htlc_max_msat_v = 0

        self.delay_u = int(entry.get('delay', 0))
        self.delay_v = 0
        self.bi = False
        self.online = True


    def update(self, entry: dict):
        self.base_fee_msat_v = int(entry.get('base_fee_millisatoshi', 0))
        self.fee_proportional_millionths_v = int(entry.get('fee_per_millionth', 0))

        min_msat_str = entry.get('htlc_minimum_msat', '0msat')
        self.htlc_min_msat_v = int(min_msat_str.replace('msat', ''))

        max_msat_str = entry.get('htlc_maximum_msat', '0msat')
        self.htlc_max_msat_v = int(max_msat_str.replace('msat', ''))

        self.delay_v = int(entry.get('delay', 0))
        self.bi = True


    def get_capacity(self, from_node: str) -> int:
        if from_node == self.u:
            return self.capacity_uv
        if from_node == self.v:
            return self.capacity_vu
        return 0
    
    def get_htlc_min_msat(self, from_node: str) -> int:
        if from_node == self.u:
            return self.htlc_min_msat_u
        if from_node == self.v:
            return self.htlc_min_msat_v
        return 0
    
    def get_base_fee_msat(self, from_node: str, amount: int) -> int:
        if from_node == self.u:
            return self.base_fee_msat_u + (amount * self.fee_proportional_millionths_u / 1000)
        elif from_node == self.v:
            return self.base_fee_msat_v + (amount * self.fee_proportional_millionths_v / 1000)
        return 0
    
    def get_htlc_max_msat(self, from_node: str) -> int:
        if from_node == self.u:
            return self.htlc_max_msat_u
        if from_node == self.v:
            return self.htlc_max_msat_v
        return 0
    
    def get_delay(self, from_node: str) -> int:
        if from_node == self.u:
            return self.delay_u
        if from_node == self.v:
            return self.delay_v
        return 0

    
    def reduce_capacity(self, from_node: str, amount: int) -> None:
        if from_node == self.u:
            # forward along u→v
            self.capacity_uv = max(0, self.capacity_uv - amount)
        elif from_node == self.v:
            # forward along v→u
            self.capacity_vu = max(0, self.capacity_vu - amount)

    def increase_capacity(self, from_node: str, amount: int) -> None:
        if from_node == self.u:
            # forward along u→v
            self.capacity_uv = max(0, self.capacity_uv + amount)
        elif from_node == self.v:
            # forward along v→u
            self.capacity_vu = max(0, self.capacity_vu + amount)



class Network:
    """
    Directed Lightning Network graph from JSON snapshot.

    - Only includes channels that are public, active, and not disabled.
    - Builds a directed adjacency list: node -> list of (neighbor_id, channel_id).
    """
    def __init__(self, snapshot_path: str):
        self.nodes = set()
        self.graph = nx.MultiDiGraph()
        self.channels = {}           # chan_id -> Channel
        self.adj = defaultdict(list) # node_id -> List[(neighbor_id, chan_id)]
        self._load_snapshot(snapshot_path)
        self.coordinates: Dict[Tuple[str,int], List[int]] = {}
        self.stab_msg_count = 0   # counter for on-demand stabilization messages
        self.nodes = sorted(self.nodes)
        self.rev_adj: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
        for u in self.nodes:
            for v, cid in self.get_neighbors(u):
                self.rev_adj[v].append((u, cid))


    def update_networkx_graph(self):
        for chan in self.channels.values():
            if not chan.online:
                continue
            self.graph.add_edge(chan.u, chan.v, key=chan.id, weight=chan.capacity_uv)
            if chan.bi:
                self.graph.add_edge(chan.v, chan.u, key=chan.id, weight=chan.capacity_vu)


    def _load_snapshot(self, path: str):
        with open(path, 'r') as f:
            data = json.load(f)['channels']

        entries = data.values() if isinstance(data, dict) else data if isinstance(data, list) else []

        for entry in entries:
            if not isinstance(entry, dict):
                continue

            chan = Channel(entry)
            # Filter non-public, inactive, or disabled channels
            if not chan.public or not chan.active:
                continue
            
            if chan.id in self.channels.keys():
                existing_chan = self.channels[chan.id]
                existing_chan.update(entry)
                self.adj[chan.u].append((chan.v, chan.id))
                self.graph.add_edge(chan.u, chan.v, key=chan.id, weight=chan.capacity_vu)
            else:
                self.channels[chan.id] = chan
                self.nodes.add(chan.u)
                self.nodes.add(chan.v)
                # Add directed edges
                self.adj[chan.u].append((chan.v, chan.id))
                self.graph.add_edge(chan.u, chan.v, key=chan.id, weight=chan.capacity_uv)


    def get_neighbors(self, node_id: str) -> List[Tuple[str, str]]:
        """
        Return list of outgoing neighbors (neighbor_id, channel_id).
        """
        return self.adj.get(node_id, [])


    def print(self) -> None:
        """
        Print the directed graph: for each node, list outgoing edges with channel id and directed capacity.
        """
        for node in sorted(self.nodes):
            print(f"Node {node}:")
            for neighbor, chan_id in self.adj.get(node, []):
                cap = self.channels[chan_id].get_capacity(node)
                online = self.channels[chan_id].online
                print(f"  -> {neighbor} via {chan_id} (cap={cap} sats) online {online}")


    def set_coordinate(self, node_id: str, tree_id: int, coordinate: List[int]) -> None:
        if node_id not in self.coordinates:
            self.coordinates[node_id] = {}
        self.stab_msg_count += 1
        self.coordinates[node_id][tree_id] = coordinate


    def get_coordinate(self, node_id: str, tree_id: int) -> List[int]:
        return self.coordinates.get(node_id, {}).get(tree_id, [])


    def find_channel_id(self, u: str, v: str) -> str:
        for neighbor, cid in self.get_neighbors(u):
            if neighbor == v:
                return cid
        return None


    def set_cred(self, u: str, v: str, new_capacity: int) -> None:
        """
        Update directed capacity u->v on a channel and perform local on-demand
        stabilization of only the affected subtree(s) per embedding (tree).
        """
        cid = self.find_channel_id(u, v)
        if cid is None:
            return
        chan = self.channels[cid]
        old_uv, old_vu = chan.cap_uv, chan.cap_vu
        # update directed capacity
        if (u, v) == (chan.u, chan.v):
            chan.cap_uv = new_capacity
        elif (u, v) == (chan.v, chan.u):
            chan.cap_vu = new_capacity
        else:
            return
        # reset soft mirrors
        chan.available_uv = chan.cap_uv
        chan.available_vu = chan.cap_vu
        # detect zero<->nonzero flip
        flipped = ((old_uv == 0) != (chan.cap_uv == 0)) or ((old_vu == 0) != (chan.cap_vu == 0))
        if not flipped:
            return
        # perform on-demand stabilization for each tree
        for tree_id in range(config.NUM_TREES):
            # check if u or v belong in this tree
            # if either has a coord, reset that subtree
            if self.get_coordinate(u, tree_id):
                self._reset_subtree(tree_id, u)
            if self.get_coordinate(v, tree_id):
                self._reset_subtree(tree_id, v)


    def _reset_subtree(self, tree_id: int, root: str) -> None:
        """
        Reset coordinates of `root` and its descendants in tree `tree_id`.
        Then reattach them by choosing new parents via two-phase BFS logic.
        """
        # collect old prefix
        old_prefix = self.get_coordinate(root, tree_id)
        if not old_prefix:
            return
        # find nodes to reset (prefix match)
        to_reset = []
        for node, coords in list(self.coordinates.items()):
            coord = coords.get(tree_id)
            if coord and coord[:len(old_prefix)] == old_prefix:
                to_reset.append(node)
        # delete old coords
        for node in to_reset:
            del self.coordinates[node][tree_id]
        # reinsert nodes by increasing depth
        to_reset.sort(key=lambda n: len(self.get_coordinate(n, tree_id)))
        for node in to_reset:
            # find candidate parents
            best_parent = None
            best_len = float('inf')
            # phase 1: bidirectional links
            for nbr, cid in self.get_neighbors(node):
                if (nbr in self.coordinates) and (tree_id in self.coordinates[nbr]):
                    # check bidirectional
                    chan = self.channels[cid]
                    if chan.cap_uv > 0 and chan.cap_vu > 0:
                        parent_coord = self.coordinates[nbr][tree_id]
                        if len(parent_coord) < best_len:
                            best_len = len(parent_coord)
                            best_parent = nbr
            # phase 2: unidirectional if none
            if not best_parent:
                for nbr, cid in self.get_neighbors(node):
                    if (nbr in self.coordinates) and (tree_id in self.coordinates[nbr]):
                        parent_coord = self.coordinates[nbr][tree_id]
                        if len(parent_coord) < best_len:
                            best_len = len(parent_coord)
                            best_parent = nbr
            if best_parent:
                # assign new coordinate
                parent_coord = self.coordinates[best_parent][tree_id]
                # random b-bit suffix
                suffix = random.getrandbits(config.COORD_BITS if hasattr(config, 'COORD_BITS') else 64)
                new_coord = parent_coord + [suffix]
                self.set_coordinate(node, tree_id, new_coord)

