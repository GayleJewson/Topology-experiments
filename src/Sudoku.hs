{-# LANGUAGE BangPatterns #-}

module Sudoku ( Sudoku(..) ) where

import Domain

import qualified Data.Vector.Unboxed as VU
import System.Random (StdGen, randomR)
import Data.List ((\\))

-- ---------------------------------------------------------------------------
-- Constants
-- ---------------------------------------------------------------------------

gridN :: Int
gridN = 9

-- | Arto Inkala's 2010 "AI Escargot" puzzle (row-major, 0 = empty).
-- 23 givens; unique solution. A well-known hard benchmark.
rawGivens :: VU.Vector Int
rawGivens = VU.fromList
  [ 1,0,0, 0,0,7, 0,9,0
  , 0,3,0, 0,2,0, 0,0,8
  , 0,0,9, 6,0,0, 5,0,0
  , 0,0,5, 3,0,0, 9,0,0
  , 0,1,0, 0,8,0, 0,0,2
  , 6,0,0, 0,0,4, 0,0,0
  , 3,0,0, 0,0,0, 0,1,0
  , 0,4,0, 0,0,0, 0,0,7
  , 0,0,7, 0,0,0, 3,0,0
  ]

-- | For each row: list of column indices that are free (not given).
freeColsPerRow :: [[Int]]
freeColsPerRow =
  [ [c | c <- [0..8], rawGivens VU.! (r * gridN + c) == 0]
  | r <- [0..8]
  ]

-- | For each row: digits that are already given.
givenDigitsPerRow :: [[Int]]
givenDigitsPerRow =
  [ [rawGivens VU.! (r * gridN + c) | c <- [0..8], rawGivens VU.! (r * gridN + c) /= 0]
  | r <- [0..8]
  ]

-- | For each row: digits missing (must be filled in).
missingPerRow :: [[Int]]
missingPerRow = [[1..9] \\ given | given <- givenDigitsPerRow]

-- | Total number of variable cells across all rows.
numVarCells :: Int
numVarCells = sum (map length freeColsPerRow)

-- | Maximum possible violations: 18 groups (9 cols + 9 boxes) × 8 each.
maxViolations :: Double
maxViolations = 18.0 * 8.0

-- ---------------------------------------------------------------------------
-- Sudoku type
-- ---------------------------------------------------------------------------

-- | Genome: 81-element unboxed vector, digits 1-9.
-- Invariant maintained throughout: each row contains each digit 1-9 exactly
-- once. Only column and 3x3 box constraints need to be optimized.
newtype Sudoku = Sudoku { grid :: VU.Vector Int }

-- ---------------------------------------------------------------------------
-- Fitness helpers
-- ---------------------------------------------------------------------------

-- | Number of violations in a group of 9 digits (= 9 - |distinct|).
groupViolations :: [Int] -> Int
groupViolations xs = 9 - length (foldr (\x acc -> if x `elem` acc then acc else x:acc) [] xs)

-- | All values in column c.
colVals :: VU.Vector Int -> Int -> [Int]
colVals g c = [g VU.! (r * gridN + c) | r <- [0..8]]

-- | All values in box (br, bc), where br, bc in {0,1,2}.
boxVals :: VU.Vector Int -> Int -> Int -> [Int]
boxVals g br bc =
  [g VU.! ((br * 3 + r) * gridN + (bc * 3 + c)) | r <- [0..2], c <- [0..2]]

-- | Total violations: sum over columns and boxes (rows are always 0 by invariant).
totalViolations :: VU.Vector Int -> Int
totalViolations g =
  sum [groupViolations (colVals g c) | c <- [0..8]] +
  sum [groupViolations (boxVals g br bc) | br <- [0..2], bc <- [0..2]]

-- ---------------------------------------------------------------------------
-- Fisher-Yates shuffle on short lists (max 9 elements)
-- ---------------------------------------------------------------------------

shuffleList :: [a] -> StdGen -> ([a], StdGen)
shuffleList []  g = ([], g)
shuffleList [x] g = ([x], g)
shuffleList xs  g0 =
  let n = length xs
      (i, g1) = randomR (0, n - 1) g0
      (chosen, rest) = removeAt i xs
      (tl, g2) = shuffleList rest g1
  in (chosen : tl, g2)

removeAt :: Int -> [a] -> (a, [a])
removeAt 0 (x:xs) = (x, xs)
removeAt k (x:xs) = let (e, rest) = removeAt (k - 1) xs in (e, x : rest)
removeAt _ []     = error "removeAt: empty list"

-- ---------------------------------------------------------------------------
-- Grid construction
-- ---------------------------------------------------------------------------

-- | Build a grid where each row is a permutation of 1-9 consistent with
-- the given cells, filling free cells with a random shuffle of the missing digits.
buildGridFromGen :: StdGen -> (VU.Vector Int, StdGen)
buildGridFromGen gen0 =
  let (rowsReversed, genFinal) = foldl fillRow ([], gen0) [0..8]
      allRows = concat (reverse rowsReversed)
  in (VU.fromList allRows, genFinal)
  where
    fillRow :: ([[Int]], StdGen) -> Int -> ([[Int]], StdGen)
    fillRow (acc, g) r =
      let missing  = missingPerRow !! r
          freeCols = freeColsPerRow !! r
          (shuffled, g') = shuffleList missing g
          rowVals = buildRow r freeCols shuffled
      in (rowVals : acc, g')

    buildRow :: Int -> [Int] -> [Int] -> [Int]
    buildRow r freeCols shuffled =
      let freeMap = zip freeCols shuffled
          lookupFree c = case lookup c freeMap of
                           Just d  -> d
                           Nothing -> rawGivens VU.! (r * gridN + c)
      in [lookupFree c | c <- [0..8]]

-- ---------------------------------------------------------------------------
-- Crossover: for each row, randomly choose which parent to take it from
-- ---------------------------------------------------------------------------

rowCrossover :: VU.Vector Int -> VU.Vector Int -> StdGen -> (VU.Vector Int, StdGen)
rowCrossover g1 g2 gen0 =
  let (rowsReversed, genFinal) = foldl pickRow ([], gen0) [0..8]
      allRows = concat (reverse rowsReversed)
  in (VU.fromList allRows, genFinal)
  where
    pickRow :: ([[Int]], StdGen) -> Int -> ([[Int]], StdGen)
    pickRow (acc, g) r =
      let (bit, g') = randomR (0 :: Int, 1) g
          src = if bit == 0 then g1 else g2
          rowVals = [src VU.! (r * gridN + c) | c <- [0..8]]
      in (rowVals : acc, g')

-- ---------------------------------------------------------------------------
-- Domain instance
-- ---------------------------------------------------------------------------

instance Domain Sudoku where

  randomIndividual gen =
    let (g, gen') = buildGridFromGen gen
    in (Sudoku g, gen')

  fitness (Sudoku g) =
    let v = totalViolations g
    in 1.0 - fromIntegral v / maxViolations

  crossover (Sudoku g1) (Sudoku g2) gen =
    let (childGrid, gen') = rowCrossover g1 g2 gen
    in (Sudoku childGrid, gen')

  mutate (Sudoku g) gen =
    let (r, gen1) = randomR (0, 8) gen
        freeCols  = freeColsPerRow !! r
        n         = length freeCols
    in if n < 2
         then (Sudoku g, gen1)
         else
           let (i1, gen2) = randomR (0, n - 1) gen1
               (i2raw, gen3) = randomR (0, n - 2) gen2
               i2  = if i2raw >= i1 then i2raw + 1 else i2raw
               idx1 = r * gridN + (freeCols !! i1)
               idx2 = r * gridN + (freeCols !! i2)
               v1   = g VU.! idx1
               v2   = g VU.! idx2
               g'   = g VU.// [(idx1, v2), (idx2, v1)]
           in (Sudoku g', gen3)

  distance (Sudoku g1) (Sudoku g2) =
    let diffs = length
          [ ()
          | r <- [0..8]
          , c <- freeColsPerRow !! r
          , g1 VU.! (r * gridN + c) /= g2 VU.! (r * gridN + c)
          ]
    in fromIntegral diffs / fromIntegral numVarCells
