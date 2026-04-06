# Jaccard Maze Experiment (15×15)

**Date:** 2026-04-05
**Commit:** db449ea (maze: replace Hamming with Jaccard spanning-tree phenotype)
**Conducted by:** Robin (runner for Claudius)

## Purpose

Re-run the 15×15 maze pilot with the Jaccard phenotype distance metric
(replacing Hamming on edge permutations) to test whether the floor effect
at diversity ~0.997 was caused by the metric rather than the domain.

## Parameters

Same as the original pilot_maze_15x15, except diversity metric:

| Parameter | Value |
|-----------|-------|
| Domain | Maze (15×15 grid) |
| Genome | Permutation of 420 edges |
| Fitness | BFS path length / num_cells |
| **Distance metric** | **Jaccard on decoded spanning-tree edge sets** |
| Population per island | 50 |
| Islands | 8 |
| Generations | 500 |
| Seeds | 3 (42, 1337, 2718) |
| Topologies | 8 |
| Total runs | 24 |

## Results

### Diversity at gen 500 (mean of 3 seeds)

| Topology | λ₂ | div@500 |
|----------|-----|---------|
| Complete | 8.000 | 0.625 |
| Star | 1.000 | 0.622 |
| Disconnected | 0.000 | 0.620 |
| Random-Regular | 1.268 | 0.619 |
| Watts-Strogatz | 1.500 | 0.619 |
| Barbell | 0.069 | 0.617 |
| Hypercube | 2.000 | 0.616 |
| Ring | 0.586 | 0.613 |

**Diversity range:** 0.012 (vs 0.005 with Hamming — 2.3× improvement)
**Spearman ρ(λ₂, div@500):** −0.19 (not significant)

### Interpretation

The Jaccard fix reduced the floor (0.997 → 0.636 at gen 0) and widened the
spread 2.3×, confirming the old Hamming metric was the primary cause of the
floor effect. However, the signal remains weak: the GA barely converges on
15×15 mazes (fitness 0.18 → 0.20 over 500 gens), so selection pressure is
too low for topology to sculpt diversity.

**Conclusion:** Jaccard is the correct metric, but the maze domain needs
stronger convergence (larger pop, more gens, or smaller grid) to show
topology effects. Sudoku is a better domain — see `results/sudoku/`.

## Files

```
<topology>_seed<seed>.csv  — simulation output
<topology>_seed<seed>.log  — stderr log
```
