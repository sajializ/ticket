import random
import config
from collections import deque
from typing import Dict, List
from network import Network

def select_landmarks_by_degree(net: Network, k: int) -> List[str]:
    """
    Choose the top-k nodes by degree (number of neighbors) in the network.
    
    Args:
        net: The Lightning Network graph (must have net.adj populated).
        k:   How many landmarks to pick.
    
    Returns:
        A list of k node-IDs with the highest degree.
    """
    # Build degree map: node -> total neighbors
    degree_map = {node: len(net.adj.get(node, [])) for node in net.adj}
    
    # Sort by degree descending
    sorted_nodes = sorted(degree_map.items(), key=lambda x: x[1], reverse=True)
    
    # Take the top k
    return [node for node, _ in sorted_nodes[:k]]


def set_routes(net: Network) -> None:
    """
    Build coordinate trees rooted at each landmark using the SpeedyMurmurs algorithm.
    Phase 1: use only bidirectional links to assign most nodes.
    Phase 2: attach remaining nodes via any non-zero link to ensure full coverage.
    """
    landmarks = select_landmarks_by_degree(net, config.NUM_TREES)
    # Reset any existing coordinates and counters
    net.coordinates.clear()
    net.stab_msg_count = 0

    for tree_id, landmark in enumerate(landmarks):
        # PHASE 1: Bidirectional-only BFS
        assigned = set()
        coord_map: Dict[str, List[int]] = {}
        queue = deque()

        # Initialize root coordinate
        coord_map[landmark] = []
        net.set_coordinate(landmark, tree_id, [])
        assigned.add(landmark)
        queue.append(landmark)
        counter = 0
        while queue:
            counter += 1
            current = queue.popleft()
            cur_coord = coord_map[current]
            for nbr, cid in net.get_neighbors(current):
                if nbr in coord_map:
                    continue
                chan = net.channels[cid]
                # Only bidirectional links
                if chan.bi:
                    suffix = random.getrandbits(
                        config.COORD_BITS if hasattr(config, 'COORD_BITS') else 64
                    )
                    # suffix = 1
                    new_coord = cur_coord + [suffix]
                    coord_map[nbr] = new_coord
                    net.set_coordinate(nbr, tree_id, new_coord)
                    assigned.add(nbr)
                    queue.append(nbr)

        # PHASE 2: Unidirectional links for remaining nodes
        queue = deque(assigned)
        while queue:
            counter += 1
            current = queue.popleft()
            cur_coord = coord_map[current]
            for nbr, cid in net.get_neighbors(current):
                if nbr in coord_map:
                    continue
                chan = net.channels[cid]
                # Allow any non-zero link
                if chan.total_capacity > 0:
                    suffix = random.getrandbits(
                        config.COORD_BITS if hasattr(config, 'COORD_BITS') else 64
                    )
                    new_coord = cur_coord + [suffix]
                    coord_map[nbr] = new_coord
                    net.set_coordinate(nbr, tree_id, new_coord)
                    assigned.add(nbr)
                    queue.append(nbr)




def random_partition(amount: int, parts: int) -> List[int]:
    """
    Split `amount` into `parts` positive integer shares summing to amount,
    with a uniform random distribution over all such compositions.
    """
    if parts <= 1:
        return [amount]
    # pick (parts-1) distinct cut points in [1..amount-1]
    cuts = sorted(random.sample(range(1, amount), parts - 1))
    # add the endpoints
    points = [0] + cuts + [amount]
    # differences are the shares
    return [points[i+1] - points[i] for i in range(parts)]