"""
compute_lambda2.py — compute the algebraic connectivity (lambda_2) of the
normalized Laplacian for every topology in topologies.py, then print a
markdown table sorted by lambda_2.

lambda_2 is the second-smallest eigenvalue of L = D - A (unnormalized
Laplacian).  For disconnected graphs lambda_2 = 0.  Higher values indicate
faster mixing / stronger connectivity.
"""

import numpy as np
from scipy.linalg import eigvalsh

from topologies import all_topologies


def laplacian(A):
    """Compute the (unnormalized) Laplacian L = D - A."""
    D = np.diag(A.sum(axis=1))
    return D - A


def lambda2(A):
    """
    Second-smallest eigenvalue of L = D - A.
    Returns 0.0 for trivial (n<=1) or fully disconnected graphs.
    """
    n = A.shape[0]
    if n <= 1:
        return 0.0
    L = laplacian(A)
    eigvals = eigvalsh(L)          # sorted ascending, real (L is symmetric)
    return float(eigvals[1])       # index 0 is always ~0


def avg_degree(A):
    """Mean node degree (number of edges * 2 / n)."""
    degrees = A.sum(axis=1)
    return float(degrees.mean())


def main():
    entries = all_topologies()

    rows = []
    for name, A, notes in entries:
        n = A.shape[0]
        k = avg_degree(A)
        lam2 = lambda2(A)
        rows.append((name, n, k, lam2, notes))

    # Sort by lambda_2 ascending
    rows.sort(key=lambda r: r[3])

    # Print markdown table
    header = "| Topology | n | k (avg degree) | lambda_2 | Notes |"
    sep    = "|----------|---|---------------|---------|-------|"
    print(header)
    print(sep)
    for name, n, k, lam2, notes in rows:
        print(f"| {name} | {n} | {k:.2f} | {lam2:.6f} | {notes} |")

    return rows


if __name__ == "__main__":
    main()
