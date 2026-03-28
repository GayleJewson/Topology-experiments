# Design Decisions

Record of all key design decisions for the island-model GA topology experiment.
Each entry includes the decision, rationale, and date.

---

## 1. Domain Sequence

**Decision:** Maze generation (domain 1) → Checkers (domain 2)

**Rationale:** Maze offers fast evaluation (BFS is O(N²)), clean combinatorial structure,
and a genome that always produces valid solutions. Run all topologies through maze first,
then move to checkers once the pipeline is validated.

**Date:** 2026-03-28

---

## 2. Maze Size

**Decision:** 15 × 15 grid (225 cells)

**Rationale:**
- 5×5 is too trivial — insufficient solution-space diversity
- 10×10 is standard in the GA-maze literature but may converge too quickly at pop=50
- 15×15 gives ~420 internal edges (spanning tree has 224 edges), creating rich genetic diversity
- BFS evaluation is O(N²) = O(225), negligible; simulation time is dominated by generations

**Revisit:** increase to 20×20 if empirical convergence is too fast; decrease if wall-clock
time becomes a problem after Lyra's timing estimates.

**Date:** 2026-03-28

---

## 3. GA Parameters (Starting Values)

| Parameter              | Value   | Notes                              |
|------------------------|---------|------------------------------------|
| Population per island  | 50      |                                    |
| Generations between migrations | 10 |                               |
| Migrants per event     | 5 (10%) |                                    |
| Available CPUs         | 8       | Run topology batches in parallel   |

**Date:** 2026-03-28

---

## 4. Genome / Representation

**Decision:** Kruskal's permutation encoding

Each individual is a **permutation of all internal edges** of the 15×15 grid (~420 edges).
The maze is constructed by running Kruskal's algorithm in the order given by the permutation:
iterate through edges; add an edge if it connects two previously disconnected components
(union-find). Stop when N²-1 = 224 edges have been added. The result is always a
**perfect maze** — a spanning tree of the grid — with no invalid states.

**Why this encoding:**
- Any permutation → valid perfect maze, no repair step needed
- Crossover and mutation cannot produce degenerate mazes
- The fitness landscape is well-defined over the space of grid spanning trees
- Genome length is fixed (number of internal edges), simplifying crossover bookkeeping

**Date:** 2026-03-28

---

## 5. Fitness Function

**Decision:** BFS shortest-path length from top-left (0,0) to bottom-right (N-1,N-1),
normalized by N²

```
f(maze) = BFS_distance((0,0), (N-1,N-1)) / N²
```

**Intuition:** In a perfect maze every cell pair has exactly one path. A longer solution
path means more winding, more dead-ends, a harder maze. Maximising f pushes evolution
toward mazes where the solution is non-trivially obfuscated.

**Properties:**
- Fast to compute: BFS is O(N²) on the adjacency graph
- Fitness landscape has many local optima (many near-diameter spanning trees)
- Normalized by N² → value in (0,1], comparable across maze sizes if we later vary N

**Date:** 2026-03-28

---

## 6. Crossover Operator

**Decision:** Order Crossover (OX) on permutations

1. Choose two random cut points in the genome
2. Copy the segment between cut points from parent 1 directly into the offspring
3. Scan parent 2 from the second cut point (wrapping around) and append edges in that
   order, skipping any already present in the offspring

Preserves relative ordering of edge subsets from both parents while guaranteeing a
valid permutation.

**Date:** 2026-03-28

---

## 7. Mutation Operator

**Decision:** Random swap — choose two random positions in the permutation and swap them

Probability: 1/L per individual per generation (expected one swap per chromosome).

**Date:** 2026-03-28

---

## 8. Topologies Tested (Batch 1 — Maze Domain)

8 islands. Chosen to span the λ₂ range cleanly using `topology_zoo.py` generators.

| Topology             | λ₂ (approx, n=8) | Notes                          |
|----------------------|------------------|--------------------------------|
| Disconnected         | 0                | No migration — baseline        |
| Ring                 | 0.59             | Slow mixing                    |
| Barbell              | ~0.07            | Bottleneck between two cliques |
| Star                 | 1.0              | Hub-mediated migration         |
| Watts-Strogatz       | ~1.5             | Small-world                    |
| Hypercube (k=3)      | 2.0              | Structured fast mixing         |
| Random regular (d=3) | ~0.27            | Expander-like                  |
| Fully connected      | 8.0              | Baseline fast                  |

**Prediction:** Diversity ordering should track λ₂ inversely —
Disconnected > Barbell > Ring > Random-regular > Star > Watts-Strogatz > Hypercube > Fully-connected

**Date:** 2026-03-28

---

## 9. Diversity Metric

**Decision:** Pairwise Hamming distance averaged over all pairs in the population

For permutation genomes, Hamming distance = number of positions where the two
permutations differ. Average over all N*(N-1)/2 pairs gives a scalar in [0,1]
(normalized by genome length).

Record mean diversity every `migration_interval` generations.

**Date:** 2026-03-28

---

## 10. Statistical Design

- Minimum 10 independent runs per topology (different random seeds)
- Primary statistic: diversity at generation 100, 500, final generation
- Secondary: generations until diversity drops below 0.1 (convergence time)
- Parallel execution: all 8 topology runs for a given configuration launched simultaneously

**Date:** 2026-03-28
