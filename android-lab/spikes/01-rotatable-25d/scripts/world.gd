extends RefCounted
## Small bounded fixture. No combat, economy, networking or production saves.

const SIZE: int = 11
const FIXED: Array[Vector2i] = [Vector2i(4, 4), Vector2i(5, 4), Vector2i(4, 5), Vector2i(7, 7), Vector2i(2, 7)]
const RADIUS: float = 0.18
var player: Vector2 = Vector2(2.5, 2.5)
var markers: Dictionary = {}
var last_error: String = ""

func in_bounds(cell: Vector2i) -> bool:
	return cell.x >= 0 and cell.y >= 0 and cell.x < SIZE and cell.y < SIZE

func blocked(cell: Vector2i) -> bool:
	return not in_bounds(cell) or cell in FIXED or markers.has(cell)

func can_stand(point: Vector2) -> bool:
	for offset: Vector2 in [Vector2(-RADIUS, -RADIUS), Vector2(RADIUS, -RADIUS), Vector2(RADIUS, RADIUS), Vector2(-RADIUS, RADIUS)]:
		var p: Vector2 = point + offset
		if blocked(Vector2i(floori(p.x), floori(p.y))):
			return false
	return true

func place(cell: Vector2i) -> bool:
	if blocked(cell):
		return false
	markers[cell] = true
	if not can_stand(player):
		markers.erase(cell)
		return false
	return true

func erase(cell: Vector2i) -> bool:
	return markers.erase(cell)

func move_by(delta: Vector2) -> void:
	# Axis-separated collision allows sliding, with substeps preventing tunnelling.
	var steps: int = maxi(1, ceili(delta.length() / 0.08))
	var part: Vector2 = delta / float(steps)
	for i in range(steps):
		if can_stand(player + Vector2(part.x, 0.0)):
			player.x += part.x
		if can_stand(player + Vector2(0.0, part.y)):
			player.y += part.y

func path_to(cell: Vector2i) -> PackedVector2Array:
	if blocked(cell):
		return PackedVector2Array()
	var grid: AStarGrid2D = AStarGrid2D.new()
	grid.region = Rect2i(0, 0, SIZE, SIZE)
	grid.cell_size = Vector2.ONE
	grid.offset = Vector2(0.5, 0.5)
	grid.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_NEVER
	grid.update()
	for c: Vector2i in FIXED:
		grid.set_point_solid(c)
	for c: Vector2i in markers:
		grid.set_point_solid(c)
	var start: Vector2i = Vector2i(floori(player.x), floori(player.y))
	return grid.get_point_path(start, cell)

func snapshot() -> Dictionary:
	var cells: Array = []
	for cell: Vector2i in markers:
		cells.append([cell.x, cell.y])
	return {"schema": 1, "purpose": "prejam-camera-lab", "player": [player.x, player.y], "markers": cells}

func _number(value: Variant) -> bool:
	return (value is int or value is float) and is_finite(float(value))

func restore(data: Variant) -> bool:
	last_error = "Invalid or incompatible lab save"
	if not data is Dictionary or data.get("schema", -1) != 1 or data.get("purpose", "") != "prejam-camera-lab":
		return false
	var p: Variant = data.get("player")
	var rows: Variant = data.get("markers")
	if not p is Array or p.size() != 2 or not _number(p[0]) or not _number(p[1]):
		return false
	if not rows is Array or rows.size() > SIZE * SIZE:
		return false
	var incoming: Dictionary = {}
	for row: Variant in rows:
		if not row is Array or row.size() != 2 or not _number(row[0]) or not _number(row[1]):
			return false
		if float(row[0]) != floorf(float(row[0])) or float(row[1]) != floorf(float(row[1])):
			return false
		var cell: Vector2i = Vector2i(int(row[0]), int(row[1]))
		if not in_bounds(cell) or cell in FIXED or incoming.has(cell):
			return false
		incoming[cell] = true
	var old_player: Vector2 = player
	var old_markers: Dictionary = markers
	player = Vector2(float(p[0]), float(p[1]))
	markers = incoming
	if not can_stand(player):
		player = old_player
		markers = old_markers
		return false
	last_error = ""
	return true

func save_to(path: String) -> bool:
	# Notifications also reach base scripts. Every save entry must use the same store.
	# Dynamic load avoids a preload cycle with the store's isolated world validator.
	var storage = load("res://scripts/save_store.gd").new()
	var ok: bool = storage.save(path, self)
	last_error = storage.last_error
	return ok

func load_from(path: String) -> bool:
	var storage = load("res://scripts/save_store.gd").new()
	var ok: bool = storage.load_into(path, self)
	last_error = storage.last_error
	return ok
