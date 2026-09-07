extends RefCounted
## Pure logical-pixel layout; OS pixels must be transformed by the caller first.
const ACTIONS: Array[String] = ["MOVE", "PLACE", "ERASE", "TURN L", "TURN R", "HOME", "-", "+", "SAVE", "LOAD", "STRESS", "GRID"]

static func make(size: Vector2, safe: Rect2 = Rect2(), touch_scale: float = 1.0) -> Dictionary:
	var full: Rect2 = Rect2(Vector2.ZERO, size)
	if not safe.has_area():
		safe = full
	safe = safe.intersection(full)
	# Caller checks minimum supported logical dimensions before applying extreme insets.
	var cap: float = minf(1.8, minf(maxf(1.0, safe.size.y / 650.0), maxf(1.0, safe.size.x / 850.0)))
	var scale: float = clampf(touch_scale, 1.0, cap)
	var pad: float = 12.0
	var gap: float = 6.0
	var inner: Rect2 = safe.grow(-pad)
	var possible: int = floori((inner.size.x + gap) / (94.0 * scale + gap))
	var columns: int = 12 if possible >= 12 else (6 if possible >= 6 else 4)
	var rows: int = ceili(float(ACTIONS.size()) / float(columns))
	var height: float = 50.0 * scale
	var cell_width: float = (inner.size.x - gap * (columns - 1)) / columns
	var toolbar_height: float = rows * height + (rows - 1) * gap
	var toolbar: Rect2 = Rect2(inner.position.x, inner.end.y - toolbar_height, inner.size.x, toolbar_height)
	var header: Rect2 = Rect2(inner.position, Vector2(inner.size.x, 96.0))
	var ground: Rect2 = Rect2(Vector2(inner.position.x, header.end.y + 8.0), Vector2(inner.size.x, maxf(1.0, toolbar.position.y - header.end.y - 18.0)))
	var controls: Array[Dictionary] = []
	for i: int in range(ACTIONS.size()):
		var col: int = i % columns
		var row: int = i / columns
		controls.append({"action": ACTIONS[i], "rect": Rect2(toolbar.position + Vector2(col * (cell_width + gap), row * (height + gap)), Vector2(cell_width, height))})
	var d: float = 48.0 * scale
	var center: Vector2 = Vector2(ground.position.x + d * 1.5 + 4.0, ground.end.y - d * 1.5 - 4.0)
	for item: Array in [["UP", Vector2.UP], ["LEFT", Vector2.LEFT], ["DOWN", Vector2.DOWN], ["RIGHT", Vector2.RIGHT]]:
		controls.append({"action": item[0], "rect": Rect2(center + item[1] * (d + 2.0) - Vector2.ONE * d * 0.5, Vector2.ONE * d)})
	return {"safe": safe, "header": header, "toolbar": toolbar, "ground": ground, "buttons": controls, "columns": columns, "rows": rows, "scale": scale}

static func fit_zoom(ground: Rect2) -> float:
	# Bounds include a full rotation of an 11x11 floor and the 1.45-high fixtures.
	return clampf(minf((ground.size.x - 32.0) / 1010.0, (ground.size.y - 24.0) / 660.0), 0.22, 1.0)
