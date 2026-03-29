# Pilot Study: 8×8 Maze Domain

**Date:** 2026-03-29
**Code branch:** feat/8x8-maze-pilot
**Conducted by:** Lyra

## Purpose

Determine whether reducing maze size (shorter genome) resolves the diversity floor effect seen in the 15×15 pilot.

## Parameters

| Parameter | Value |
|-----------|-------|
| Domain | Maze (8×8 grid) |
| Genome | Permutation of ~112 edges |
| Fitness function | BFS path length / num_cells (pure path length) |
| Population per island | 50 |
| Islands | 8 |
| Generations | 500 |
| Seeds | 3 |
| Topologies | 8 |
| Total runs | 24 |

## Results

### Diversity

All topologies maintain diversity **>0.97** throughout 500 generations.

Approximately **2× faster diversity decay** than 15×15, but still far from the regime where topology effects would be detectable.

### Fitness

Best fitness observed: ~0.573 (hypercube, seed 2718) = path covering ~86/64 cells.

**Topology ordering on fitness at gen 500:**

| Topology | Best fitness (approx) |
|----------|-----------------------|
| Complete | 0.573 |
| Hypercube | ~0.552 |
| Watts-Strogatz | ~0.548 |
| Ring | ~0.545 |
| Star | ~0.542 |
| Random-Regular | ~0.540 |
| Barbell | ~0.531 |
| Disconnected | ~0.521 |

Note: Complete graph (λ₂ = 8.0) reaches highest fitness — topology IS doing something, but Hamming diversity metric cannot detect it.

### Correlation

λ₂ vs diversity at gen 500: ρ ≈ 0 — not significant.
λ₂ vs best fitness at gen 500: weak positive correlation (not tested for significance).

## Key Finding

**Hamming distance on permutation genomes is the wrong diversity metric.**

A small structural change in a maze (e.g. swapping two edges) produces very different permutation vectors. Even genomes that encode similar maze structures differ at most positions. Genotypic Hamming distance saturates quickly and does not track phenotypic (structural) convergence.

The topology signal exists (fitness ordering roughly matches λ₂ prediction at gen 500), but the standard diversity metric cannot reveal it.

## Conclusion

8×8 maze is not sufficient to fix the floor effect. The problem is **metric mismatch**, not genome length alone.

Two remedies:
1. **Phenotypic diversity** (measure maze structural similarity, not permutation Hamming distance) — requires non-trivial implementation
2. **Different domain with a meaningful genotypic metric** — OneMax (binary genome, Hamming distance IS phenotypic) was explored next (see `onemax_transient_10runs/`)
