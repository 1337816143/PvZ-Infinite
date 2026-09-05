#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
PROJECT="$ROOT/android-lab/spikes/01-rotatable-25d"
OUTPUT="$ROOT/android-lab/build"
mkdir -p "$OUTPUT"
godot --headless --path "$PROJECT" --script res://tests/test_hardening.gd -- --lab-unit-tests 2>&1 | tee "$OUTPUT/hardening-tests.log"
grep -q 'LAB_HARDENING_RESULT:.*failures=0' "$OUTPUT/hardening-tests.log"
if grep -E 'SCRIPT ERROR|Parse Error|HARDENING_FAIL' "$OUTPUT/hardening-tests.log"; then exit 1; fi
export GODOT_ANDROID_KEYSTORE_DEBUG_PATH="$RUNNER_TEMP/farmlab-debug.keystore"
export GODOT_ANDROID_KEYSTORE_DEBUG_USER=androiddebugkey
export GODOT_ANDROID_KEYSTORE_DEBUG_PASSWORD=android
godot --headless --path "$PROJECT" --export-debug 'Android Emulator Lab' "$OUTPUT/farmlab-emulator.apk" 2>&1 | tee "$OUTPUT/emulator-export.log"
if grep -E 'SCRIPT ERROR|Parse Error' "$OUTPUT/emulator-export.log"; then exit 1; fi
SDK="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-}}"
"$SDK/build-tools/35.0.0/apksigner" verify --verbose "$OUTPUT/farmlab-emulator.apk" > "$OUTPUT/emulator-signature.txt"
"$SDK/build-tools/35.0.0/aapt" dump permissions "$OUTPUT/farmlab-emulator.apk" > "$OUTPUT/emulator-permissions.txt"
if grep -q android.permission.INTERNET "$OUTPUT/emulator-permissions.txt"; then exit 1; fi
python - "$OUTPUT/farmlab-emulator.apk" <<'PY'
import sys, zipfile
with zipfile.ZipFile(sys.argv[1]) as z:
    assert 'lib/x86_64/libgodot_android.so' in z.namelist()
PY
python "$ROOT/android-lab/ci/emulator_test.py"
