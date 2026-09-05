"""Fetch pinned official Godot binaries, verifying the release SHA-512 list."""
from __future__ import annotations
import hashlib
import os
from pathlib import Path
import shutil
import urllib.request
import zipfile

VERSION = "4.5.2"
TAG = f"{VERSION}-stable"
BASE = f"https://github.com/godotengine/godot-builds/releases/download/{TAG}/"
ROOT = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "farmlab-godot"
ROOT.mkdir(parents=True, exist_ok=True)


def fetch(name: str, sums: dict[str, str]) -> Path:
    destination = ROOT / name
    urllib.request.urlretrieve(BASE + name, destination)
    with destination.open("rb") as handle:
        actual = hashlib.file_digest(handle, "sha512").hexdigest()
    if actual.lower() != sums[name].lower():
        raise RuntimeError(f"Checksum mismatch: {name}")
    print(f"SHA512 verified: {name}", flush=True)
    return destination


def main() -> None:
    raw = urllib.request.urlopen(BASE + "SHA512-SUMS.txt", timeout=60).read().decode()
    sums = {}
    for line in raw.splitlines():
        parts = line.split()
        if len(parts) == 2:
            sums[parts[1].lstrip("*")] = parts[0]
    binary_name = f"Godot_v{TAG}_linux.x86_64"
    binary_zip = fetch(binary_name + ".zip", sums)
    with zipfile.ZipFile(binary_zip) as archive:
        with archive.open(binary_name) as source, (ROOT / "godot").open("wb") as target:
            shutil.copyfileobj(source, target)
    (ROOT / "godot").chmod(0o755)
    templates = fetch(f"Godot_v{TAG}_export_templates.tpz", sums)
    output = Path.home() / ".local/share/godot/export_templates" / f"{VERSION}.stable"
    output.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(templates) as archive:
        for name in ("android_debug.apk", "android_release.apk", "version.txt"):
            with archive.open("templates/" + name) as source, (output / name).open("wb") as target:
                shutil.copyfileobj(source, target)
    if "GITHUB_PATH" in os.environ:
        with open(os.environ["GITHUB_PATH"], "a", encoding="utf-8") as handle:
            handle.write(str(ROOT) + "\n")
    print(f"Godot installed: {ROOT / 'godot'}", flush=True)


if __name__ == "__main__":
    main()
