{-# LANGUAGE BangPatterns #-}

module Maze
  ( Maze(..)
  , gridSize
  , numEdges
  , decodeMaze
  , bfsShortestPath
  ) where

import Domain
import UnionFind (UF, makeUF, find, union)

import qualified Data.Vector.Unboxed as VU
import qualified Data.Vector.Unboxed.Mutable as VUM
import qualified Data.IntSet as IS
import qualified Data.Sequence as Seq
import System.Random (StdGen, randomR)
import Control.Monad.ST (runST)

-- ---------------------------------------------------------------------------
-- Constants
-- ---------------------------------------------------------------------------

-- | Grid dimension (15x15).
gridSize :: Int
gridSize = 15

-- | Total cells.
numCells :: Int
numCells = gridSize * gridSize  -- 225

-- | Number of horizontal internal edges: 15 rows * 14 gaps = 210.
numHorizontal :: Int
numHorizontal = gridSize * (gridSize - 1)  -- 210

-- | Number of vertical internal edges: 14 gaps * 15 cols = 210.
numVertical :: Int
numVertical = (gridSize - 1) * gridSize  -- 210

-- | Total internal edges.
numEdges :: Int
numEdges = numHorizontal + numVertical  -- 420

-- | Spanning tree needs N^2 - 1 edges.
treeEdges :: Int
treeEdges = numCells - 1  -- 224

-- ---------------------------------------------------------------------------
-- Maze type
-- ---------------------------------------------------------------------------

-- | A maze genome: a permutation of edge indices [0..419].
newtype Maze = Maze { edgePermutation :: VU.Vector Int }

-- ---------------------------------------------------------------------------
-- Edge encoding
-- ---------------------------------------------------------------------------

-- | Decode an edge index into the pair of cells it connects.
--
-- Edges 0..209: horizontal. Edge i connects cell (r, c) to cell (r, c+1)
--   where r = i `div` 14, c = i `mod` 14.
--   Cell indices: r*15+c and r*15+c+1.
--
-- Edges 210..419: vertical. Edge i (offset = i - 210) connects cell (r, c)
--   to cell (r+1, c) where r = offset `div` 15, c = offset `mod` 15.
--   Cell indices: r*15+c and (r+1)*15+c.
edgeCells :: Int -> (Int, Int)
edgeCells !e
  | e < numHorizontal =
      let r = e `div` (gridSize - 1)
          c = e `mod` (gridSize - 1)
      in (r * gridSize + c, r * gridSize + c + 1)
  | otherwise =
      let offset = e - numHorizontal
          r = offset `div` gridSize
          c = offset `mod` gridSize
      in (r * gridSize + c, (r + 1) * gridSize + c)

-- ---------------------------------------------------------------------------
-- Fisher-Yates shuffle (pure, using STVector internally)
-- ---------------------------------------------------------------------------

-- | Fisher-Yates shuffle of [0..n-1].
fisherYates :: Int -> StdGen -> (VU.Vector Int, StdGen)
fisherYates n gen0 = runST $ do
  vec <- VUM.new n
  -- Initialize with [0..n-1]
  let initLoop !i
        | i >= n    = return ()
        | otherwise = VUM.write vec i i >> initLoop (i + 1)
  initLoop 0
  -- Shuffle
  gen' <- shuffleLoop vec (n - 1) gen0
  result <- VU.unsafeFreeze vec
  return (result, gen')
  where
    shuffleLoop _ 0 g = return g
    shuffleLoop vec !i g = do
      let (j, g') = randomR (0, i) g
      -- Swap vec[i] and vec[j]
      vi <- VUM.read vec i
      vj <- VUM.read vec j
      VUM.write vec i vj
      VUM.write vec j vi
      shuffleLoop vec (i - 1) g'

-- ---------------------------------------------------------------------------
-- Kruskal's algorithm: decode permutation -> spanning tree
-- ---------------------------------------------------------------------------

-- | Decode a maze permutation into the set of edge indices forming the
-- spanning tree (perfect maze). Uses Kruskal's with union-find.
decodeMaze :: Maze -> IS.IntSet
decodeMaze (Maze perm) = go 0 (makeUF numCells) IS.empty 0
  where
    go !added !uf !edgeSet !idx
      | added >= treeEdges = edgeSet
      | idx >= VU.length perm = edgeSet  -- shouldn't happen for valid input
      | otherwise =
          let e = perm VU.! idx
              (cellA, cellB) = edgeCells e
              (merged, uf') = union uf cellA cellB
          in if merged
               then go (added + 1) uf' (IS.insert e edgeSet) (idx + 1)
               else go added uf' edgeSet (idx + 1)

-- ---------------------------------------------------------------------------
-- BFS shortest path
-- ---------------------------------------------------------------------------

-- | BFS shortest path from cell 0 (top-left) to cell (numCells-1) (bottom-right)
-- through the spanning tree. Returns the path length (number of edges).
bfsShortestPath :: IS.IntSet -> Int
bfsShortestPath treeEdges' = bfs (Seq.singleton (0, 0)) IS.empty
  where
    target = numCells - 1

    bfs Seq.Empty _ = 0  -- unreachable (shouldn't happen in spanning tree)
    bfs (front Seq.:<| rest) visited
      | fst front == target = snd front
      | IS.member (fst front) visited = bfs rest visited
      | otherwise =
          let cell = fst front
              dist = snd front
              visited' = IS.insert cell visited
              neighbors = cellNeighbors cell treeEdges'
              newEntries = foldr
                (\n acc -> if IS.member n visited' then acc else acc Seq.|> (n, dist + 1))
                rest
                neighbors
          in bfs newEntries visited'

-- | Get the neighbors of a cell in the spanning tree.
-- A cell (r,c) can have up to 4 neighbors:
--   Right: (r, c+1) if horizontal edge (r*14+c) is in tree, and c < 14
--   Left:  (r, c-1) if horizontal edge (r*14+(c-1)) is in tree, and c > 0
--   Down:  (r+1, c) if vertical edge (r*15+c + 210) is in tree, and r < 14
--   Up:    (r-1, c) if vertical edge ((r-1)*15+c + 210) is in tree, and r > 0
cellNeighbors :: Int -> IS.IntSet -> [Int]
cellNeighbors cell treeEdges' =
  let r = cell `div` gridSize
      c = cell `mod` gridSize
      gs = gridSize
      gs1 = gridSize - 1
      right = if c < gs1 && IS.member (r * gs1 + c) treeEdges'
              then [cell + 1] else []
      left  = if c > 0   && IS.member (r * gs1 + (c - 1)) treeEdges'
              then [cell - 1] else []
      down  = if r < gs1 && IS.member (numHorizontal + r * gs + c) treeEdges'
              then [cell + gs] else []
      up    = if r > 0   && IS.member (numHorizontal + (r - 1) * gs + c) treeEdges'
              then [cell - gs] else []
  in right ++ left ++ down ++ up

-- ---------------------------------------------------------------------------
-- Domain instance
-- ---------------------------------------------------------------------------

instance Domain Maze where

  randomIndividual gen =
    let (perm, gen') = fisherYates numEdges gen
    in (Maze perm, gen')

  fitness maze =
    let tree = decodeMaze maze
        pathLen = bfsShortestPath tree
    in fromIntegral pathLen / fromIntegral numCells

  crossover (Maze p1) (Maze p2) gen =
    let len = VU.length p1
        (i, gen1) = randomR (0, len - 2) gen
        (j, gen2) = randomR (i + 1, len - 1) gen1
        child = orderCrossover p1 p2 i j
    in (Maze child, gen2)

  mutate (Maze perm) gen =
    let len = VU.length perm
        (i, gen1) = randomR (0, len - 1) gen
        (j, gen2) = randomR (0, len - 1) gen1
        perm' = swapVec perm i j
    in (Maze perm', gen2)

  distance (Maze p1) (Maze p2) =
    let len = VU.length p1
        diffs = VU.sum $ VU.zipWith (\a b -> if a /= b then (1 :: Int) else 0) p1 p2
    in fromIntegral diffs / fromIntegral len

-- ---------------------------------------------------------------------------
-- Order Crossover (OX)
-- ---------------------------------------------------------------------------

-- | Order crossover: copy segment [i..j] from p1, fill rest from p2 in order.
orderCrossover :: VU.Vector Int -> VU.Vector Int -> Int -> Int -> VU.Vector Int
orderCrossover p1 p2 i j = runST $ do
  let len = VU.length p1
      segLen = j - i + 1

  -- Collect the set of elements in the segment from p1
  let segSet = IS.fromList [p1 VU.! k | k <- [i..j]]

  -- Collect elements from p2 that are NOT in the segment, in p2's order
  -- starting from position (j+1) and wrapping around
  let p2order = [ p2 VU.! ((j + 1 + k) `mod` len) | k <- [0 .. len - 1] ]
      fillElems = filter (\x -> not (IS.member x segSet)) p2order

  -- Build the child
  child <- VUM.new len

  -- Place segment from p1 at positions [i..j]
  let copySegment !k
        | k > j     = return ()
        | otherwise = VUM.write child k (p1 VU.! k) >> copySegment (k + 1)
  copySegment i

  -- Fill remaining positions starting from (j+1) wrapping around
  let fillLoop _ [] = return ()
      fillLoop !pos (e:es)
        | pos >= len - segLen = return ()  -- shouldn't happen
        | otherwise = do
            let actualPos = (j + 1 + pos) `mod` len
            VUM.write child actualPos e
            fillLoop (pos + 1) es
  fillLoop 0 fillElems

  VU.unsafeFreeze child

-- ---------------------------------------------------------------------------
-- Helper
-- ---------------------------------------------------------------------------

-- | Swap two elements in an unboxed vector (pure, O(n) copy).
swapVec :: VU.Vector Int -> Int -> Int -> VU.Vector Int
swapVec v i j
  | i == j    = v
  | otherwise =
      let vi = v VU.! i
          vj = v VU.! j
      in v VU.// [(i, vj), (j, vi)]
