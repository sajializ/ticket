# path to a real‐world Lightning snapshot (e.g. CSV or JSON)
# SNAPSHOT_PATH = "./other/listchannels20220412.json"
SNAPSHOT_PATH = "2024-05-20.json"

# ───────── BFS ──────────────────────────────────────────
# choose "hop" or "fee" for your two versions
BFS_MODE = "hop"       # or "fee"
# if fee mode, we ignore real fees and assign random weights in [1, MAX_WEIGHT]


# ───────── Bloom Filter ──────────────────────────────────
# false‑positive rate you’re willing to tolerate
BF_FALSE_POS_RATE = 0.0000001
# number of items you expect to insert per filter
BF_EXPECTED_ITEMS = 100000
# fallback strategy: "retry" or "alternative_path"

# ───────── Splitting ────────────────────────────────────
# how many sub‑payments to split into (1 = no split)
SPLIT_COUNT = 1
SPLIT_CHANNEL_PERCENT = 0.5
OFF_CHANNELS = 0

# ───────── Simulation ───────────────────────────────────
NUM_PAYMENTS = 50000

# Maximum payment amount in satoshis
MIN_PAYMENT = 100
MAX_PAYMENT = 1000

# Maximum number of candidate channels per node to include in the Bloom filter
MAX_CANDIDATES = 3000
NUM_ATTEMPTS = 1

NUM_TREES = 1  # or however many trees you want to use
SPLIT_COUNT = 1
SATURATION_PORTION = 0

# random or bet
SATURATION_MODE = 'random'
# Which routing algorithm: "bfs" or "speedy"
ROUTING_ALGO = "purebfs"

