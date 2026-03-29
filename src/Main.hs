module Main where

import IslandGA (Topology, Stats(..), runSimulation)
import Maze (Maze)  -- import Domain instance for Maze
import Domain (Domain(..))

import qualified Data.Vector as V
import Data.Proxy (Proxy(..))
import System.Environment (getArgs)
import System.Random (mkStdGen)
import Data.Bits (xor, testBit, popCount)
import System.IO (hFlush, stdout, hPutStrLn, stderr)

-- ---------------------------------------------------------------------------
-- Topology builders
-- ---------------------------------------------------------------------------

-- | No edges -- fully disconnected islands.
disconnected :: Int -> Topology
disconnected n = V.replicate n []

-- | Ring (cycle): each island connected to its two neighbors.
ring :: Int -> Topology
ring n = V.generate n (\i -> [(i - 1) `mod` n, (i + 1) `mod` n])

-- | Star: island 0 connected to all others, others connected only to 0.
star :: Int -> Topology
star n = V.generate n (\i -> if i == 0
                               then [1 .. n - 1]
                               else [0])

-- | Complete graph: every island connected to every other.
complete :: Int -> Topology
complete n = V.generate n (\i -> [j | j <- [0 .. n - 1], j /= i])

-- | Hypercube of dimension k (n = 2^k nodes).
-- Two nodes are connected iff they differ in exactly one bit.
hypercube :: Int -> Topology
hypercube k =
  let n = 2 ^ k
  in V.generate n (\i -> [j | j <- [0 .. n - 1], popCount (i `xor` j) == 1])

-- | Barbell: two cliques of n/2 connected by a single edge.
-- Nodes 0..half-1 form clique 1, nodes half..n-1 form clique 2.
-- Node (half-1) and node half are the bridge.
barbell :: Int -> Topology
barbell n =
  let half = n `div` 2
  in V.generate n (\i ->
       if i < half
         then
           -- Clique 1: connected to all other clique-1 nodes
           let clique = [j | j <- [0 .. half - 1], j /= i]
           in if i == half - 1
                then half : clique  -- bridge node
                else clique
         else
           -- Clique 2: connected to all other clique-2 nodes
           let clique = [j | j <- [half .. n - 1], j /= i]
           in if i == half
                then (half - 1) : clique  -- bridge node
                else clique
     )

-- | Watts-Strogatz small-world graph.
-- Start with ring lattice of degree k (each node connected to k/2 neighbors
-- on each side), then rewire each edge with probability p.
-- Uses a deterministic seed for reproducibility.
wattsStrogatz :: Int -> Int -> Double -> Int -> Topology
wattsStrogatz n k p seed =
  let -- Start with ring lattice
      halfK = k `div` 2
      ringLattice = V.generate n (\i ->
        [j | d <- [1..halfK], let j = (i + d) `mod` n] ++
        [j | d <- [1..halfK], let j = (i - d) `mod` n])

      -- Rewire edges deterministically using a simple LCG
      -- We only rewire "forward" edges (i -> (i+d) mod n for d in 1..halfK)
      -- to avoid double-rewiring
      rewire :: V.Vector [Int] -> V.Vector [Int]
      rewire adj0 = foldl rewireEdge adj0
        [(i, (i + d) `mod` n) | i <- [0..n-1], d <- [1..halfK]]
        where
          -- Simple deterministic hash for "should we rewire this edge?"
          shouldRewire i j =
            let h = (i * 7919 + j * 6271 + seed * 1031) `mod` 10000
            in fromIntegral h / 10000.0 < p

          rewireEdge :: V.Vector [Int] -> (Int, Int) -> V.Vector [Int]
          rewireEdge adj (i, j)
            | not (shouldRewire i j) = adj
            | otherwise =
                -- Pick a new target for i (deterministic)
                let newJ = ((i * 3571 + j * 2749 + seed * 947) `mod` (n - 1))
                    newJ' = if newJ >= i then newJ + 1 else newJ
                in if newJ' == j || newJ' `elem` (adj V.! i)
                     then adj  -- skip if same or already connected
                     else
                       -- Remove j from i's neighbors, add newJ'
                       let adjI = filter (/= j) (adj V.! i) ++ [newJ']
                           -- Remove i from j's neighbors
                           adjJ = filter (/= i) (adj V.! j)
                           -- Add i to newJ's neighbors
                           adjN = (adj V.! newJ') ++ [i]
                           adj' = adj V.// [(i, adjI), (j, adjJ), (newJ', adjN)]
                       in adj'

  in rewire ringLattice

