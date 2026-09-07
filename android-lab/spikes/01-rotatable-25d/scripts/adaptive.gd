extends "res://scripts/runtime.gd"
## v0.3: responsive diagnostic UI, bounded telemetry, connected footprint fixtures.
const LabLayout = preload("res://scripts/lab_layout.gd")
const LabOcclusion = preload("res://scripts/lab_occlusion.gd")
var ui: Dictionary = {}
var safe_override: Rect2 = Rect2()
var applied_safe: Rect2 = Rect2()
var applied_scale: float = 1.0
var safe_poll: float = 0.0
var show_grid: bool = true
var stress_count: int = 0
var stress_time: float = 0.0
var frame_ms: Array[float] = []
var sample_cursor: int = 0
var frame_total: int = 0
var visual_ms: float = 0.0
var faded_count: int = 0
var terrain_cache: Array[PackedVector2Array] = []
var cache_key: Array = []
var cache_rebuilds: int = 0

func _safe_rect() -> Rect2:
	var full: Rect2 = get_viewport_rect()
	if safe_override.has_area():
		return safe_override.intersection(full)
	if OS.get_name() not in ["Android", "iOS"]:
		return full
	var physical: Rect2 = Rect2(DisplayServer.get_display_safe_area())
	var inverse: Transform2D = get_viewport().get_screen_transform().affine_inverse()
	var start: Vector2 = inverse * physical.position
	var end: Vector2 = inverse * physical.end
	var logical: Rect2 = Rect2(start, end - start).intersection(full)
	return logical if logical.has_area() else full

func _touch_scale() -> float:
	if OS.get_name() not in ["Android", "iOS"]:
		return 1.0
	var pixels_per_unit: float = get_viewport().get_screen_transform().get_scale().x
	return clampf(float(DisplayServer.screen_get_dpi()) / 160.0 / maxf(pixels_per_unit, 0.01), 1.0, 1.8)

func _layout() -> void:
	var previous: Vector2 = ui.ground.get_center() if not ui.is_empty() else camera.origin
	last_size = get_viewport_rect().size
	applied_safe = _safe_rect()
	applied_scale = _touch_scale()
	# A portrait compatibility view is supported, but very small windows are not a
	# comfortable play target. Prefer complete controls to silently dropping actions.
	ui = LabLayout.make(last_size, applied_safe, applied_scale)
	buttons = ui.buttons
	camera.origin += ui.ground.get_center() - previous
	if cache_key.is_empty():
		_fit_view()
	_reset_input()

func _fit_view() -> void:
	if ui.is_empty():
		return
	camera.zoom = LabLayout.fit_zoom(ui.ground)
	camera.origin = ui.ground.get_center() + Vector2(0, 28.0 * camera.zoom)

func _action(action: String) -> void:
	if action == "HOME":
		camera.angle = PI / 4.0
		_fit_view()
	elif action == "STRESS":
		stress_count = 128 if stress_count == 0 else (512 if stress_count == 128 else 0)
		frame_ms.clear()
		sample_cursor = 0
		status = "DRAW-ONLY load: %d moving markers | no combat or save changes" % stress_count
	elif action == "GRID":
		show_grid = not show_grid
	else:
		super._action(action)

func _ground_input(position: Vector2) -> bool:
	if ui.is_empty() or not ui.ground.has_point(position):
		return false
	for button: Dictionary in buttons:
		if button.rect.has_point(position):
			return false
	return true

func _pointer_down(id: int, position: Vector2) -> void:
	_pointer_cancel(id)
	for button: Dictionary in buttons:
		if button.rect.has_point(position):
			held[id] = button.action
			_action(button.action)
			return
	if not _ground_input(position):
		return
	fingers[id] = {"position": position, "start": position, "moved": false}
	if fingers.size() > 1:
		multi_gesture = true
		for key: Variant in fingers:
			fingers[key].moved = true

func _process(delta: float) -> void:
	super._process(delta)
	safe_poll += delta
	if safe_poll >= 0.5:
		safe_poll = 0.0
		if _safe_rect() != applied_safe or not is_equal_approx(_touch_scale(), applied_scale):
			_layout()
	if application_active:
		stress_time += minf(delta, 0.05)
		frame_total += 1
		if frame_ms.size() < 600:
			frame_ms.append(delta * 1000.0)
		else:
			frame_ms[sample_cursor] = delta * 1000.0
			sample_cursor = (sample_cursor + 1) % 600

