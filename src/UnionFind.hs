module UnionFind
  ( UF
  , makeUF
  , find
  , union
  , connected
  ) where

import qualified Data.IntMap.Strict as IM

-- | Immutable Union-Find backed by IntMap.
--
-- Stores parent pointers and ranks. Path compression is applied during 'find',
-- returning an updated structure. This is pure -- no ST or IO needed.
data UF = UF
  { parent :: !(IM.IntMap Int)
  , rank   :: !(IM.IntMap Int)
  } deriving (Show)

-- | Create a Union-Find where each element 0..n-1 is its own root.
makeUF :: Int -> UF
makeUF n = UF
  { parent = IM.fromList [(i, i) | i <- [0 .. n - 1]]
  , rank   = IM.fromList [(i, 0) | i <- [0 .. n - 1]]
  }

-- | Find the root of element x, with path compression.
-- Returns (root, updated UF).
find :: UF -> Int -> (Int, UF)
find uf x =
  let p = parent uf IM.! x
  in if p == x
       then (x, uf)
       else
         let (root, uf') = find uf p
             uf'' = uf' { parent = IM.insert x root (parent uf') }
         in (root, uf'')

-- | Union the sets containing x and y. Returns (True if merged, updated UF).
-- Uses union by rank.
union :: UF -> Int -> Int -> (Bool, UF)
union uf x y =
  let (rx, uf1) = find uf  x
      (ry, uf2) = find uf1 y
  in if rx == ry
       then (False, uf2)
       else
         let rankX = rank uf2 IM.! rx
             rankY = rank uf2 IM.! ry
         in if rankX < rankY
              then (True, uf2 { parent = IM.insert rx ry (parent uf2) })
              else if rankX > rankY
              then (True, uf2 { parent = IM.insert ry rx (parent uf2) })
              else (True, uf2 { parent = IM.insert ry rx (parent uf2)
                              , rank   = IM.insert rx (rankX + 1) (rank uf2) })

-- | Check whether x and y are in the same set.
-- Returns (True if connected, updated UF with path compression).
connected :: UF -> Int -> Int -> (Bool, UF)
connected uf x y =
  let (rx, uf1) = find uf  x
      (ry, uf2) = find uf1 y
  in (rx == ry, uf2)