-- | Random 3-regular graph (deterministic construction).
-- Uses a simple pairing algorithm with a fixed seed.
-- For small n (8, 10, 16, 20), constructs a 3-regular graph.
randomRegular :: Int -> Int -> Int -> Topology
randomRegular n d seed =
  -- Simple construction: start with ring, add d-2 more connections deterministically
  -- For d=3 on n=8: ring gives degree 2, add one more connection per node
  let base = ring n
      -- Add extra edges to reach degree d
      addExtras :: V.Vector [Int] -> V.Vector [Int]
      addExtras adj = foldl tryAddEdge adj [0 .. n - 1]
        where
          tryAddEdge :: V.Vector [Int] -> Int -> V.Vector [Int]
          tryAddEdge adj' i =
            let currentDeg = length (adj' V.! i)
            in if currentDeg >= d
                 then adj'
                 else
                   -- Find a node to connect to
                   let target = ((i * 5021 + seed * 1733) `mod` (n - 2))
                       target' = if target >= i then target + 1 else target
                       -- Ensure target also has room
                       targetDeg = length (adj' V.! target')
                   in if target' `elem` (adj' V.! i) || targetDeg >= d
                        then adj'  -- skip
                        else adj' V.// [ (i, target' : (adj' V.! i))
                                       , (target', i : (adj' V.! target'))
                                       ]
  in addExtras base

-- ---------------------------------------------------------------------------
-- Topology lookup
-- ---------------------------------------------------------------------------

-- | Parse topology name and build the corresponding adjacency list.
buildTopology :: String -> Int -> Topology
buildTopology name n = case name of
  "disconnected"    -> disconnected n
  "ring"            -> ring n
  "star"            -> star n
  "complete"        -> complete n
  "hypercube"       -> hypercube 3  -- k=3 for 8 islands
  "barbell"         -> barbell n
  "watts-strogatz"  -> wattsStrogatz n 4 0.3 42
  "random-regular"  -> randomRegular n 3 42
  _                 -> error $ "Unknown topology: " ++ name

-- ---------------------------------------------------------------------------
-- Main
-- ---------------------------------------------------------------------------

main :: IO ()
main = do
  args <- getArgs
  case args of
    [topoName, nIslandsStr, popSizeStr, migIntervalStr, nMigrantsStr, totalGensStr, seedStr] -> do
      let numIslands   = read nIslandsStr   :: Int
          popSize      = read popSizeStr    :: Int
          migInterval  = read migIntervalStr :: Int
          nMigrants    = read nMigrantsStr  :: Int
          totalGens    = read totalGensStr   :: Int
          seed         = read seedStr        :: Int
          gen          = mkStdGen seed
          topo         = buildTopology topoName numIslands

      hPutStrLn stderr $ "Running: " ++ topoName
                      ++ " | islands=" ++ show numIslands
                      ++ " | pop=" ++ show popSize
                      ++ " | migInterval=" ++ show migInterval
                      ++ " | migrants=" ++ show nMigrants
                      ++ " | gens=" ++ show totalGens
                      ++ " | seed=" ++ show seed

      -- Print CSV header
      putStrLn "generation,meanFitness,bestFitness,diversity"

      -- Run simulation (Maze domain)
      let stats = runSimulation (Proxy :: Proxy Maze) popSize migInterval nMigrants totalGens topo numIslands gen

      -- Print each stats row
      mapM_ (\s -> do
        putStrLn $ show (generation s)
              ++ "," ++ show (meanFitness s)
              ++ "," ++ show (bestFitness s)
              ++ "," ++ show (diversity s)
        hFlush stdout
        ) stats

      hPutStrLn stderr "Done."

    _ -> do
      hPutStrLn stderr "Usage: topology-sim <topology-name> <num-islands> <pop-size> <migration-interval> <num-migrants> <total-generations> <seed>"
      hPutStrLn stderr ""
      hPutStrLn stderr "Topologies: disconnected, ring, star, complete, hypercube, barbell, watts-strogatz, random-regular"
      hPutStrLn stderr ""
      hPutStrLn stderr "Example:"
      hPutStrLn stderr "  topology-sim ring 8 50 10 5 500 42"
