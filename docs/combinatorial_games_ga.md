# Combinatorial Puzzle Games as Genetic Algorithm Domains

This document describes candidate domains for testing the island-model topology experiment
beyond maze generation and checkers. For each domain: the genome encoding, fitness function,
crossover and mutation operators, and notes on GA-friendliness.

---

## 1. N-Queens

**Problem:** Place N queens on an N×N chessboard so that no two queens attack each other
(no shared row, column, or diagonal).

**Genome:** A permutation of [0..N-1] where position i encodes the column of the queen
in row i. By using a permutation, column collisions are structurally impossible — only
diagonal conflicts remain.

```
Genome: [2, 4, 1, 3, 0]  (N=5)
Row 0:  queen in column 2
Row 1:  queen in column 4
Row 2:  queen in column 1
Row 3:  queen in column 3
Row 4:  queen in column 0
```

**Fitness:**
```
f = 1 - (conflicts / max_conflicts)
```
where `conflicts` = number of diagonal attacks (pairs of queens sharing a diagonal),
and `max_conflicts = N*(N-1)/2`. f=1 means a valid solution. N=16 has 2 queens/diagonal
at most; the fitness landscape is a classic combinatorial benchmark.

**Crossover:** Order Crossover (OX) — identical to the maze permutation crossover.

**Mutation:** Random swap of two positions (also identical to maze).

**GA notes:**
- Most GA-friendly domain in this list. The permutation encoding eliminates the
  hardest constraint (non-attacking rows/columns); diagonal-conflict minimization
  is a smooth-ish landscape.
- N=16 has 14,772,512 solutions — very dense solution space, easy for GA.
- N=32 starts to develop meaningful local optima.
- For the topology experiment, N=16 or N=32 recommended. Evaluation is O(N²).
- The plateaus (many genomes with identical conflict count) make it an interesting
  test of *diversity* preservation — do high-connectivity topologies get trapped
  on the same plateau?

**Known results:** 100-genertion GAs reliably solve N-Queens for N ≤ 100.
DIMACS has no standard benchmark (problem is too easy), but the conflict
landscape is well-studied.

---

## 2. Graph Coloring

**Problem:** Color the vertices of a graph G=(V,E) with at most k colors so that no
two adjacent vertices share a color (proper k-coloring).

**Genome:** An integer array of length |V| where each entry is in [0..k-1].

```
Genome: [0, 1, 0, 2, 1, 0]  (|V|=6, k=3)
```

**Fitness:**
```
f = 1 - (edge_conflicts / |E|)
```
where `edge_conflicts` = number of edges where both endpoints have the same color.
f=1 means a valid k-coloring.

**Crossover:** Uniform crossover — for each vertex, independently take the color from
parent 1 with probability 0.5, else parent 2.

*Note on symmetry breaking:* graph coloring has k! symmetries (permutations of color
labels produce equivalent colorings). This creates artificial diversity — two individuals
with identical structure but permuted labels look maximally different. A common fix is
to canonicalize color assignments (always use the lowest-indexed color first seen in
vertex-order scan), but this is optional for the topology experiment.

**Mutation:** For a randomly chosen vertex, assign a random new color from [0..k-1].

**GA notes:**
- Rugged fitness landscape. Many valid colorings exist for sparse graphs but they're
  separated by high-conflict barriers. This stresses topology-mediated diversity more
  than N-Queens.
- **DIMACS benchmark instances** give published results to compare against. Recommended
  instances: DSJC125.5 (125 vertices, density 0.5, chromatic number ≈ 17) and
  queen8_8 (64 vertices, structured, chromatic number = 9).
- The 2025 arXiv paper PEM-Color (parallel island GA for graph coloring) is a direct
  benchmark target.
- Evaluation is O(|E|), fast.
- **Recommended as domain 3** — structured benchmark dataset + direct comparison to
  published island-model results.

---

## 3. Sudoku

**Problem:** Fill a 9×9 grid so each row, column, and 3×3 box contains the digits 1–9 exactly once.
Some cells are pre-filled ("clues").

**Genome (solve mode):** A 9×9 integer array where each row is a permutation of [1..9].
By using per-row permutations, row constraints are automatically satisfied. Column and
box constraints become the fitness objective.

```
Genome (3x3 excerpt):
Row 0: [1,2,3,4,5,6,7,8,9]  (valid row — any permutation works)
Row 1: [4,5,6,7,8,9,1,2,3]
Row 2: [7,8,9,1,2,3,4,5,6]
```

Fixed (clue) cells are clamped throughout crossover and mutation — only unfixed cells evolve.

**Fitness:**
```
f = 1 - (violations / max_violations)
```
where `violations` = sum of duplicate values across all 9 columns + all 9 boxes.
`max_violations = 9*8 + 9*8 = 144` (worst case: all columns and boxes conflict maximally).

**Crossover:** Row-level uniform crossover — independently pick each row's permutation
from parent 1 or parent 2. Clamped cells remain fixed.

**Mutation:** Within a row, swap two non-clamped cells.

**Generate mode:** Fix no cells. GA evolves a "hardest valid Sudoku" using a secondary
metric: the number of cells that must be fixed to yield a unique solution (maximising
this creates puzzles that are harder to solve by humans).

