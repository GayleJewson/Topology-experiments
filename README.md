# Topology-experiments

Spectral analysis of migration topologies for island-model genetic algorithms,
combined with empirical diversity measurements from GA simulations.

## Purpose

In an island-model GA, subpopulations (islands) evolve independently and
periodically exchange individuals via migration.  The topology of the migration
graph controls how fast diversity spreads across islands.

**Algebraic connectivity** (lambda_2, the second-smallest eigenvalue of the
Laplacian L = D - A) is a clean spectral proxy for mixing speed:

- `lambda_2 = 0` → disconnected graph, no mixing
- Small `lambda_2` → slow mixing, diversity preserved longer
- Large `lambda_2` → fast mixing, islands converge quickly

This repo compares classic parameterized topologies with symmetric cubic graphs
from the Foster census to understand the relationship between graph structure
and GA performance.

## Collaboration

- **Claudius** selects topologies and calculates lambda_2 (spectral side).
- **Lyra** runs the GA simulations and measures empirical diversity (empirical side).
- PRs: Claudius reviews Lyra's simulation code; Lyra reviews Claudius's spectral analysis.

## Lambda_2 Results

Table sorted by lambda_2 ascending (computed by `compute_lambda2.py`):

| Topology | n | k (avg degree) | lambda_2 | Notes |
|----------|---|---------------|---------|-------|
| none(n=8) | 8 | 0.00 | 0.000000 | isolated islands |
| none(n=10) | 10 | 0.00 | 0.000000 | isolated islands |
| none(n=16) | 16 | 0.00 | 0.000000 | isolated islands |
| none(n=20) | 20 | 0.00 | 0.000000 | isolated islands |
| ring(n=20) | 20 | 2.00 | 0.097887 | cycle C_n |
| ring(n=16) | 16 | 2.00 | 0.152241 | cycle C_n |
| rand_reg(n=20,k=3) | 20 | 3.00 | 0.285795 | random 3-regular |
| ring(n=10) | 10 | 2.00 | 0.381966 | cycle C_n |
| grid(n≈25) | 25 | 3.20 | 0.381966 | 2-D grid, actual n=25 |
| rand_reg(n=16,k=3) | 16 | 3.00 | 0.456545 | random 3-regular |
| grid(n≈16) | 16 | 3.00 | 0.585786 | 2-D grid, actual n=16 |
| ring(n=8) | 8 | 2.00 | 0.585786 | cycle C_n |
| dodecahedron | 20 | 3.00 | 0.763932 | n=20, cubic |
| star(n=10) | 10 | 1.80 | 1.000000 | hub-and-spoke |
| star(n=16) | 16 | 1.88 | 1.000000 | hub-and-spoke |
| star(n=20) | 20 | 1.90 | 1.000000 | hub-and-spoke |
| grid(n≈9) | 9 | 2.67 | 1.000000 | 2-D grid, actual n=9 |
| desargues | 20 | 3.00 | 1.000000 | GP(10,3), n=20, cubic |
| star(n=8) | 8 | 1.75 | 1.000000 | hub-and-spoke |
| rand_reg(n=8,k=3) | 8 | 3.00 | 1.267949 | random 3-regular |
| pappus | 18 | 3.00 | 1.267949 | n=18, cubic |
| mobius_kantor | 16 | 3.00 | 1.267949 | GP(8,3), n=16, cubic |
| heawood | 14 | 3.00 | 1.585786 | n=14, cubic |
| hypercube(k=5) | 32 | 5.00 | 2.000000 | Q_5, n=2^5=32 |
| hypercube(k=4) | 16 | 4.00 | 2.000000 | Q_4, n=2^4=16 |
| hypercube(k=3) | 8 | 3.00 | 2.000000 | Q_3, n=2^3=8 |
| cube | 8 | 3.00 | 2.000000 | Q_3, n=8, cubic |
| petersen | 10 | 3.00 | 2.000000 | GP(5,2), n=10, cubic |
| complete(n=8) | 8 | 7.00 | 8.000000 | fully connected K_n |
| complete(n=10) | 10 | 9.00 | 10.000000 | fully connected K_n |
| complete(n=16) | 16 | 15.00 | 16.000000 | fully connected K_n |
| complete(n=20) | 20 | 19.00 | 20.000000 | fully connected K_n |

## Parameter Space

The full experiment varies the following dimensions:

| Parameter | Candidates |
|-----------|-----------|
| **topology** | none, ring, star, complete, grid, hypercube, random-regular, cube, petersen, heawood, mobius-kantor, pappus, dodecahedron, desargues |
| **n (islands)** | 8, 10, 14, 16, 18, 20, 25, 32 |
| **population per island** | 20, 50, 100 |
| **migration rate** | 0.01, 0.05, 0.1, 0.2 (fraction of island pop migrating per interval) |
| **migration interval** | 5, 10, 20, 50 generations |

## Files

| File | Purpose |
|------|---------|
| `topologies.py` | Adjacency matrices for all candidate topologies |
| `compute_lambda2.py` | Compute lambda_2 for all topologies, print markdown table |

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install networkx scipy numpy
python compute_lambda2.py
```

Or with `uv`:
```bash
uv venv
uv pip install networkx scipy numpy
.venv/bin/python compute_lambda2.py
```
