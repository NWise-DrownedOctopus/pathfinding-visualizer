"""
graph_generator.py

Generates a random undirected weighted graph as a list of Node objects,
using fake lat/lon coordinates centred on the same region as the preset
city graph.  The output is a drop-in replacement for import_graph() —
hand the returned list straight to Graph.nodes and call
Graph.build_screen_positions().

Public API
----------
    generate_graph(params: dict) -> list[Node]

params keys (all produced by GeneratorDialog):
    n_nodes       int    number of nodes to create
    branching     float  expected number of neighbours per node
    weight_min    int    minimum edge weight (≥ 0)
    weight_max    int    maximum edge weight (≥ weight_min)
    connectedness float  fraction of maximum possible edges (0, 1]
    seed          int    RNG seed for reproducibility
"""

import random
import math
from graph import Node   # reuse the existing Node class

# ── Geographic centre — matches the preset Kansas city graph ──────────────────
_CENTER_LAT =  37.75
_CENTER_LON = -97.62

# Maximum radius in degrees from the centre.
# The graph window is 950px wide; build_screen_positions uses dist_multi=200.
# 200 * 2.0° ≈ 400px — fits comfortably inside the window on both axes.
_MAX_RADIUS_LAT = 1.6   # degrees latitude  (north/south)
_MAX_RADIUS_LON = 2.0   # degrees longitude (east/west)

# Minimum separation between nodes (degrees) to avoid extreme overlap.
_MIN_SEP = 0.08


def _random_position(rng: random.Random) -> tuple[float, float]:
    """
    Sample a (lat, lon) inside an ellipse centred on _CENTER_LAT/_CENTER_LON.

    Using polar coordinates with independent lat/lon radii gives an elliptical
    safe zone that matches the rectangular graph window aspect ratio, so nodes
    never appear off-screen regardless of N.
    """
    # Random angle and radius (sqrt gives uniform area distribution in the ellipse)
    angle  = rng.uniform(0, 2 * math.pi)
    radius = math.sqrt(rng.uniform(0, 1))   # sqrt → uniform density in disk

    lat = _CENTER_LAT + radius * _MAX_RADIUS_LAT * math.sin(angle)
    lon = _CENTER_LON + radius * _MAX_RADIUS_LON * math.cos(angle)
    return round(lat, 6), round(lon, 6)


def _dist(a: Node, b: Node) -> float:
    """Euclidean distance in lat/lon space."""
    return math.hypot(a.lat - b.lat, a.lon - b.lon)


def _place_nodes(n: int, rng: random.Random) -> list[Node]:
    """
    Create N nodes with well-separated positions.
    Tries up to 30 candidates per node and picks the one furthest from all
    existing nodes (Poisson-disk-lite).  Falls back to any valid position if
    all candidates are too close.
    """
    nodes: list[Node] = []
    for i in range(n):
        best_pos  = None
        best_dist = -1.0
        candidates = 30

        for _ in range(candidates):
            lat, lon = _random_position(rng)
            # Find minimum distance to any already-placed node
            if nodes:
                min_d = min(_dist_raw(lat, lon, nd.lat, nd.lon) for nd in nodes)
            else:
                min_d = float('inf')

            if min_d > best_dist:
                best_dist = min_d
                best_pos  = (lat, lon)

            # Accept immediately if well-separated
            if min_d >= _MIN_SEP:
                best_pos = (lat, lon)
                break

        lat, lon = best_pos
        nodes.append(Node(f"N{i:02d}", lat, lon))

    return nodes


def _dist_raw(lat1, lon1, lat2, lon2) -> float:
    return math.hypot(lat1 - lat2, lon1 - lon2)


def _sorted_neighbours(i: int, nodes: list[Node]) -> list[int]:
    """Return indices of all other nodes sorted by distance to nodes[i]."""
    return sorted(
        (j for j in range(len(nodes)) if j != i),
        key=lambda j: _dist(nodes[i], nodes[j])
    )


def generate_graph(params: dict) -> list[Node]:
    """
    Build and return a list of fully-linked Node objects.

    Algorithm
    ---------
    1. Place N nodes using a best-of-30 sampling strategy so they stay
       spread out and inside the visible window (polar clamping).
    2. Guarantee connectivity with a proximity-biased spanning tree:
       each new node connects to its nearest already-connected neighbour
       rather than a random one — this alone cuts most long crossings.
    3. Add extra edges by iterating each node's nearest neighbours first,
       so additional connections also prefer short edges.
    4. All edges are bidirectional with a random weight in [weight_min, weight_max].
    5. Nodes are named "N00", "N01", …
    """
    n         = params["n_nodes"]
    branching = params["branching"]
    w_min     = params["weight_min"]
    w_max     = params["weight_max"]
    connect   = params["connectedness"]
    seed      = params["seed"]

    rng = random.Random(seed)

    # ── Step 1: place nodes with spread-out positions ─────────────────────
    nodes = _place_nodes(n, rng)

    # ── Step 2: proximity-biased spanning tree ────────────────────────────
    # adj[i] = {j: weight} for all neighbours of node i
    adj: dict[int, dict[int, int]] = {i: {} for i in range(n)}

    def _add_edge(i: int, j: int):
        w = rng.randint(w_min, w_max) if w_min < w_max else w_min
        adj[i][j] = w
        adj[j][i] = w

    # Start with node 0 connected; add each remaining node to its
    # nearest already-connected neighbour.
    connected   = {0}
    unconnected = list(range(1, n))
    # Sort unconnected by distance to node 0 so we grow outward naturally
    unconnected.sort(key=lambda j: _dist(nodes[0], nodes[j]))

    for idx in unconnected:
        # Find closest node already in the connected set
        nearest = min(connected, key=lambda c: _dist(nodes[idx], nodes[c]))
        _add_edge(idx, nearest)
        connected.add(idx)

    # ── Step 3: add extra edges (nearest-first) ───────────────────────────
    max_edges    = n * (n - 1) // 2
    target_edges = max(n - 1, int(connect * max_edges))
    max_degree   = max(2, int(branching * 2))

    current_edges = sum(len(v) for v in adj.values()) // 2

    # Precompute sorted neighbour lists for every node
    sorted_nbrs = {i: _sorted_neighbours(i, nodes) for i in range(n)}

    # Iterate nodes in random order; for each, try connecting to nearest
    # unconnected neighbours until degree cap or target reached.
    node_order = list(range(n))
    rng.shuffle(node_order)

    for i in node_order:
        if current_edges >= target_edges:
            break
        for j in sorted_nbrs[i]:
            if current_edges >= target_edges:
                break
            if j in adj[i]:
                continue
            if len(adj[i]) >= max_degree or len(adj[j]) >= max_degree:
                continue
            _add_edge(i, j)
            current_edges += 1

    # ── Step 4: convert to Node.adjacencies tuples ────────────────────────
    for i, node in enumerate(nodes):
        node.adjacencies = tuple(nodes[j] for j in adj[i])

    avg_deg = sum(len(adj[i]) for i in range(n)) / n
    print(
        f"[generate_graph] seed={seed}  nodes={n}  "
        f"edges={current_edges}  avg_degree={avg_deg:.2f}"
    )
    return nodes