#!/bin/bash
# Sudoku experiment: 3 seeds × 8 topologies × 500 generations
# Commit: 79b23a7 (Sudoku domain on main)
# Parameters: 8 islands, pop 50/island, migrate 1 every 10 gens

set -e

SIM=$(cabal list-bin topology-sim 2>/dev/null)
RESULTS_DIR="results/sudoku"
mkdir -p "$RESULTS_DIR"

TOPOLOGIES="disconnected ring star complete hypercube barbell watts-strogatz random-regular"
SEEDS="42 1337 2718"

ISLANDS=8
POP=50
MIG_INTERVAL=10
MIGRANTS=1
GENS=500

echo "Starting Sudoku experiment: 3 seeds × 8 topologies × 500 gens"
echo "Binary: $SIM"
echo "Results: $RESULTS_DIR/"
echo ""

PIDS=()
COUNT=0

for seed in $SEEDS; do
  for topo in $TOPOLOGIES; do
    OUTFILE="${RESULTS_DIR}/${topo}_seed${seed}.csv"
    LOGFILE="${RESULTS_DIR}/${topo}_seed${seed}.log"

    echo "Launching: sudoku topo=$topo seed=$seed -> $OUTFILE"
    $SIM sudoku $topo $ISLANDS $POP $MIG_INTERVAL $MIGRANTS $GENS $seed +RTS -N1 -RTS \
      > "$OUTFILE" 2> "$LOGFILE" &
    PIDS+=($!)
    COUNT=$((COUNT + 1))
  done
done

echo ""
echo "Launched $COUNT jobs. Waiting..."
echo ""

FAILED=0
for pid in "${PIDS[@]}"; do
  if ! wait $pid; then
    FAILED=$((FAILED + 1))
  fi
done

if [ $FAILED -eq 0 ]; then
  echo "All $COUNT runs completed successfully."
else
  echo "WARNING: $FAILED of $COUNT runs failed."
fi

echo ""
echo "Results:"
ls -la "$RESULTS_DIR"/*.csv | wc -l
echo "CSV files generated."