func _terrain() -> void:
	var key: Array = [camera.angle, camera.zoom, camera.origin, camera.focus]
	if key != cache_key:
		terrain_cache.clear()
		for y: int in range(world.SIZE):
			for x: int in range(world.SIZE):
				terrain_cache.append(camera.polygon(Vector2i(x, y)))
		cache_key = key
		cache_rebuilds += 1
	for i: int in range(terrain_cache.size()):
		var polygon: PackedVector2Array = terrain_cache[i]
		var color: Color = Color("28483f") if (i % world.SIZE + i / world.SIZE) % 2 == 0 else Color("2d5146")
		draw_colored_polygon(polygon, color)
		if show_grid:
			draw_polyline(PackedVector2Array([polygon[0], polygon[1], polygon[2], polygon[3], polygon[0]]), Color("436156"), 1.0, true)

func _draw() -> void:
	if ui.is_empty():
		return
	var started: int = Time.get_ticks_usec()
	_terrain()
	if world.in_bounds(selected):
		draw_colored_polygon(camera.polygon(selected), Color(0.8, 0.8, 0.3, 0.35))
	for p: Vector2 in route:
		draw_circle(camera.project(p), 2.0, ACCENT)
	var objects: Array[Dictionary] = []
	for c: Vector2i in world.FIXED:
		objects.append({"p": Vector2(c) + Vector2.ONE * 0.5, "cell": c, "h": 1.45, "kind": 0, "id": objects.size()})
	for c: Vector2i in world.markers:
		objects.append({"p": Vector2(c) + Vector2.ONE * 0.5, "cell": c, "h": 0.65, "kind": 1, "id": objects.size()})
	objects.append({"p": world.player, "kind": 2, "id": objects.size()})
	for i: int in range(stress_count):
		# Uniform deterministic diagnostic samples, not AI agents or pathfinding load.
		var p: Vector2 = Vector2(fposmod(i * 0.6180339 + stress_time * 0.17, 1.0) * 10.0 + 0.5, fposmod(i * 0.4142135 + sin(stress_time * 0.4 + i) * 0.03, 1.0) * 10.0 + 0.5)
		objects.append({"p": p, "kind": 3, "id": objects.size()})
	objects.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		var da: float = camera.depth(a.p)
		var db: float = camera.depth(b.p)
		return a.id < b.id if da == db else da < db)
	faded_count = 0
	for object: Dictionary in objects:
		if object.kind == 2:
			_draw_player()
		elif object.kind == 3:
			draw_circle(camera.project(object.p, 0.1), maxf(2.0, 5.0 * camera.zoom), Color("cf9658"))
		else:
			_draw_block(object.cell, object.h, Color("a9b7ae") if object.kind == 0 else Color("d8ab68"), object.kind == 0)
	draw_arc(camera.project(world.player), maxf(4.0, 12.0 * camera.zoom), 0, TAU, 20, ACCENT, 1.8, true)
	if faded_count > 0:
		# Explicit x-ray location aid, not a physically visible body part.
		draw_arc(camera.project(world.player, 0.62), maxf(4.0, 11.0 * camera.zoom), 0, TAU, 24, ACCENT, 1.5, true)
	_draw_ui()
	visual_ms = float(Time.get_ticks_usec() - started) / 1000.0

func _draw_block(cell: Vector2i, top: float, color: Color, connected: bool) -> void:
	var footprint: Rect2 = Rect2(Vector2(cell), Vector2.ONE)
	if not connected:
		footprint = footprint.grow(-0.07)
	if LabOcclusion.covers_player(world.player, footprint, top, camera.angle):
		color.a = 0.28
		faded_count += 1
	var p: Vector2 = footprint.position
	var corners: Array[Vector2] = [p, p + Vector2(footprint.size.x, 0), footprint.end, p + Vector2(0, footprint.size.y)]
	var low: PackedVector2Array = PackedVector2Array()
	var high: PackedVector2Array = PackedVector2Array()
	for corner: Vector2 in corners:
		low.append(camera.project(corner))
		high.append(camera.project(corner, top))
	var normals: Array[Vector2i] = [Vector2i.UP, Vector2i.RIGHT, Vector2i.DOWN, Vector2i.LEFT]
	var viewer: Vector2 = Vector2(sin(camera.angle), cos(camera.angle))
	for i: int in range(4):
		if Vector2(normals[i]).dot(viewer) <= 0.00001:
			continue
		if connected and cell + normals[i] in world.FIXED:
			continue # Cull interior walls in the L-shaped, multi-cell footprint.
		var j: int = (i + 1) % 4
		var shade: Color = color.darkened(0.22 if i % 2 == 0 else 0.38)
		shade.a = color.a
		draw_colored_polygon(PackedVector2Array([low[i], low[j], high[j], high[i]]), shade)
	draw_colored_polygon(high, color)
	for i: int in range(4):
		if not connected or cell + normals[i] not in world.FIXED:
			draw_line(high[i], high[(i + 1) % 4], Color(0.9, 0.96, 0.92, color.a * 0.5), 1.2, true)

