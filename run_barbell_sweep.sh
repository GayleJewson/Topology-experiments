#!/bin/bash
# Barbell bridge-width sweep: 6 widths × 3 seeds × 500 gens on Sudoku
# Tests transition from anomalous (b=1) to spectral (b=16=complete)

set -e

SIM=$(cabal list-bin topology-sim 2>/dev/null)
RESULTS_DIR="results/barbell_sweep"
mkdir -p "$RESULTS_DIR"

BRIDGE_WIDTHS="1 2 4 8 12 16"
SEEDS="42 1337 2718"

ISLANDS=8
POP=50
MIG_INTERVAL=10
MIGRANTS=1
GENS=500

echo "Barbell bridge-width sweep on Sudoku"
echo "Bridge widths: $BRIDGE_WIDTHS"
echo ""

PIDS=()
COUNT=0

for b in $BRIDGE_WIDTHS; do
  for seed in $SEEDS; do
    OUTFILE="${RESULTS_DIR}/barbell-${b}_seed${seed}.csv"
    LOGFILE="${RESULTS_DIR}/barbell-${b}_seed${seed}.log"

    echo "Launching: barbell-$b seed=$seed"
    $SIM sudoku barbell-$b $ISLANDS $POP $MIG_INTERVAL $MIGRANTS $GENS $seed +RTS -N1 -RTS \
      > "$OUTFILE" 2> "$LOGFILE" &
    PIDS+=($!)
    COUNT=$((COUNT + 1))
  done
done

echo ""
echo "Launched $COUNT jobs. Waiting..."

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
