extends RefCounted
## Local experiment storage only. Verified temporary writes and one known-good backup.
## Checksums detect accidental corruption, not malicious modification or cheating.
const LabWorld = preload("res://scripts/world.gd")
const MAX_BYTES: int = 65536
var last_error: String = ""
var recovered_from: String = ""

func _valid(payload: Variant) -> bool:
	if not payload is Dictionary:
		return false
	var p: Variant = payload.get("player")
	if not p is Array or p.size() != 2:
		return false
	for coordinate: Variant in p:
		if not (coordinate is int or coordinate is float):
			return false
		if not is_finite(float(coordinate)) or float(coordinate) < 0.0 or float(coordinate) >= LabWorld.SIZE:
			return false
	var rows: Variant = payload.get("markers")
	if not rows is Array or rows.size() > LabWorld.SIZE * LabWorld.SIZE:
		return false
	for row: Variant in rows:
		if not row is Array or row.size() != 2:
			return false
		for coordinate: Variant in row:
			if not (coordinate is int or coordinate is float):
				return false
			if not is_finite(float(coordinate)) or float(coordinate) < 0.0 or float(coordinate) >= LabWorld.SIZE:
				return false
	var candidate = LabWorld.new()
	return candidate.restore(payload)

func _read(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {}
	var file: FileAccess = FileAccess.open(path, FileAccess.READ)
	if file == null:
		return {}
	if file.get_length() > MAX_BYTES:
		file.close()
		return {}
	var text: String = file.get_as_text()
	file.close()
	var parsed: Variant = JSON.parse_string(text)
	if not parsed is Dictionary:
		return {}
	if parsed.get("format", "") == "camera-lab-envelope-v1":
		var body: Variant = parsed.get("payload_json")
		if not body is String or body.sha256_text() != parsed.get("sha256", ""):
			return {}
		parsed = JSON.parse_string(body)
	# Legacy v0.1.0 plain snapshots remain readable, but are not checksummed.
	return parsed if _valid(parsed) else {}

func has_any(path: String) -> bool:
	return FileAccess.file_exists(path) or FileAccess.file_exists(path + ".bak") or FileAccess.file_exists(path + ".tmp")

func save(path: String, world: RefCounted) -> bool:
	last_error = ""
	var payload: Dictionary = world.snapshot()
	if not _valid(payload):
		last_error = "Refused to save an invalid experiment state"
		return false
	var current: Dictionary = _read(path)
	if current == payload:
		return true # Do not rotate an identical checkpoint over the useful backup.
	var body: String = JSON.stringify(payload)
	var envelope: Dictionary = {"format": "camera-lab-envelope-v1", "payload_json": body, "sha256": body.sha256_text()}
	var temporary: String = path + ".tmp"
	var file: FileAccess = FileAccess.open(temporary, FileAccess.WRITE)
	if file == null:
		last_error = "Cannot open temporary save"
		return false
	file.store_string(JSON.stringify(envelope))
	file.flush()
	var write_error: Error = file.get_error()
	file.close()
	if write_error != OK or _read(temporary) != payload:
		last_error = "Temporary save failed verification; previous checkpoint kept"
		return false
	if not current.is_empty():
		var backup_stage: String = path + ".bak.tmp"
		if DirAccess.copy_absolute(path, backup_stage) != OK or _read(backup_stage) != current:
			last_error = "Cannot preserve previous checkpoint"
			return false
		if DirAccess.rename_absolute(backup_stage, path + ".bak") != OK:
			last_error = "Cannot finish backup checkpoint"
			return false
	# Same-directory rename reduces partial-write exposure; it is not a power-loss guarantee.
	if DirAccess.rename_absolute(temporary, path) != OK:
		last_error = "Cannot commit verified save; recovery files retained"
		return false
	return true

func load_into(path: String, world: RefCounted) -> bool:
	recovered_from = ""
	last_error = "No valid checkpoint; current experiment left unchanged"
	for suffix: String in ["", ".bak", ".tmp"]:
		var payload: Dictionary = _read(path + suffix)
		if not payload.is_empty() and world.restore(payload):
			recovered_from = "primary" if suffix == "" else suffix.trim_prefix(".")
			last_error = ""
			return true
	return false
