#!/usr/bin/env bash
# Retrain each annotator's ilastik Pixel Classification project on its own labels (headless)
# and export nucleus probability maps for all 53 frames.
# Usage: run_ilastik.sh [project.ilp ...]   (default: projects/*.ilp)
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ILASTIK="$ROOT/tools/ilastik-1.4.2-Linux/run_ilastik.sh"
RAW="$ROOT/data/mitocheck/mitocheck_2d+t/mitocheck_94570_2D+t_01-53.h5/volume/data"
mkdir -p "$ROOT/out/probs"
export LAZYFLOW_THREADS=4 LAZYFLOW_TOTAL_RAM_MB=12000
[ $# -eq 0 ] && set -- "$ROOT"/projects/*.ilp
for ilp in "$@"; do
  name="$(basename "$ilp" .ilp)"
  echo "== $name $(date +%T)"
  "$ILASTIK" --headless --readonly=False --project="$ilp" --retrain \
    --export_source="Probabilities" --output_format=hdf5 \
    --output_filename_format="$ROOT/out/probs/${name}.h5" --output_internal_path=probs \
    "$RAW" 2>&1 | grep -E "Label counts|Traceback|Error" | tail -3
done
echo "all done $(date +%T)"
