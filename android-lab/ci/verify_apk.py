"""Inspect actual APK contents and record reproducible build provenance."""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sys
import zipfile


def main() -> None:
    output = Path(sys.argv[1]).resolve()
    apk = output / "farmlab-debug.apk"
    with zipfile.ZipFile(apk) as archive:
        names = set(archive.namelist())
        for abi in ("armeabi-v7a", "arm64-v8a"):
            if f"lib/{abi}/libgodot_android.so" not in names:
                raise RuntimeError(f"Missing native ABI: {abi}")
    permissions = (output / "permissions.txt").read_text()
    if "android.permission.INTERNET" in permissions:
        raise RuntimeError("Unexpected INTERNET permission")
    badging = (output / "badging.txt").read_text()
    if "io.github.u1337816143.farmlab" not in badging:
        raise RuntimeError("Unexpected application ID")
    with apk.open("rb") as handle:
        digest = hashlib.file_digest(handle, "sha256").hexdigest()
    (output / "SHA256SUMS.txt").write_text(f"{digest}  {apk.name}\n")
    record = {
        "purpose": "pre-jam technical exercise; not a competition submission",
        "commit": os.environ.get("GITHUB_SHA", "local"),
        "run_id": os.environ.get("GITHUB_RUN_ID"),
        "built_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "godot": (output / "godot-version.txt").read_text().strip(),
        "apk_sha256": digest,
        "apk_bytes": apk.stat().st_size,
        "native_abis_verified": ["armeabi-v7a", "arm64-v8a"],
        "internet_permission": False,
        "signature": "ephemeral debug key; not suitable for final store release",
        "android_device_launch": "NOT TESTED",
        "tapplay_launch": "NOT TESTED",
        "tapplay_stability_check": "NOT TESTED",
        "competition_submission": "NOT SUBMITTED",
    }
    (output / "provenance.json").write_text(json.dumps(record, ensure_ascii=False, indent=2))
    root = Path(__file__).resolve().parents[1]
    with zipfile.ZipFile(output / "android-lab-source.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(root.rglob("*")):
            relative = path.relative_to(root)
            if path.is_file() and not any(part in {"build", ".godot", "__pycache__"} for part in relative.parts) and path.suffix not in {".keystore", ".jks"}:
                archive.write(path, Path("android-lab") / relative)
    print("APK_VERIFIED: ARMv7 + ARM64; no INTERNET permission; provenance written")


if __name__ == "__main__":
    main()
