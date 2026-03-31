# Sudoku as a GA Domain

## Overview

We use Sudoku as a **generation** domain: the GA constructs complete, valid
9×9 Sudoku grids from scratch. We are not solving partially-filled puzzles —
the goal is to evolve an individual that satisfies all Sudoku constraints.

The choice to generate rather than solve matters for topology experiments:
- **Fixed fitness target**: every individual is measured against the same
  standard (zero violations = valid Sudoku)
- **Deceptive landscape**: fixing column violations tends to introduce box
  violations and vice versa — strong local optima requiring correlated moves
  to escape, exactly where island topology effects should be visible
- **Scale control**: one genome encoding, no puzzle-to-puzzle variation

## Genome

**Row-permutation encoding** — one permutation of [1–9] per row.

```
Individual = [[p1,p2,...,p9], [p1,p2,...,p9], ..., [p1,p2,...,p9]]
             ^^^^^^^^^^^Row 0^^^^^^^^^^^      ^^^Row 8^^^
```

- **Length**: 81 genes (9 rows × 9 elements)
- **Row constraint**: satisfied *by construction* — each row is a permutation
  of [1–9], so no repeated digits within any row
- **Remaining constraints**: column and box uniqueness are not guaranteed and
  must be achieved by evolution

## Fitness Function

Minimize violations (0 = valid Sudoku, lower is better):

```python
def fitness(individual):
    grid = individual.reshape(9, 9)
    violations = 0

    # Column violations: count repeated digits in each column
    for col in range(9):
        violations += 9 - len(set(grid[:, col]))

    # Box violations: count repeated digits in each 3x3 box
    for box_row in range(3):
        for box_col in range(3):
            box = grid[box_row*3:(box_row+1)*3, box_col*3:(box_col+1)*3].flatten()
            violations += 9 - len(set(box))

    return violations  # 0 = solved
```

- **Maximum violations**: 144 (64 column + 80 box in worst case)
- **Evaluation cost**: O(1) — fixed 9×9 grid, constant-time constraint checks
- **Row violations**: always 0, not counted (guaranteed by encoding)

## Genetic Operators

### Crossover: Row-level uniform crossover
Each row independently inherited from parent A or parent B with 50% probability.
Maintains the permutation property for every row.

```python
def crossover(parent_a, parent_b):
    child = []
    for row_idx in range(9):
        if random.random() < 0.5:
            child.append(parent_a[row_idx].copy())
        else:
            child.append(parent_b[row_idx].copy())
    return child
```

### Mutation: Row shuffle
Select a random row, shuffle two elements within it (swap-mutation).
Preserves the permutation property.

```python
def mutate(individual, mutation_rate=0.1):
    for row_idx in range(9):
        if random.random() < mutation_rate:
            i, j = random.sample(range(9), 2)
            individual[row_idx][i], individual[row_idx][j] = \
                individual[row_idx][j], individual[row_idx][i]
    return individual
```

## Experimental Predictions

Based on the OneMax transient findings:

- **cycle_rank predicts fitness at gen 15–25**: convergence pressure is higher
  on Sudoku than OneMax (harder constraint satisfaction), so the transient
  window should be earlier and shorter
- **Star anomaly replicates**: Star has cycle_rank=0, forcing all migration
  through the hub regardless of eigenvalue — the bottleneck should be visible
  earlier and more sharply than on OneMax
- **lambda_2 still fails Star**: lambda_2(Star)=1.0 says "well connected";
  cycle_rank=0 says "serial bottleneck" — same structural mismatch as OneMax

If cycle_rank predicts Sudoku performance too, that's three domains — OneMax,
maze (planned), Sudoku — all showing the same structural effect. That's a
claim robust enough to anchor the framework.

## Domain Comparison Table

| Property              | OneMax          | Sudoku (proposed) | Maze (planned) |
|-----------------------|-----------------|-------------------|----------------|
| Genome type           | Binary          | Row permutations  | Path/tree      |
| Genome length         | 100             | 81 (9×9)          | Variable       |
| Fitness landscape     | Unimodal        | Deceptive (rugged)| Single-solution |
| Evaluation cost       | O(n)            | O(1)              | O(n) BFS       |
| Constraint type       | None            | Column+box unique | Solvable maze  |
| Transient window est. | Gen 20–40       | Gen 15–25         | TBD            |

## Status

Proposed domain for the **follow-up paper** after GECCO 2026.
Not included in April 3 GECCO submission — insufficient time to implement,
run, and validate before deadline.

Implementation target: post-GECCO, Batch 2 (alongside tree-phenotype maze).