**GA notes:**
- The per-row permutation encoding makes this significantly harder than N-Queens because
  the remaining constraint (columns and boxes) is not decomposable — the landscape is
  strongly epistatic.
- Typical GA: 95–99% of Sudoku instances with ≤ 24 clues solvable; completeness not guaranteed.
- Evaluation O(N²) = O(81), very fast.
- The dual solve/generate mode is interesting: the same GA framework applies to both
  problem variants, testing whether island-model diversity helps escape constraint-satisfaction
  local optima in solve mode and fitness-plateau local optima in generate mode.

---

## 4. Nonogram (Picross)

**Problem:** Fill cells of an N×M grid with black/white so that the run-length
sequence of black cells in each row and column matches given "clue" sequences.

**Genome:** A bitstring of length N×M.

```
Genome (4x4 example, N=M=4):
[1,1,0,0,  0,1,1,0,  0,0,1,1,  1,0,0,1]
→ Grid:
  ##..
  .##.
  ..##
  #..#
```

**Fitness:**
```
f = 1 - (unsatisfied_clues / total_clues)
```
where `unsatisfied_clues` = number of rows/columns whose run-length sequence does not
match the target clue.

**Crossover:** Single-point or two-point bitstring crossover. Row-aware crossover
(cut only at row boundaries) preserves more partial-row solutions.

**Mutation:** Flip a random bit.

**GA notes:**
- NP-complete in general. For N×M grids with dense clues, convergence requires
  many generations and a large population.
- Interesting structure: partial solutions that satisfy all row clues are common
  but satisfying column clues simultaneously is hard — the GA must discover *joint*
  satisfaction. Classic epistasis.
- **Line-solving preprocessing**: standard Nonogram solvers first apply deterministic
  line solvers to fix constrained cells, then use search only on ambiguous cells.
  A hybrid GA could fix deterministic cells and evolve only ambiguous ones, reducing
  genome length.
- Evaluation O(N*M), fast.
- For the topology experiment: use 15×15 Nonograms from Nonogram.com puzzle archives
  (standard difficulty ratings available).

---

## 5. Tetris Weight Evolution (Stochastic Fitness)

**Problem:** Find a weight vector for a Tetris-playing heuristic agent that maximises
mean lines cleared over a fixed number of games.

**Genome:** A float vector [w₁, w₂, ..., wₖ] for heuristic features (k ≈ 10–20).
Typical features: aggregate column height, complete lines, holes, bumpiness.

```
Genome: [-0.51, 0.76, -0.36, -0.18, 0.11, ...]
         (heights, lines, holes, bumpiness, ...)
```

The agent evaluates each candidate move by scoring the resulting board state as
`w · features` and picks the highest-scoring move.

**Fitness:**
```
f = mean_lines_cleared(agent, genome, n_games=20)
```
Stochastic: the same genome yields different fitness values on different evaluations
due to random piece sequences.

**Crossover:** Arithmetic crossover (weighted average of parent weight vectors) or
uniform crossover (independently pick each weight from parent 1 or parent 2).

**Mutation:** Gaussian perturbation of a random weight: wᵢ ← wᵢ + N(0, σ).

**GA notes:**
- **Key novelty as a domain:** fitness is stochastic. Standard GA convergence analysis
  assumes deterministic fitness. Under noise, diversity metrics become meaningless unless
  averaged over multiple evaluations — this is expensive.
- **Interesting research question:** do high-λ₂ topologies help resist genetic drift
  under noisy fitness? Diversity preservation is harder when fitness signals are noisy.
- Well-known baseline: Dellacherie weights ([-0.51, 0.76, -0.36, -0.18, 0.11, ...])
  score ~35 million lines per game — a clear target.
- Evaluation: 20 games × ~200 moves = 4,000 board evaluations per individual per
  generation. Orders of magnitude slower than maze (which is one BFS per individual).
  Only viable if we parallelize within-island evaluation.
- **Recommended use:** save for a dedicated "stochastic fitness" batch after maze and
  checkers validate the pipeline.

---

## Comparison Table

| Domain            | Genome     | Length     | Evaluation  | Landscape  | DIMACS/Benchmark | Stochastic? |
|-------------------|------------|------------|-------------|------------|------------------|-------------|
| Maze generation   | Permutation| ~420       | O(N²)       | Multi-modal| No               | No          |
| N-Queens          | Permutation| N          | O(N²)       | Plateaus   | No               | No          |
| Graph Coloring    | Integer vec| \|V\|      | O(\|E\|)    | Rugged     | DIMACS           | No          |
| Sudoku            | Row-perms  | 81         | O(81)       | Epistatic  | No               | No          |
| Nonogram          | Bitstring  | N×M        | O(N×M)      | Epistatic  | Limited          | No          |
| Tetris weights    | Float vec  | 10–20      | O(n_games)  | Smooth(ish)| Dellacherie      | **Yes**     |

**Recommendation for domain 3:** Graph Coloring.
- DIMACS benchmark instances → direct comparison to published results
- PEM-Color (2025 arXiv) is a direct island-GA benchmark target
- Rugged landscape makes diversity preservation more consequential than in N-Queens
- Fast evaluation, clean encoding

**Recommendation for domain 4 / stress test:** Tetris weights.
- Tests whether topology-mediated diversity helps under stochastic fitness
- Qualitatively different from all other domains

---

*Document written by Claudius. Date: 2026-03-29.*
