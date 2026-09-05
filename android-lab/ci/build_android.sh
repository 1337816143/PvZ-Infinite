#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
PROJECT="$ROOT/android-lab/spikes/01-rotatable-25d"
OUTPUT="$ROOT/android-lab/build"
mkdir -p "$OUTPUT"
SDK="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-}}"
: "${SDK:?Android SDK path required}"
: "${JAVA_HOME:?Java 17 home required}"
sdkmanager --sdk_root="$SDK" 'platform-tools' 'build-tools;35.0.0' 'platforms;android-35'
mkdir -p "$HOME/.config/godot"
cat > "$HOME/.config/godot/editor_settings-4.5.tres" <<EOF
[gd_resource type="EditorSettings" format=3]

[resource]
export/android/java_sdk_path = "$JAVA_HOME"
export/android/android_sdk_path = "$SDK"
EOF
export GODOT_ANDROID_KEYSTORE_DEBUG_PATH="$RUNNER_TEMP/farmlab-debug.keystore"
export GODOT_ANDROID_KEYSTORE_DEBUG_USER=androiddebugkey
export GODOT_ANDROID_KEYSTORE_DEBUG_PASSWORD=android
keytool -genkeypair -keystore "$GODOT_ANDROID_KEYSTORE_DEBUG_PATH" -storepass android -alias androiddebugkey -keypass android -keyalg RSA -keysize 2048 -validity 3650 -dname 'CN=Farm Camera Lab Debug,O=Pre-jam technical exercise,C=CN'
godot --version | tee "$OUTPUT/godot-version.txt"
godot --headless --path "$PROJECT" --editor --import --quit 2>&1 | tee "$OUTPUT/import.log"
if grep -E 'SCRIPT ERROR|Parse Error' "$OUTPUT/import.log"; then exit 1; fi
godot --headless --path "$PROJECT" --script res://tests/test_lab.gd 2>&1 | tee "$OUTPUT/tests.log"
grep -q 'failures=0' "$OUTPUT/tests.log"
xvfb-run -a godot --path "$PROJECT" --rendering-method gl_compatibility --audio-driver Dummy -- --capture-dir="$OUTPUT/screenshots" 2>&1 | tee "$OUTPUT/capture.log"
grep -q LAB_CAPTURE_OK "$OUTPUT/capture.log"
if grep -E 'SCRIPT ERROR|Parse Error' "$OUTPUT/capture.log"; then exit 1; fi
godot --headless --path "$PROJECT" --export-debug 'Android Lab' "$OUTPUT/farmlab-debug.apk" 2>&1 | tee "$OUTPUT/export.log"
if grep -E 'SCRIPT ERROR|Parse Error' "$OUTPUT/export.log"; then exit 1; fi
"$SDK/build-tools/35.0.0/apksigner" verify --verbose "$OUTPUT/farmlab-debug.apk" | tee "$OUTPUT/signature.txt"
"$SDK/build-tools/35.0.0/aapt" dump badging "$OUTPUT/farmlab-debug.apk" > "$OUTPUT/badging.txt"
"$SDK/build-tools/35.0.0/aapt" dump permissions "$OUTPUT/farmlab-debug.apk" > "$OUTPUT/permissions.txt"
python "$ROOT/android-lab/ci/verify_apk.py" "$OUTPUT"
