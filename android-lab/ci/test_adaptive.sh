#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
PROJECT="$ROOT/android-lab/spikes/01-rotatable-25d"
OUTPUT="$ROOT/android-lab/build"
mkdir -p "$OUTPUT"
timeout 60s godot --headless --path "$PROJECT" --script res://tests/test_adaptive.gd -- --lab-unit-tests 2>&1 | tee "$OUTPUT/adaptive-tests.log"
grep -q 'LAB_ADAPTIVE_RESULT:.*failures=0' "$OUTPUT/adaptive-tests.log"
if grep -E 'SCRIPT ERROR|Parse Error|ADAPTIVE_FAIL' "$OUTPUT/adaptive-tests.log"; then exit 1; fi
timeout 120s xvfb-run -a -s '-screen 0 1920x1440x24' godot --path "$PROJECT" --rendering-method gl_compatibility --audio-driver Dummy --script res://tests/render_matrix.gd -- --lab-unit-tests --matrix-dir="$OUTPUT/matrix" 2>&1 | tee "$OUTPUT/matrix.log"
grep -q LAB_RENDER_MATRIX_OK "$OUTPUT/matrix.log"
if grep -E 'SCRIPT ERROR|Parse Error|MATRIX_FAIL' "$OUTPUT/matrix.log"; then exit 1; fi

bash "$ROOT/android-lab/ci/test_batch.sh"
