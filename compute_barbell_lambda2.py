#!/usr/bin/env python3
"""Compute lambda_2 for parameterized barbell topologies (n=8, bridge width 1..16)."""

import numpy as np
from numpy.linalg import eigvalsh

def barbell_adjacency(n, b):
    """Build adjacency matrix for barbell with b cross-clique edges."""
    half = n // 2
    A = np.zeros((n, n))

    # Intra-clique: fully connected within each half
    for i in range(half):
        for j in range(i+1, half):
            A[i][j] = A[j][i] = 1
    for i in range(half, n):
        for j in range(i+1, n):
            A[i][j] = A[j][i] = 1

    # Cross-clique edges, ordered by Manhattan distance from classic bridge
    all_cross = []
    for d in range(2 * (half - 1) + 1):
        for i in range(half):
            for j in range(half, n):
                if (half - 1 - i) + (j - half) == d:
                    all_cross.append((i, j))

    bridges = all_cross[:min(b, half * half)]
    for (i, j) in bridges:
        A[i][j] = A[j][i] = 1

    return A

def lambda2(A):
    """Algebraic connectivity: second-smallest eigenvalue of the Laplacian."""
    n = A.shape[0]
    D = np.diag(A.sum(axis=1))
    L = D - A
    eigs = eigvalsh(L)
    return eigs[1]

print("Barbell bridge-width sweep: λ₂ for n=8")
print()
print(f"{'Bridge width':>14} {'λ₂':>10} {'Avg degree':>12} {'Cross-edges':>14}")
print("-" * 54)

for b in [1, 2, 4, 8, 12, 16]:
    A = barbell_adjacency(8, b)
    l2 = lambda2(A)
    avg_deg = A.sum() / 8
    print(f"{b:>14} {l2:>10.4f} {avg_deg:>12.2f} {b:>14}")

# Also print the cross-edge ordering for reference
print()
print("Cross-edge priority (Manhattan distance from classic bridge):")
half = 4
for d in range(2 * (half - 1) + 1):
    edges = [(i, j) for i in range(half) for j in range(half, 8)
             if (half - 1 - i) + (j - half) == d]
    print(f"  d={d}: {edges}")
