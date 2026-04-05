#!/usr/bin/env python3
"""Analyze Jaccard maze experiment results: diversity spread across topologies."""

import csv
import os
from collections import defaultdict
import math

RESULTS_DIR = "results/jaccard_maze_15x15"
SEEDS = [42, 1337, 2718]
TOPOLOGIES = [
    "disconnected", "ring", "star", "complete",
    "hypercube", "barbell", "watts-strogatz", "random-regular"
]

# Lambda_2 values from the README (n=8 islands)
LAMBDA2 = {
    "disconnected": 0.000,
    "ring": 0.586,
    "star": 1.000,
    "complete": 8.000,
    "hypercube": 2.000,
    "barbell": 0.069,  # approximate for n=8
    "watts-strogatz": 1.500,  # approximate
    "random-regular": 1.268,
}

def read_csv(filepath):
    """Read CSV and return list of dicts."""
    rows = []
    with open(filepath) as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                'generation': int(row['generation']),
                'meanFitness': float(row['meanFitness']),
                'bestFitness': float(row['bestFitness']),
                'diversity': float(row['diversity']),
            })
    return rows

def get_value_at_gen(rows, gen, field):
    """Get value at a specific generation."""
    for row in rows:
        if row['generation'] == gen:
            return row[field]
    # Return last row if gen not found
    return rows[-1][field] if rows else None