func _line(text: String, at: Vector2, width: float, size: int, color: Color) -> void:
	while text.length() > 1 and ThemeDB.fallback_font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x > width:
		text = text.left(text.length() - 2) + "~"
	_text(text, at, size, color)

func _draw_ui() -> void:
	var safe: Rect2 = ui.safe
	var h: Rect2 = ui.header
	# Fully mask reserved regions: no gameplay clicks can pass through these panels.
	draw_rect(Rect2(0, 0, last_size.x, ui.ground.position.y - 4), Color("0f2428"))
	draw_rect(Rect2(0, ui.toolbar.position.y - 6, last_size.x, last_size.y - ui.toolbar.position.y + 6), Color("0f2428"))
	if safe.position.x > 0:
		draw_rect(Rect2(0, 0, safe.position.x, last_size.y), Color("0a171b"))
	if safe.end.x < last_size.x:
		draw_rect(Rect2(safe.end.x, 0, last_size.x - safe.end.x, last_size.y), Color("0a171b"))
	_line("FARM CAMERA LAB  /  " + str(ProjectSettings.get_setting("application/config/version")), h.position + Vector2(0, 24), h.size.x, 24, ACCENT)
	_line("PRE-JAM TECHNICAL EXERCISE | NOT A COMPETITION BUILD", h.position + Vector2(0, 45), h.size.x, 14, MUTED)
	_line(status, h.position + Vector2(0, 68), h.size.x, 16, INK)
	_line("Yaw %03d | Zoom %.2f | Draw-only %d | Fade %d | FPS %d (not a phone benchmark)" % [int(fposmod(rad_to_deg(camera.angle), 360)), camera.zoom, stress_count, faded_count, Engine.get_frames_per_second()], h.position + Vector2(0, 90), h.size.x, 14, MUTED)
	for button: Dictionary in buttons:
		var active: bool = mode == button.action or _held(button.action) or (button.action == "STRESS" and stress_count > 0) or (button.action == "GRID" and show_grid)
		var rect: Rect2 = button.rect
		draw_rect(rect, Color("326755") if active else Color("1c393e"))
		draw_rect(rect, ACCENT if active else Color("365258"), false, 1.5)
		var text_size: int = 16
		var text: String = button.action
		if text == "STRESS":
			text = "LOAD %d" % stress_count
		var w: float = ThemeDB.fallback_font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, text_size).x
		_text(text, rect.position + Vector2((rect.size.x - w) * 0.5, rect.size.y * 0.5 + 5), text_size)

func metrics() -> Dictionary:
	var samples: Array[float] = frame_ms.duplicate()
	samples.sort()
	var p50: float = samples[samples.size() / 2] if not samples.is_empty() else 0.0
	var p95: float = samples[mini(samples.size() - 1, floori(samples.size() * 0.95))] if not samples.is_empty() else 0.0
	return {"samples": samples.size(), "frame_total": frame_total, "frame_p50_ms": p50, "frame_p95_ms": p95, "draw_cpu_ms": visual_ms, "static_bytes": int(Performance.get_monitor(Performance.MEMORY_STATIC)), "nodes": int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT)), "cache_entries": terrain_cache.size(), "cache_rebuilds": cache_rebuilds, "stress_count": stress_count}

func _write_probe() -> void:
	super._write_probe()
	if not probe_enabled or ui.is_empty():
		return
	var path: String = "user://lab_diagnostics.json"
	var report: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if not report is Dictionary:
		return
	var bounds: Dictionary = {}
	for button: Dictionary in buttons:
		var r: Rect2 = button.rect
		bounds[button.action] = [r.position.x, r.position.y, r.size.x, r.size.y]
	var safe: Rect2 = ui.safe
	report["layout"] = {"safe": [safe.position.x, safe.position.y, safe.size.x, safe.size.y], "rows": ui.rows, "bounds": bounds}
	report["metrics"] = metrics()
	var file: FileAccess = FileAccess.open(path, FileAccess.WRITE)
	if file != null:
		file.store_string(JSON.stringify(report))
		file.close()
