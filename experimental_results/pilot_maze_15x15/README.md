# Pilot Study: 15×15 Maze Domain

**Date:** 2026-03-29
**Code branch:** main (PR #2)
**Conducted by:** Lyra

## Purpose

Validate that the island-model GA framework can produce measurable topology effects on diversity and fitness for the maze domain.

## Parameters

| Parameter | Value |
|-----------|-------|
| Domain | Maze (15×15 grid) |
| Genome | Permutation of 420 edges |
| Fitness function | BFS path length / num_cells (pure path length) |
| Population per island | 50 |
| Islands | 8 |
| Generations | 500 |
| Seeds | 3 (42, 1337, 2718) |
| Topologies | 8 (see below) |
| Total runs | 24 |
| Wall-clock time | ~36 minutes (parallel, 8 CPUs) |

## Topologies Tested

| Topology | λ₂ | Predicted rank |
|----------|----|----------------|
| Complete | 8.00 | 1 (fastest) |
| Hypercube | 2.00 | 2 |
| Watts-Strogatz | ~1.50 | 3 |
| Star | 1.00 | 4 |
| Ring | 0.59 | 5 |
| Random-Regular | 0.27 | 6 |
| Barbell | 0.07 | 7 |
| Disconnected | 0.00 | 8 (slowest) |

## Results

### Diversity

| Topology | Diversity gen 0 | Diversity gen 500 | Change |
|----------|-----------------|-------------------|--------|
| Complete | ~0.997 | ~0.993 | −0.004 |
| Hypercube | ~0.997 | ~0.994 | −0.003 |
| Watts-Strogatz | ~0.997 | ~0.996 | −0.001 |
| Star | ~0.997 | ~0.997 | ~0.000 |
| Ring | ~0.997 | ~0.995 | −0.002 |
| Random-Regular | ~0.997 | ~0.994 | −0.003 |
| Barbell | ~0.997 | ~0.993 | −0.004 |
| Disconnected | ~0.997 | ~0.998 | +0.001 |

**Diversity range at gen 500:** 0.005 (0.9927 – 0.9977)

### Fitness

| Metric | Gen 0 | Gen 500 |
|--------|-------|---------|
| Mean fitness (all topologies) | ~0.29 | ~0.35 |
| Best fitness observed | ~0.32 | ~0.38 |

### Correlation (λ₂ vs diversity at gen 500)

Spearman ρ = 0.12 — **not significant**.

## Interpretation

**Null result.** The 420-element permutation genome produces near-maximal pairwise Hamming distance even between random individuals (theoretical max diversity ≈ 0.998 for random 420-permutations). With population size 50 per island (400 total), the GA cannot exhaust the search space in 500 generations, so diversity never decays enough for topology effects to emerge. This is a **floor effect** at the diversity ceiling.

The fitness signal (0.29 → 0.35) is also modest — the GA has not converged. Topology cannot be observed acting on a population that isn't yet experiencing selection pressure on diversity.

## Conclusion

The 15×15 maze with permutation genome is **not a suitable domain** for measuring migration topology effects at these population sizes and generation counts. The issue is genome length relative to population size — not the fitness function.

Two remedies were explored:
1. Smaller maze (8×8) — see `pilot_maze_8x8/`
2. Different domain with binary genome — see `onemax_transient_10runs/`
