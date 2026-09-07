#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
PROJECT="$ROOT/android-lab/spikes/01-rotatable-25d"
OUTPUT="$ROOT/android-lab/build"
mkdir -p "$OUTPUT"
timeout 60s godot --headless --path "$PROJECT" --script res://tests/test_batch.gd -- --lab-unit-tests 2>&1 | tee "$OUTPUT/batch-tests.log"
grep -q 'LAB_BATCH_RESULT:.*failures=0' "$OUTPUT/batch-tests.log"
if grep -E 'SCRIPT ERROR|Parse Error|BATCH_FAIL' "$OUTPUT/batch-tests.log"; then exit 1; fi
timeout 180s xvfb-run -a godot --path "$PROJECT" --rendering-method gl_compatibility --audio-driver Dummy --script res://tests/benchmark_batch.gd -- --lab-unit-tests --batch-dir="$OUTPUT/batch" 2>&1 | tee "$OUTPUT/batch.log"
grep -q LAB_BATCH_RENDER_OK "$OUTPUT/batch.log"
if grep -E 'SCRIPT ERROR|Parse Error|BATCH_FAIL' "$OUTPUT/batch.log"; then exit 1; fi
