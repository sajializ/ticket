import random
from typing import List, Tuple, Dict
import networkx as nx
import config
from network import Network
import metrics
import config
from network import Network
from speedy_setup import set_routes
import metrics
from our_route import our_route
from bfs_route import bfs_route
from speedy_routing import route_payment as speedy_route_payment
from tools import make_channels_offline, saturate_channels, is_there_really_a_path, not_connected_nodes


def add_to_dict(c, d: Dict):
    if c in d.keys():
        d[c] += 1
    else:
        d[c] = 1


def run():
    net_bfs = Network(config.SNAPSHOT_PATH)
    net_speedy = Network(config.SNAPSHOT_PATH)
    net_sourceRouting = Network(config.SNAPSHOT_PATH)

    make_channels_offline(net_bfs, config.OFF_CHANNELS)
    make_channels_offline(net_speedy, config.OFF_CHANNELS)
    make_channels_offline(net_sourceRouting, config.OFF_CHANNELS)

    saturate_channels(net_bfs, config.SATURATION_PORTION, config.SATURATION_MODE)
    saturate_channels(net_speedy, config.SATURATION_PORTION, config.SATURATION_MODE)
    saturate_channels(net_sourceRouting, config.SATURATION_PORTION, config.SATURATION_MODE)

    set_routes(net_speedy)
    blacklist = not_connected_nodes(net_speedy)
    del net_bfs.graph
    del net_speedy.graph
    del net_sourceRouting.graph
    nodes = list(net_bfs.nodes)

    bfs_results = []
    speedy_results = []
    sr_results = []
    bf1_size = dict()
    bf2_size = dict()

    random.seed(88)
    for counter in range(config.NUM_PAYMENTS):
        print(counter)
        src, dst = random.sample(nodes, 2)
        amt = random.randint(config.MIN_PAYMENT, config.MAX_PAYMENT)

        while True:
            bfs, _ = is_there_really_a_path(net_bfs, src, dst, amt)
            speedy, _ = is_there_really_a_path(net_speedy, src, dst, amt)
            sr, _ = is_there_really_a_path(net_sourceRouting, src, dst, amt)

            if bfs and speedy and sr and src not in blacklist and dst not in blacklist and src != dst:
                break

            src, dst = random.sample(nodes, 2)
            amt = random.randint(config.MIN_PAYMENT, config.MAX_PAYMENT)

        bfs_results.append((our_route(net_bfs, src, dst, amt)))
        speedy_results.append((speedy_route_payment(net_speedy, src, dst, amt)))
        sr_results.append((bfs_route(net_sourceRouting, src, dst, amt)))


        # if not bfs_results[counter][0] or not speedy_results[counter][0] or not sr_results[counter][0]:
        #     print( speedy_results[counter][0] )
        #     print(src, dst, amt)
        #     return

    metrics.report(bfs_results, "bfs")
    metrics.report(speedy_results, "speedy")
    metrics.report(sr_results, "source_routing")

    

if __name__ == "__main__":
    run()
