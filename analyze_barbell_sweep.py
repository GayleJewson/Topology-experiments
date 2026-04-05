#!/usr/bin/env python3
"""Analyze barbell bridge-width sweep: diversity vs bridge width on Sudoku."""

import csv
import os
import math
from collections import defaultdict

RESULTS_DIR = "results/barbell_sweep"
SEEDS = [42, 1337, 2718]
BRIDGE_WIDTHS = [1, 2, 4, 8, 12, 16]

# Lambda_2 computed by compute_barbell_lambda2.py
LAMBDA2 = {1: 0.3542, 2: 0.6277, 4: 1.2004, 8: 2.3187, 12: 3.8299, 16: 8.0000}

# Reference values from the full Sudoku experiment
REF_DISCONNECTED_DIV500 = 0.6529
REF_COMPLETE_DIV500 = 0.2796
REF_RING_DIV500 = 0.6374

def read_csv(filepath):
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

def get_at_gen(rows, gen, field):
    for row in rows:
        if row['generation'] == gen:
            return row[field]
    return rows[-1][field] if rows else None

def mean(vals):
    return sum(vals) / len(vals) if vals else 0

def std(vals):
    m = mean(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / len(vals)) if vals else 0

def main():
    data = defaultdict(list)  # bridge_width -> [(seed, rows)]

    for b in BRIDGE_WIDTHS:
        for seed in SEEDS:
            fp = os.path.join(RESULTS_DIR, f"barbell-{b}_seed{seed}.csv")
            if os.path.exists(fp):
                data[b].append((seed, read_csv(fp)))

    print("=" * 80)
    print("BARBELL BRIDGE-WIDTH SWEEP — SUDOKU")
    print("n=8 islands, two 4-node cliques, variable cross-clique edges")
    print("=" * 80)

    # === MAIN TABLE ===
    checkpoints = [0, 20, 50, 100, 250, 500]

    print(f"\n{'Bridge':>7} {'λ₂':>7}", end="")
    for g in checkpoints:
        print(f" {'div@'+str(g):>8}", end="")
    print(f" {'fit@500':>8}")
    print("-" * (7 + 8 + len(checkpoints) * 9 + 9))

    div500 = {}
    fit500 = {}
    div_at = {}

    for b in BRIDGE_WIDTHS:
        l2 = LAMBDA2[b]
        divs = {}
        for g in checkpoints:
            vals = [get_at_gen(rows, g, 'diversity') for _, rows in data[b]]
            vals = [v for v in vals if v is not None]
            divs[g] = mean(vals)

        fvals = [get_at_gen(rows, 500, 'meanFitness') for _, rows in data[b]]
        fvals = [v for v in fvals if v is not None]

        div500[b] = divs[500]
        fit500[b] = mean(fvals)
        div_at[b] = divs

        print(f"{'b='+str(b):>7} {l2:>7.4f}", end="")
        for g in checkpoints:
            print(f" {divs[g]:>8.4f}", end="")
        print(f" {mean(fvals):>8.4f}")

    # === DIVERSITY vs BRIDGE WIDTH (the money plot) ===
    print(f"\n{'=' * 80}")
    print("DIVERSITY @ GEN 500 vs BRIDGE WIDTH")
    print(f"{'=' * 80}")

    print(f"\n  Reference lines:")
    print(f"    Disconnected (no migration):  {REF_DISCONNECTED_DIV500:.4f}")
    print(f"    Ring (λ₂=0.586):              {REF_RING_DIV500:.4f}")
    print(f"    Complete (λ₂=8.0):            {REF_COMPLETE_DIV500:.4f}")
    print()

    # ASCII bar chart
    min_div = min(min(div500.values()), REF_COMPLETE_DIV500) - 0.02
    max_div = max(max(div500.values()), REF_DISCONNECTED_DIV500) + 0.02
    bar_width = 50

    for b in BRIDGE_WIDTHS:
        d = div500[b]
        l2 = LAMBDA2[b]
        pos = int((d - min_div) / (max_div - min_div) * bar_width)
        bar = " " * pos + "█"
        # Show per-seed values
        seed_vals = [get_at_gen(rows, 500, 'diversity') for _, rows in data[b]]
        seed_str = ", ".join(f"{v:.3f}" for v in seed_vals)
        print(f"  b={b:>2} (λ₂={l2:.2f}) |{bar:<{bar_width+1}}| {d:.4f}  [{seed_str}]")

    # Mark reference lines
    ring_pos = int((REF_RING_DIV500 - min_div) / (max_div - min_div) * bar_width)
    print(f"  {'Ring':>14} |{' ' * ring_pos}↑{' ' * (bar_width - ring_pos)}| {REF_RING_DIV500:.4f}")

    # === SPECTRAL PREDICTION vs ACTUAL ===
    print(f"\n{'=' * 80}")
    print("λ₂ PREDICTION vs ACTUAL DIVERSITY")
    print("If λ₂ fully explains diversity, points should follow a monotone decreasing curve")
    print(f"{'=' * 80}")

    # Normalize: disconnected=1.0, complete=0.0
    div_range = REF_DISCONNECTED_DIV500 - REF_COMPLETE_DIV500

    print(f"\n{'Bridge':>7} {'λ₂':>7} {'div@500':>8} {'normalized':>11} {'λ₂ rank':>9} {'div rank':>9} {'match':>7}")
    print("-" * 62)

    sorted_by_l2 = sorted(BRIDGE_WIDTHS, key=lambda b: LAMBDA2[b])
    sorted_by_div = sorted(BRIDGE_WIDTHS, key=lambda b: div500[b], reverse=True)
    l2_rank = {b: i+1 for i, b in enumerate(sorted_by_l2)}
    div_rank = {b: i+1 for i, b in enumerate(sorted_by_div)}

    for b in BRIDGE_WIDTHS:
        norm = (div500[b] - REF_COMPLETE_DIV500) / div_range if div_range > 0 else 0
        match = "✓" if l2_rank[b] == div_rank[b] else ""
        print(f"{'b='+str(b):>7} {LAMBDA2[b]:>7.4f} {div500[b]:>8.4f} {norm:>10.3f} {l2_rank[b]:>9} {div_rank[b]:>9} {match:>7}")

    # Spearman
    n = len(BRIDGE_WIDTHS)
    d_sq = sum((l2_rank[b] - div_rank[b]) ** 2 for b in BRIDGE_WIDTHS)
    rho = 1 - 6 * d_sq / (n * (n * n - 1))
    print(f"\n  Spearman ρ(λ₂, diversity@500) = {rho:.3f}")

    # === CROSSOVER ANALYSIS ===
    print(f"\n{'=' * 80}")
    print("CROSSOVER ANALYSIS: Where does barbell stop being anomalous?")
    print(f"{'=' * 80}")

    # The barbell is "anomalous" when its diversity is higher than what
    # its λ₂ would predict relative to the other topologies in the full experiment.
    # A simple test: is div@500 > Ring's div@500 (Ring has λ₂=0.586)?
    print(f"\n  Ring reference: div@500 = {REF_RING_DIV500:.4f} (λ₂ = 0.586)")
    print()
    for b in BRIDGE_WIDTHS:
        l2 = LAMBDA2[b]
        d = div500[b]
        above_ring = d > REF_RING_DIV500
        status = "ABOVE Ring (anomalous — λ₂ predicts lower)" if above_ring and l2 > 0.586 else \
                 "ABOVE Ring (expected — λ₂ < Ring's λ₂)" if above_ring else \
                 "BELOW Ring"
        print(f"  b={b:>2} (λ₂={l2:.4f}): div={d:.4f}  → {status}")

    # === PER-SEED VARIANCE ===
    print(f"\n{'=' * 80}")
    print("PER-SEED CONSISTENCY")
    print(f"{'=' * 80}")

    print(f"\n{'Bridge':>7}", end="")
    for seed in SEEDS:
        print(f" {'seed '+str(seed):>10}", end="")
    print(f" {'mean':>8} {'std':>8}")
    print("-" * 50)

    for b in BRIDGE_WIDTHS:
        vals = [get_at_gen(rows, 500, 'diversity') for _, rows in data[b]]
        print(f"{'b='+str(b):>7}", end="")
        for v in vals:
            print(f" {v:>10.4f}", end="")
        print(f" {mean(vals):>8.4f} {std(vals):>8.4f}")

if __name__ == "__main__":
    main()