def main():
    # Collect data
    data = defaultdict(list)  # topo -> [(seed, rows), ...]

    for topo in TOPOLOGIES:
        for seed in SEEDS:
            filepath = os.path.join(RESULTS_DIR, f"{topo}_seed{seed}.csv")
            if os.path.exists(filepath):
                rows = read_csv(filepath)
                data[topo].append((seed, rows))

    # === DIVERSITY AT KEY GENERATIONS ===
    print("=" * 80)
    print("JACCARD MAZE EXPERIMENT — DIVERSITY ANALYSIS")
    print("Commit: db449ea | 15×15 maze | 8 islands | pop 50 | migrate 1/10 gens")
    print("=" * 80)

    # Diversity at gen 0, gen 50 (transient window), gen 250 (mid), gen 500 (final)
    checkpoints = [0, 30, 50, 100, 250, 500]

    print(f"\n{'Topology':<18} {'λ₂':>6}", end="")
    for g in checkpoints:
        print(f" {'div@'+str(g):>10}", end="")
    print(f" {'fit@500':>10}")
    print("-" * (18 + 7 + len(checkpoints) * 11 + 11))

    topo_div500 = {}
    topo_fit500 = {}
    topo_div_series = {}

    for topo in sorted(TOPOLOGIES, key=lambda t: LAMBDA2.get(t, 0)):
        l2 = LAMBDA2.get(topo, 0)

        divs = {}
        for g in checkpoints:
            vals = []
            for seed, rows in data[topo]:
                v = get_value_at_gen(rows, g, 'diversity')
                if v is not None:
                    vals.append(v)
            divs[g] = sum(vals) / len(vals) if vals else 0

        # Mean fitness at 500
        fit_vals = []
        for seed, rows in data[topo]:
            v = get_value_at_gen(rows, 500, 'meanFitness')
            if v is not None:
                fit_vals.append(v)
        mean_fit = sum(fit_vals) / len(fit_vals) if fit_vals else 0

        topo_div500[topo] = divs[500]
        topo_fit500[topo] = mean_fit
        topo_div_series[topo] = divs

        print(f"{topo:<18} {l2:>6.3f}", end="")
        for g in checkpoints:
            print(f" {divs[g]:>10.4f}", end="")
        print(f" {mean_fit:>10.4f}")

    # === SPREAD ANALYSIS ===
    print(f"\n{'=' * 80}")
    print("DIVERSITY SPREAD")
    print(f"{'=' * 80}")

    divs_500 = [topo_div500[t] for t in TOPOLOGIES]
    div_range = max(divs_500) - min(divs_500)
    div_mean = sum(divs_500) / len(divs_500)
    div_std = math.sqrt(sum((d - div_mean) ** 2 for d in divs_500) / len(divs_500))

    print(f"\nAt gen 500:")
    print(f"  Range:  {div_range:.4f} (max - min)")
    print(f"  Mean:   {div_mean:.4f}")
    print(f"  StdDev: {div_std:.4f}")
    print(f"  Max:    {max(divs_500):.4f} ({max(topo_div500, key=topo_div500.get)})")
    print(f"  Min:    {min(divs_500):.4f} ({min(topo_div500, key=topo_div500.get)})")

    # Compare with prior Hamming result
    print(f"\n  Prior Hamming range at gen 500: 0.005 (0.9927 - 0.9977)")
    print(f"  Jaccard range at gen 500:       {div_range:.4f}")
    print(f"  Improvement factor:             {div_range / 0.005:.1f}×")

    # === TRANSIENT WINDOW ===
    print(f"\n{'=' * 80}")
    print("TRANSIENT WINDOW ANALYSIS (gen 0–50)")
    print(f"{'=' * 80}")

    # Diversity drop from gen 0 to gen 50
    print(f"\n{'Topology':<18} {'λ₂':>6} {'div@0':>8} {'div@50':>8} {'drop':>8} {'drop%':>8}")
    print("-" * 58)
    for topo in sorted(TOPOLOGIES, key=lambda t: LAMBDA2.get(t, 0)):
        l2 = LAMBDA2.get(topo, 0)
        d0 = topo_div_series[topo][0]
        d50 = topo_div_series[topo][50]
        drop = d0 - d50
        drop_pct = (drop / d0 * 100) if d0 > 0 else 0
        print(f"{topo:<18} {l2:>6.3f} {d0:>8.4f} {d50:>8.4f} {drop:>8.4f} {drop_pct:>7.1f}%")

    # === RANK CORRELATION (Spearman) ===
    print(f"\n{'=' * 80}")
    print("RANK CORRELATION: λ₂ vs diversity at gen 500")
    print(f"{'=' * 80}")

    # Sort by lambda2 and by diversity
    topos_by_l2 = sorted(TOPOLOGIES, key=lambda t: LAMBDA2.get(t, 0))
    topos_by_div = sorted(TOPOLOGIES, key=lambda t: topo_div500[t], reverse=True)  # higher diversity = more preserved

    print(f"\n{'Rank':<6} {'By λ₂ (ascending)':>22} {'By diversity@500 (desc)':>28}")
    print("-" * 58)
    for i in range(len(TOPOLOGIES)):
        print(f"{i+1:<6} {topos_by_l2[i]:>22} {topos_by_div[i]:>28}")

    # Spearman rank correlation
    n = len(TOPOLOGIES)
    ranks_l2 = {t: i for i, t in enumerate(topos_by_l2)}
    ranks_div = {t: i for i, t in enumerate(topos_by_div)}
    d_sq = sum((ranks_l2[t] - ranks_div[t]) ** 2 for t in TOPOLOGIES)
    rho = 1 - 6 * d_sq / (n * (n * n - 1))
    print(f"\nSpearman ρ = {rho:.3f}")
    print(f"(Prior Hamming: ρ = 0.12)")

    # === PER-SEED VARIANCE ===
    print(f"\n{'=' * 80}")
    print("PER-SEED DIVERSITY AT GEN 500 (checking consistency)")
    print(f"{'=' * 80}")

    print(f"\n{'Topology':<18}", end="")
    for seed in SEEDS:
        print(f" {'seed '+str(seed):>12}", end="")
    print(f" {'std':>8}")
    print("-" * 60)

    for topo in sorted(TOPOLOGIES, key=lambda t: LAMBDA2.get(t, 0)):
        vals = []
        print(f"{topo:<18}", end="")
        for seed, rows in data[topo]:
            v = get_value_at_gen(rows, 500, 'diversity')
            vals.append(v)
            print(f" {v:>12.4f}", end="")
        std = math.sqrt(sum((v - sum(vals)/len(vals))**2 for v in vals) / len(vals)) if vals else 0
        print(f" {std:>8.4f}")

    # === STAR AND BARBELL ANOMALY CHECK ===
    print(f"\n{'=' * 80}")
    print("ANOMALY CHECK: Star & Barbell")
    print(f"{'=' * 80}")

    star_div = topo_div500.get("star", 0)
    barbell_div = topo_div500.get("barbell", 0)
    ring_div = topo_div500.get("ring", 0)

    print(f"\nStar (λ₂=1.0):    div@500 = {star_div:.4f}")
    print(f"Ring (λ₂=0.586):  div@500 = {ring_div:.4f}")
    print(f"Barbell (λ₂≈0.07): div@500 = {barbell_div:.4f}")

    if star_div > ring_div:
        print(f"\n→ Star preserves MORE diversity than Ring despite higher λ₂")
        print(f"  (hub bottleneck effect — replicates OneMax finding)")
    else:
        print(f"\n→ Star preserves LESS diversity than Ring (follows λ₂ prediction)")

    if barbell_div < ring_div:
        print(f"→ Barbell preserves LESS diversity than Ring (follows λ₂ prediction)")
    else:
        print(f"→ Barbell preserves MORE diversity than Ring despite lower λ₂")
        print(f"  (intra-clique effect — replicates OneMax finding)")

if __name__ == "__main__":
    main()
