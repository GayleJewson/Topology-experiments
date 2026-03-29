# Maze Generation as a Genetic Algorithm

## Overview

We use **perfect maze generation** as the first domain for the island-model topology
diversity experiments. Each individual in the GA population represents one maze.
The GA evolves a population of mazes, and we measure how **population diversity**
changes over time under different island migration topologies.

---

## What Is a Perfect Maze?

A perfect maze is a rectangular grid of cells where:
- Every cell is reachable from every other cell
- There is **exactly one path** between any two cells (no loops)

Structurally: a perfect maze is a **spanning tree** of the grid graph.

```
+--+--+--+--+--+
|        |     |
+  +--+  +  +-+
|  |     |  |  |
+  +  +--+  +  +
|     |     |  |
+--+  +  +--+  +
|     |  |     |
+  +--+  +  +--+
|           |  |
+--+--+--+--+--+
```
*A 5×5 perfect maze. Every pair of cells has exactly one path between them.*

The internal structure can be thought of as a graph:

```
Cells (nodes):       Walls (edges that could be removed):

 0  1  2  3  4       —: horizontal passage (between vertically adjacent cells)
 5  6  7  8  9       |: vertical passage (between horizontally adjacent cells)
10 11 12 13 14
15 16 17 18 19
20 21 22 23 24

Removing a horizontal wall between cells i and i+5 creates a N-S passage.
Removing a vertical wall between cells i and i+1 creates an E-W passage.
A perfect maze = a subset of wall removals forming a spanning tree.
```

---

## Genome / Encoding

**Representation:** A permutation of all internal edges of the N×N grid.

For an N×N grid there are:
- N×(N-1) horizontal internal walls (E-W passages)
- (N-1)×N vertical internal walls (N-S passages)
- Total: 2×N×(N-1) = **420 edges** for a 15×15 grid

The genome is a permutation of these 420 edge indices, e.g.:

```
[312, 7, 88, 204, 11, 391, ..., 45]   ← length 420
```

