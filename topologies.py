"""
topologies.py — candidate migration topologies as adjacency matrices.

Each function returns a numpy adjacency matrix (float64, symmetric, zero diagonal).

Classic topologies are parameterized by n (number of islands).
Symmetric graphs from the Foster census are fixed-size cubic graphs.
"""

import math
import numpy as np
import networkx as nx


# ---------------------------------------------------------------------------
# Classic topologies (parameterized by n)
# ---------------------------------------------------------------------------

def none(n):
    """No edges — n isolated nodes. lambda_2 = 0."""
    return np.zeros((n, n), dtype=float)


def ring(n):
    """Cycle graph C_n. Each node connected to its two neighbours."""
    G = nx.cycle_graph(n)
    return nx.to_numpy_array(G, dtype=float)


def star(n):
    """Star graph S_n — one hub (node 0) connected to all n-1 leaves."""
    G = nx.star_graph(n - 1)   # nx.star_graph(k) has k+1 nodes
    return nx.to_numpy_array(G, dtype=float)


def complete(n):
    """Complete graph K_n — every node connected to every other."""
    G = nx.complete_graph(n)
    return nx.to_numpy_array(G, dtype=float)


def grid(n):
    """
    Approximate square grid.  Tries to form an (r x c) grid with r*c == n.
    If n is not a perfect square, uses the largest r such that r^2 <= n and
    builds an (r x r) grid (dropping extra nodes).  Returns the adjacency
    matrix for that grid; actual node count may be < n.
    """
    r = int(math.isqrt(n))
    if r * r < n:
        # fall back: use largest square <= n
        pass  # r is already floor(sqrt(n))
    G = nx.grid_2d_graph(r, r)
    return nx.to_numpy_array(G, dtype=float)


def hypercube(k):
    """k-dimensional hypercube graph. n = 2^k nodes, each with degree k."""
    G = nx.hypercube_graph(k)
    return nx.to_numpy_array(G, dtype=float)


def random_regular(n, k, seed=42):
    """Random k-regular graph on n nodes (uses networkx)."""
    G = nx.random_regular_graph(k, n, seed=seed)
    return nx.to_numpy_array(G, dtype=float)


# ---------------------------------------------------------------------------
# Symmetric cubic graphs from the Foster census (fixed size)
# ---------------------------------------------------------------------------

def cube():
    """Q_3 — 3-dimensional hypercube graph. n=8, cubic (degree 3)."""
    G = nx.cubical_graph()
    return nx.to_numpy_array(G, dtype=float)


def petersen():
    """Petersen graph GP(5,2). n=10, cubic."""
    G = nx.petersen_graph()
    return nx.to_numpy_array(G, dtype=float)


def heawood():
    """Heawood graph. n=14, cubic."""
    G = nx.heawood_graph()
    return nx.to_numpy_array(G, dtype=float)


def mobius_kantor():
    """Moebius-Kantor graph GP(8,3). n=16, cubic."""
    G = nx.moebius_kantor_graph()
    return nx.to_numpy_array(G, dtype=float)


def pappus():
    """Pappus graph. n=18, cubic."""
    G = nx.pappus_graph()
    return nx.to_numpy_array(G, dtype=float)


def dodecahedron():
    """Dodecahedron graph. n=20, cubic (degree 3)."""
    G = nx.dodecahedral_graph()
    return nx.to_numpy_array(G, dtype=float)


def desargues():
    """Desargues graph GP(10,3). n=20, cubic."""
    G = nx.desargues_graph()
    return nx.to_numpy_array(G, dtype=float)


# ---------------------------------------------------------------------------
# Registry helper
# ---------------------------------------------------------------------------

def all_topologies():
    """
    Return a list of (name, adjacency_matrix, notes) tuples for all
    canonical topologies used in the lambda_2 survey.
    """
    entries = []

    # Classic
    for n in [8, 10, 16, 20]:
        entries.append((f"none(n={n})",      none(n),                 "isolated islands"))
    for n in [8, 10, 16, 20]:
        entries.append((f"ring(n={n})",      ring(n),                 "cycle C_n"))
    for n in [8, 10, 16, 20]:
        entries.append((f"star(n={n})",      star(n),                 "hub-and-spoke"))
    for n in [8, 10, 16, 20]:
        entries.append((f"complete(n={n})",  complete(n),             "fully connected K_n"))
    for n in [9, 16, 25]:
        A = grid(n)
        actual_n = A.shape[0]
        entries.append((f"grid(n≈{n})",      A,                       f"2-D grid, actual n={actual_n}"))
    for k in [3, 4, 5]:
        entries.append((f"hypercube(k={k})", hypercube(k),            f"Q_{k}, n=2^{k}={2**k}"))
    for n, k_deg in [(8, 3), (16, 3), (20, 3)]:
        entries.append((f"rand_reg(n={n},k={k_deg})", random_regular(n, k_deg), "random 3-regular"))

    # Foster census cubic graphs
    entries.append(("cube",          cube(),          "Q_3, n=8, cubic"))
    entries.append(("petersen",      petersen(),      "GP(5,2), n=10, cubic"))
    entries.append(("heawood",       heawood(),       "n=14, cubic"))
    entries.append(("mobius_kantor", mobius_kantor(), "GP(8,3), n=16, cubic"))
    entries.append(("pappus",        pappus(),        "n=18, cubic"))
    entries.append(("dodecahedron",  dodecahedron(),  "n=20, cubic"))
    entries.append(("desargues",     desargues(),     "GP(10,3), n=20, cubic"))

    return entries
