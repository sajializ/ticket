from typing import List, Tuple
import config
import sys
import csv

def report(results: List[Tuple[bool, float, int]], routing_algorithm: str) -> None:
    """
    Print summary metrics for payment simulation results.

    Args:
        results: A list of tuples (success, latency_s, hops) for each payment.
                 - success (bool): True if payment succeeded
                 - latency_s (float): time elapsed in seconds
                 - hops (int): number of hops taken (fee metric)
    """
    total = len(results)
    if total == 0:
        print("No simulation results to report.")
        return

    successes = sum(1 for success, _, _, _ in results if success == True)
    failures = total - successes
    success_rate = (successes / total) * 100.0
    average_hops = sum(int(hops) for success, hops, _, _ in results if success == True) / successes
    average_delay = sum(int(delay) for success, _, delay, _ in results if success == True) / successes
    average_fee = sum(int(fee) for success, _, _, fee in results if success == True) / successes


    print("===== Simulation Metrics =====")
    print(f"Routing Algorithm: {routing_algorithm}")
    print(f"Total payments: {total}")
    print(f"Success rate: {successes}/{total} ({success_rate:.2f}%)")
    print(f"Failures: {failures}")
    print(f"Average hops: {average_hops}")
    print(f"Average delay: {average_delay}")
    print(f"Average fees: {average_fee}")
    print(f"BloomFilter False Positive Rate: {config.BF_FALSE_POS_RATE}")
    print(f"BloomFilter Expected Items: {config.BF_EXPECTED_ITEMS}")
    print(f"Min amount: {config.MIN_PAYMENT}, Max amount: {config.MAX_PAYMENT}")
    print(f"Max candidate per node: {config.MAX_CANDIDATES}")
    print(f"Portion of saturated channels: {config.SATURATION_PORTION}")
    print(f"Portion of offline channels: {config.OFF_CHANNELS}")
    
    with open(sys.argv[1] + "_" + routing_algorithm + ".csv", 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(results)