**Decoding (Kruskal's algorithm):**

```
Initialize: every cell is its own component (union-find structure)
For edge in genome_permutation:
    cell_a, cell_b = endpoints(edge)
    if find(cell_a) ≠ find(cell_b):   # not yet connected
        remove the wall (add edge to maze)
        union(cell_a, cell_b)
    if |edges_added| == N²-1:
        break                          # spanning tree is complete
```

This always produces a valid perfect maze. **No repair step is ever needed.**

```
Example (4×4, edges shown as e0..e23):

  e0  e1  e2        (horizontal edges, row 0)
 e3  e4  e5  e6     (vertical edges, col 0-3)
  e7  e8  e9       (horizontal edges, row 1)
e10 e11 e12 e13
  ...

Genome [e5, e0, e12, e3, ...] means:
  → Try e5 first: connects (0,1)-(0,2), not same component → ADD
  → Try e0: connects (0,0)-(0,1), not same component → ADD
  → Try e12: etc.
```

---

## What Are We Optimizing?

**Fitness function:** A composite of three maze quality metrics.

```
f(maze) = 0.5 * path_length/N²  +  0.3 * dead_end_density  +  0.2 * junction_density
```

Where:
- `path_length` = BFS distance from (0,0) to (N-1,N-1)
- `dead_end_density` = fraction of cells with degree 1 (one passage, no branches)
- `junction_density` = fraction of cells with degree ≥ 3 (branching points)

**Higher fitness = more complex, harder maze.**

**Why the composite?**

Pure path-length fitness has a degenerate optimum: the fitness-maximising maze is a
single space-filling Hamiltonian path from start to finish — one long winding corridor
with no branches at all. A human solver would find it trivially easy once they realise
there are no dead ends.

A proper maze needs all three components:

| Component | What it captures | Without it |
|-----------|------------------|------------|
| Path length | Solution is long/winding | Short, direct path wins |
| Dead-end density | Many false branches to explore | Single-corridor degeneracy |
| Junction density | Complex decision points | Linear chains dominate |

In a spanning tree on N² nodes, the three components are related but not redundant:
a maze can have a long solution path while having very few junctions (e.g., a spiral).
Adding junction weight prevents the spiral/space-fill degenerate case.

**Computing the components:**

```
path_length  = BFS distance (0,0) → (N-1,N-1)     [O(N²)]
dead_ends    = count of cells with degree 1         [O(N²)]
junctions    = count of cells with degree ≥ 3       [O(N²)]

dead_end_density  = dead_ends  / N²
junction_density  = junctions  / N²
```

Cell degree = number of passages (removed walls) connecting it to neighbours.

```
Low-fitness maze:               High-fitness maze:

+--+--+--+--+                   +--+--+--+--+
|S           |                  |S  |        |
+  +--+--+   +                  +  +  +--+  +
|  |         |                  |     |  |  |
+  +  +--+--+                   +--+--+  +  +
|     |      |                  |        |  |
+--+  +  +--+                   +  +--+--+  +
|         |G |                  |  |      G |
+--+--+--+--+                   +--+--+--+--+

Few dead ends, few junctions     Many dead ends, many junctions
→ low dead_end + junction score  → high composite score
```

**Why these weights (0.5 / 0.3 / 0.2)?**

Path length is the most direct measure of difficulty. Dead-end density is the
primary guard against the degenerate single-corridor case. Junction density is a
secondary guard. Equal weighting would over-reward mazes with many tiny dead-end
stubs at the cost of solution length. These weights can be tuned if early results
suggest the degenerate case persists.

**Haskell implementation note for Lyra:**

```haskell
fitness :: Maze -> Double
fitness (Maze perm) =
  let tree   = kruskalDecode perm
      path   = fromIntegral (bfsLength tree) / fromIntegral (n*n)
      degs   = V.map (degree tree) (V.fromList [0..n*n-1])
      deadEnds   = fromIntegral (V.length (V.filter (== 1) degs)) / fromIntegral (n*n)
      junctions  = fromIntegral (V.length (V.filter (>= 3) degs)) / fromIntegral (n*n)
  in  0.5 * path + 0.3 * deadEnds + 0.2 * junctions
```

**Evaluation cost:** still O(N²) — one BFS pass + one degree scan. Negligible.

**Why this fitness function?**
- Guards against the degenerate single-corridor optimum
- All three components have many local optima — good test for diversity preservation
- Evaluation remains fast; the simulation cost is still dominated by generation count

---

## Crossover

**Operator:** Order Crossover (OX) on permutations

```
Parent 1:  [3, 7, 1, 4, 8, 2, 9, 5, 6, 0]
Parent 2:  [9, 3, 7, 8, 2, 6, 0, 1, 5, 4]
                    ^--------^
                  cut points at 2 and 5

Step 1: Copy segment from P1 into offspring:
Offspring: [_, _, 1, 4, 8, _, _, _, _, _]

Step 2: Scan P2 from position 5, skipping 1, 4, 8 (already present):
P2 scan:   [9, 3, 7, 8*, 2, 6, 0, 1*, 5, 4*]
                         skip    keep skip keep skip

Offspring: [2, 6, 1, 4, 8, 0, 9, 3, 5, 7]
```

The offspring always contains each edge exactly once — guaranteed valid permutation,
guaranteed valid maze after Kruskal decoding.

---

## Mutation

**Operator:** Random swap — choose two random positions and exchange them

```
Before: [..., 88, ..., 204, ...]
                ↕
After:  [..., 204, ..., 88, ...]
```

Mutation rate: 1/L per gene position per individual (expected one swap per chromosome).
Probability chosen so mutation explores without destroying all structure inherited via crossover.

---

## Example Evolution Trace (schematic)

```
Generation 0 (random):         Generation 500 (evolved):

Individual 1: f = 0.31         Individual 1: f = 0.71
Individual 2: f = 0.28         Individual 2: f = 0.68
Individual 3: f = 0.35         Individual 3: f = 0.70
...                            ...
Mean fitness:  0.30            Mean fitness:  0.67
Diversity:     0.91            Diversity:     0.43
```

The GA improves mean fitness while diversity decreases. The rate of diversity loss
depends on the island migration topology — the central question of our experiment.

---

## Why Maze Is a Good Test Domain

1. **Evaluation is trivial** — BFS on 225 cells takes microseconds; the entire
   simulation is dominated by evolutionary operators, not fitness evaluation.

2. **Rich landscape** — the space of 15×15 spanning trees is astronomical
   (approximately 10^{300}). The fitness landscape has many local optima.

3. **Diversity naturally arises** — structurally very different mazes can have
   similar fitness values, so topology-induced isolation should produce qualitatively
   different solution styles across islands.

4. **Clean validation** — we can visually inspect evolved mazes to sanity-check
   that evolution is working, and confirm that high-fitness mazes genuinely look harder.

5. **Natural bridge to checkers** — maze-solving can be treated as a navigation
   problem, with an agent traversing the maze. This conceptual link to game-playing
   agents (checkers) makes the domain sequence coherent.

---

## Implementation Notes for Lyra

The maze domain should expose a Haskell type class conforming to the Kleisli pipeline
interface. The key functions needed:

```haskell
class Domain a where
  -- Generate a random individual
  randomIndividual :: RandomGen g => g -> (a, g)

  -- Compute fitness (higher is better)
  fitness :: a -> Double

  -- Crossover two parents to produce an offspring
  crossover :: RandomGen g => a -> a -> g -> (a, g)

  -- Mutate an individual
  mutate :: RandomGen g => a -> g -> (a, g)
```

The `Maze` type wraps a permutation of edge indices:

```haskell
newtype Maze = Maze { edgePermutation :: V.Vector Int }

instance Domain Maze where
  randomIndividual = ...  -- random permutation of [0..419]
  fitness (Maze perm) = fromIntegral (bfsLength (kruskalDecode perm)) / 225.0
  crossover = orderCrossover
  mutate = randomSwapMutation
```

The Kleisli pipeline (island selection, migration, generation loop) never needs to
know about `Maze` specifically — it works through the `Domain` type class.

Topologies live in a separate module and are passed to the pipeline as adjacency lists.
Switching to checkers means implementing `instance Domain CheckersBoard` without
touching the pipeline at all.

---

## File Organization

```
Topology-experiments/
├── DESIGN_DECISIONS.md     ← this document's decisions
├── docs/
│   └── maze_ga.md          ← this document
├── topologies/
│   └── topology_zoo.py     ← spectral analysis (Python)
├── src/
│   ├── Domain.hs           ← Domain type class
│   ├── Maze.hs             ← Maze instance
│   ├── IslandGA.hs         ← Kleisli pipeline (topology-agnostic)
│   └── Main.hs             ← experiment runner
└── results/
    └── (simulation outputs go here)
```
