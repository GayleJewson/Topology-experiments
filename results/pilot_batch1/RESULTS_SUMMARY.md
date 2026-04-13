# Pilot Study Results: Batch 1

**Date:** 2026-03-29
**Configuration:** 3 runs x 8 topologies x 500 generations
**Fitness:** BFS-only (path length / N^2)
**Domain:** 15x15 maze, Kruskal permutation encoding
**GA:** 8 islands, pop=50/island, migInterval=10, migrants=5, tournament size 3

## Key Finding: NO DIVERSITY SIGNAL AT 500 GENERATIONS

The pilot study reveals that **500 generations is far too few** to observe meaningful diversity differences between topologies in this domain. All 8 topologies maintain diversity above 0.99 throughout the entire run.

### Why This Happened

1. **Genome length is 420** (number of internal edges in 15x15 grid). Two random permutations differ at ~99.7% of positions. Even after 500 generations of selection, diversity barely moves.

2. **BFS fitness is a weak selector.** Best fitness reaches ~0.35 (path length ~79 out of 225 cells) — far below the theoretical maximum (~1.0, a Hamiltonian path). The GA is not converging because the fitness landscape has many similar-quality local optima.

3. **50 generations between observations is too coarse.** With migInterval=10 and 50 checkpoints (every 10 gens), we see noisy fluctuations, not trends.

### Raw Numbers at Generation 500

| Topology | lambda_2 | Avg Diversity | Std Dev | Avg Best Fitness |
|----------|----------|--------------|---------|-----------------|
| Barbell | 0.07 | 0.99774 | 0.00052 | 0.3585 |
| Hypercube | 2.00 | 0.99762 | 0.00021 | 0.3556 |
| Random-regular | 0.27 | 0.99742 | 0.00107 | 0.3526 |
| Star | 1.00 | 0.99718 | 0.00132 | 0.3319 |
| Complete | 8.00 | 0.99710 | 0.00090 | 0.3467 |
| Disconnected | 0.00 | 0.99595 | 0.00180 | 0.3467 |
| Ring | 0.59 | 0.99516 | 0.00297 | 0.3348 |
| Watts-Strogatz | 1.50 | 0.99270 | 0.00773 | 0.3378 |

### Diversity Spread

- **Total diversity range:** 0.99774 - 0.99270 = **0.00504**
- **Standard deviations within topologies:** 0.0002 to 0.0077
- **Signal-to-noise ratio:** The inter-topology variation (0.005) is comparable to intra-topology variation (std devs). This means the ordering is effectively noise.

### Spearman Rank Correlation

**rho = 0.12** (lambda_2 ascending vs. diversity descending)

This is essentially zero correlation. The predicted ordering (Disconnected > Barbell > Ring > Random-regular > Star > Watts-Strogatz > Hypercube > Complete) does not match the observed ordering.

### Diversity Drop from Initial to Final

The maximum diversity drop across all topologies is **0.45%** (Watts-Strogatz). Most topologies show drops of < 0.2%. Several show *increases* in average diversity, which is just noise.

## Timing

| Topology | Avg Time (s) |
|----------|-------------|
| Disconnected | 2171.5 |
| Ring | 2179.1 |
| Star | 2173.5 |
| Complete | 2175.2 |
| Hypercube | 2176.6 |
| Barbell | 2174.3 |
| Watts-Strogatz | 2179.1 |
| Random-regular | 2177.9 |

- **All topologies run at the same speed** (~36 minutes per run with 24 parallel jobs)
- **Total CPU time:** 52,221 seconds (870 minutes)
- **Wall-clock time:** ~36 minutes (24 parallel jobs on available CPUs)
- **Per-run sequential estimate:** ~90 seconds (when running 1 at a time — extrapolated from CPU/wall ratio)

Note: The high wall-clock per run (36 min) is due to 24 jobs competing for CPU. When running fewer in parallel, each run would be much faster.

## Diagnosis and Recommendations

### Problem 1: Genome too long for diversity to decay in 500 generations
The 420-position permutation genome means initial diversity is 0.997. Even with strong selection, it would take thousands of generations for diversity to drop meaningfully. The diversity metric (Hamming distance) measures raw genotype difference, not phenotypic similarity.

**Fix options:**
- (a) Run for 5,000-10,000 generations
- (b) Use a smaller maze (e.g., 8x8 = 92 edges, diversity will decay faster)
- (c) Switch to a phenotypic diversity metric (e.g., BFS path similarity, tree edit distance)
- (d) Increase selection pressure (larger tournament size, elitism)

### Problem 2: BFS fitness has low selective pressure
Best fitness barely improves from 0.29 (gen 0) to 0.35 (gen 500). The landscape has many flat plateaus — most random permutations produce mazes with similar path lengths.

**Fix options:**
- (a) Switch to composite fitness (path length + dead ends + junctions) — Claudius's commit `726fa99`
- (b) Increase population pressure (reduce pop size, increase tournament size)
- (c) Use a domain with stronger selection (e.g., a numeric optimization problem)

### Problem 3: Not enough runs for statistical power
With 3 runs and diversity differences of 0.005, we need far more runs (10+) to distinguish signal from noise, even if the signal existed.

### Recommended Next Steps (in priority order)

1. **Run for 5,000 generations** (10x longer) with the same parameters. Check if diversity trends become visible.
2. **Switch to 8x8 maze** — faster per run, shorter genome, diversity decays faster.
3. **Consider phenotypic diversity** — measure how similar the actual maze structures are, not just the genome encoding.
4. **Use 10 runs per topology** as originally planned in DESIGN_DECISIONS.md.
5. **Consider a domain where selection pressure is stronger** — e.g., TSP, OneMax, or a deceptive function where topology effects are known to be large.

## Files

- Raw CSV data: `results/pilot_batch1/<topology>_seed<seed>.csv`
- Per-run logs: `results/pilot_batch1/<topology>_seed<seed>.log`
- Per-run timing: `results/pilot_batch1/<topology>_seed<seed>.time`
- Full analysis output: `results/pilot_batch1/ANALYSIS.txt`
- Analysis script: `analyze_pilot.py`
- Runner script: `run_pilot.sh`
