#!/usr/bin/env python3
"""Analyze Sudoku topology experiment results."""

import csv
import os
from collections import defaultdict
import math

RESULTS_DIR = "results/sudoku"
SEEDS = [42, 1337, 2718]
TOPOLOGIES = [
    "disconnected", "ring", "star", "complete",
    "hypercube", "barbell", "watts-strogatz", "random-regular"
]

LAMBDA2 = {
    "disconnected": 0.000,
    "ring": 0.586,
    "star": 1.000,
    "complete": 8.000,
    "hypercube": 2.000,
    "barbell": 0.069,
    "watts-strogatz": 1.500,
    "random-regular": 1.268,
}

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

def get_value_at_gen(rows, gen, field):
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
    data = defaultdict(list)
    for topo in TOPOLOGIES:
        for seed in SEEDS:
            filepath = os.path.join(RESULTS_DIR, f"{topo}_seed{seed}.csv")
            if os.path.exists(filepath):
                rows = read_csv(filepath)
                data[topo].append((seed, rows))

    checkpoints = [0, 10, 20, 30, 50, 100, 250, 500]

    print("=" * 90)
    print("SUDOKU TOPOLOGY EXPERIMENT — RESULTS")
    print("Commit: 79b23a7 | AI Escargot (23 givens) | 8 islands | pop 50 | migrate 1/10 gens")
    print("=" * 90)

    # === MAIN TABLE ===
    print(f"\n{'Topology':<18} {'λ₂':>6}", end="")
    for g in checkpoints:
        print(f" {'div@'+str(g):>8}", end="")
    print()
    print("-" * (18 + 7 + len(checkpoints) * 9))

    topo_divs = {}  # topo -> {gen: mean_div}
    topo_fits = {}  # topo -> {gen: mean_fit}

    for topo in sorted(TOPOLOGIES, key=lambda t: LAMBDA2.get(t, 0)):
        l2 = LAMBDA2.get(topo, 0)
        divs = {}
        fits = {}
        for g in checkpoints:
            dvals = [get_value_at_gen(rows, g, 'diversity') for _, rows in data[topo]]
            fvals = [get_value_at_gen(rows, g, 'meanFitness') for _, rows in data[topo]]
            dvals = [v for v in dvals if v is not None]
            fvals = [v for v in fvals if v is not None]
            divs[g] = mean(dvals)
            fits[g] = mean(fvals)
        topo_divs[topo] = divs
        topo_fits[topo] = fits

        print(f"{topo:<18} {l2:>6.3f}", end="")
        for g in checkpoints:
            print(f" {divs[g]:>8.4f}", end="")
        print()

    # === FITNESS TABLE ===
    print(f"\n{'Topology':<18} {'λ₂':>6}", end="")
    for g in checkpoints:
        print(f" {'fit@'+str(g):>8}", end="")
    print()
    print("-" * (18 + 7 + len(checkpoints) * 9))

    for topo in sorted(TOPOLOGIES, key=lambda t: LAMBDA2.get(t, 0)):
        l2 = LAMBDA2.get(topo, 0)
        print(f"{topo:<18} {l2:>6.3f}", end="")
        for g in checkpoints:
            print(f" {topo_fits[topo][g]:>8.4f}", end="")
        print()

    # === SPREAD AT EACH CHECKPOINT ===
    print(f"\n{'=' * 90}")
    print("DIVERSITY SPREAD OVER TIME")
    print(f"{'=' * 90}")
    print(f"\n{'Gen':>6} {'Range':>8} {'StdDev':>8} {'Max (topology)':>28} {'Min (topology)':>28}")
    print("-" * 80)
    for g in checkpoints:
        vals = {t: topo_divs[t][g] for t in TOPOLOGIES}
        v_list = list(vals.values())
        rng = max(v_list) - min(v_list)
        sd = std(v_list)
        mx = max(vals, key=vals.get)
        mn = min(vals, key=vals.get)
        print(f"{g:>6} {rng:>8.4f} {sd:>8.4f}   {vals[mx]:.4f} ({mx}){' '*(16-len(mx))}  {vals[mn]:.4f} ({mn})")

    # === TRANSIENT WINDOW (fine-grained) ===
    print(f"\n{'=' * 90}")
    print("TRANSIENT WINDOW: DIVERSITY DROP gen 0 → 20 (predicted window gen 15–25)")
    print(f"{'=' * 90}")
    print(f"\n{'Topology':<18} {'λ₂':>6} {'div@0':>8} {'div@20':>8} {'drop':>8} {'drop%':>8}")
    print("-" * 58)
    for topo in sorted(TOPOLOGIES, key=lambda t: topo_divs[t][0] - topo_divs[t][20], reverse=True):
        l2 = LAMBDA2.get(topo, 0)
        d0 = topo_divs[topo][0]
        d20 = topo_divs[topo][20]
        drop = d0 - d20
        drop_pct = (drop / d0 * 100) if d0 > 0 else 0
        print(f"{topo:<18} {l2:>6.3f} {d0:>8.4f} {d20:>8.4f} {drop:>8.4f} {drop_pct:>7.1f}%")

    # === RANK CORRELATIONS AT MULTIPLE TIMEPOINTS ===
    print(f"\n{'=' * 90}")
    print("SPEARMAN ρ (λ₂ vs diversity) AT EACH CHECKPOINT")
    print("Negative ρ = higher λ₂ → lower diversity (faster mixing → more convergence)")
    print(f"{'=' * 90}")

    topos_by_l2 = sorted(TOPOLOGIES, key=lambda t: LAMBDA2.get(t, 0))

    for g in checkpoints:
        topos_by_div = sorted(TOPOLOGIES, key=lambda t: topo_divs[t][g], reverse=True)
        n = len(TOPOLOGIES)
        ranks_l2 = {t: i for i, t in enumerate(topos_by_l2)}
        ranks_div = {t: i for i, t in enumerate(topos_by_div)}
        d_sq = sum((ranks_l2[t] - ranks_div[t]) ** 2 for t in TOPOLOGIES)
        rho = 1 - 6 * d_sq / (n * (n * n - 1))
        bar = "█" * int(abs(rho) * 30)
        sign = "−" if rho < 0 else "+"
        print(f"  gen {g:>3}: ρ = {rho:>+.3f}  {sign}{bar}")

    # === RANKING TABLE AT GEN 500 ===
    print(f"\n{'=' * 90}")
    print("RANKING: λ₂ vs DIVERSITY at gen 500")
    print(f"{'=' * 90}")

    topos_by_l2 = sorted(TOPOLOGIES, key=lambda t: LAMBDA2.get(t, 0))
    topos_by_div500 = sorted(TOPOLOGIES, key=lambda t: topo_divs[t][500], reverse=True)

    print(f"\n{'Rank':<6} {'By λ₂ (ascending)':>22} {'By diversity@500 (desc)':>28}")
    print("-" * 58)
    for i in range(len(TOPOLOGIES)):
        match = " ✓" if topos_by_l2[i] == topos_by_div500[i] else ""
        print(f"{i+1:<6} {topos_by_l2[i]:>22} {topos_by_div500[i]:>28}{match}")

    # === PER-SEED VARIANCE ===
    print(f"\n{'=' * 90}")
    print("PER-SEED DIVERSITY & FITNESS AT GEN 500")
    print(f"{'=' * 90}")

    print(f"\n{'Topology':<18}", end="")
    for seed in SEEDS:
        print(f" {'d'+str(seed):>8}", end="")
    print(f" {'d_std':>8}", end="")
    for seed in SEEDS:
        print(f" {'f'+str(seed):>8}", end="")
    print(f" {'f_std':>8}")
    print("-" * 100)

    for topo in sorted(TOPOLOGIES, key=lambda t: LAMBDA2.get(t, 0)):
        d_vals = []
        f_vals = []
        print(f"{topo:<18}", end="")
        for seed, rows in data[topo]:
            d = get_value_at_gen(rows, 500, 'diversity')
            d_vals.append(d)
            print(f" {d:>8.4f}", end="")
        print(f" {std(d_vals):>8.4f}", end="")
        for seed, rows in data[topo]:
            f = get_value_at_gen(rows, 500, 'meanFitness')
            f_vals.append(f)
            print(f" {f:>8.4f}", end="")
        print(f" {std(f_vals):>8.4f}")

    # === ANOMALY CHECK ===
    print(f"\n{'=' * 90}")
    print("ANOMALY CHECK: Star & Barbell")
    print(f"{'=' * 90}")

    for g in [20, 50, 100, 500]:
        star_d = topo_divs["star"][g]
        ring_d = topo_divs["ring"][g]
        barbell_d = topo_divs["barbell"][g]
        complete_d = topo_divs["complete"][g]
        disconn_d = topo_divs["disconnected"][g]

        print(f"\n  Gen {g}:")
        print(f"    Disconnected (λ₂=0.00): {disconn_d:.4f}")
        print(f"    Barbell      (λ₂≈0.07): {barbell_d:.4f}")
        print(f"    Ring         (λ₂=0.59): {ring_d:.4f}")
        print(f"    Star         (λ₂=1.00): {star_d:.4f}")
        print(f"    Complete     (λ₂=8.00): {complete_d:.4f}")

        if star_d > ring_d:
            print(f"    → Star > Ring: hub bottleneck REPLICATES")
        else:
            print(f"    → Star < Ring: follows λ₂")

        if barbell_d > ring_d:
            print(f"    → Barbell > Ring: intra-clique effect REPLICATES")
        elif barbell_d < ring_d:
            print(f"    → Barbell < Ring: follows λ₂ prediction")

    # === COMPARISON WITH ONEMAX ===
    print(f"\n{'=' * 90}")
    print("CROSS-DOMAIN COMPARISON")
    print(f"{'=' * 90}")

    print(f"\n{'Metric':<40} {'OneMax':>10} {'Maze(J)':>10} {'Sudoku':>10}")
    print("-" * 72)

    div500_range = max(topo_divs[t][500] for t in TOPOLOGIES) - min(topo_divs[t][500] for t in TOPOLOGIES)
    div500_vals = [topo_divs[t][500] for t in TOPOLOGIES]

    # Spearman at gen 500
    topos_by_div500 = sorted(TOPOLOGIES, key=lambda t: topo_divs[t][500], reverse=True)
    n = len(TOPOLOGIES)
    ranks_l2 = {t: i for i, t in enumerate(topos_by_l2)}
    ranks_div = {t: i for i, t in enumerate(topos_by_div500)}
    d_sq = sum((ranks_l2[t] - ranks_div[t]) ** 2 for t in TOPOLOGIES)
    rho_500 = 1 - 6 * d_sq / (n * (n * n - 1))

    # Spearman at gen 30
    topos_by_div30 = sorted(TOPOLOGIES, key=lambda t: topo_divs[t][30], reverse=True)
    ranks_div30 = {t: i for i, t in enumerate(topos_by_div30)}
    d_sq30 = sum((ranks_l2[t] - ranks_div30[t]) ** 2 for t in TOPOLOGIES)
    rho_30 = 1 - 6 * d_sq30 / (n * (n * n - 1))

    print(f"{'Diversity range @ gen 500':<40} {'0.005':>10} {'0.012':>10} {div500_range:>10.4f}")
    print(f"{'Spearman ρ(λ₂, div) @ gen 30':<40} {'0.88*':>10} {'n/a':>10} {rho_30:>10.3f}")
    print(f"{'Spearman ρ(λ₂, div) @ gen 500':<40} {'~0':>10} {'-0.19':>10} {rho_500:>10.3f}")
    print(f"{'Fitness progress (gen 0→500)':<40} {'0→1.0':>10} {'0.18→0.20':>10} {topo_fits[TOPOLOGIES[0]][0]:>.2f}→{mean([topo_fits[t][500] for t in TOPOLOGIES]):>.2f}".rjust(10))
    print(f"\n* OneMax gen 30 ρ from onemax_transient_10runs study (10 seeds)")

if __name__ == "__main__":
    main()
