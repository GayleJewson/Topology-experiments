# Topology-Experiments: Experimental Results

This directory contains tabulated results from all pilot and full runs.
Each subdirectory contains a `README.md` describing the experiment parameters and results.

## Overview

| Study | Domain | Genome | Pop | Gens | Topologies | Runs | Key Finding |
|-------|--------|--------|-----|------|------------|------|-------------|
| [pilot_maze_15x15](pilot_maze_15x15/) | Maze (15×15) | Permutation (420) | 50/island | 500 | 8 | 3 | No signal — genome too long |
| [pilot_maze_8x8](pilot_maze_8x8/) | Maze (8×8) | Permutation (112) | 50/island | 500 | 8 | 3 | No signal — same floor effect |
| [onemax_transient_10runs](onemax_transient_10runs/) | OneMax | Binary (100) | 50/island | 500 | 8 | 10 | **88% variance at gen 30; Star + Barbell anomalies** |

## Key Result

λ₂ (algebraic connectivity) predicts topology effects on convergence speed during the **transient window** (gen 0–40), with two categorical anomalies:

- **Star** (λ₂ = 1.0) behaves like a near-disconnected graph — hub bottleneck not captured by global scalar
- **Barbell** (λ₂ = 0.07) outperforms its spectral prediction — intra-clique structure not captured by global scalar

These anomalies are the empirical argument for categorical/compositional analysis beyond λ₂.

## Common Parameters

Unless noted otherwise:

| Parameter | Value |
|-----------|-------|
| Islands | 8 |
| Population per island | 50 (400 total) |
| Migration rate | 1 individual per island per migration event |
| Migration interval | Every 10 generations |
| Selection | Tournament (k=3) |
| Crossover | Order crossover (OX) for permutation; uniform for binary |
| Mutation | Swap mutation for permutation; bit-flip for binary |
| Diversity metric | Hamming distance (mean pairwise) |

## Hardware / Timing

All experiments run in parallel across 8 CPUs.
Wall-clock timings reported per study.
