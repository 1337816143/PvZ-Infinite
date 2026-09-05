extends Node2D
## Procedural diagnostic view. Every visible shape is drawn here; no game assets.

const Projection = preload("res://scripts/projection.gd")
const World = preload("res://scripts/world.gd")
const SAVE_PATH: String = "user://camera_lab_v1.json"
const INK: Color = Color("dcebe7")
const MUTED: Color = Color("8da8a5")
const ACCENT: Color = Color("8ed8b3")
var camera = Projection.new()
var world = World.new()
var mode: String = "MOVE"
var status: String = "PRE-JAM TECHNICAL EXERCISE | No final game content"
var selected: Vector2i = Vector2i(-1, -1)
var route: PackedVector2Array = PackedVector2Array()
var buttons: Array[Dictionary] = []
var held: Dictionary = {}
var fingers: Dictionary = {}
var multi_gesture: bool = false
var right_drag: bool = false
var last_size: Vector2 = Vector2.ZERO
var capture_running: bool = false

func _ready() -> void:
	Engine.max_fps = 60
	_layout()
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--capture-dir="):
			capture_running = true
			_capture.call_deferred(arg.trim_prefix("--capture-dir="))

func _layout() -> void:
	var size: Vector2 = get_viewport_rect().size
	camera.origin += Vector2(size.x * 0.5, size.y * 0.52) - (Vector2(last_size.x * 0.5, last_size.y * 0.52) if last_size != Vector2.ZERO else camera.origin)
	last_size = size
	buttons.clear()
	var actions: Array[String] = ["MOVE", "PLACE", "ERASE", "TURN L", "TURN R", "HOME", "-", "+", "SAVE", "LOAD"]
	var width: float = (size.x - 48.0) / float(actions.size())
	for i in range(actions.size()):
		buttons.append({"action": actions[i], "rect": Rect2(24.0 + i * width, size.y - 79.0, width - 8.0, 53.0)})
	var center: Vector2 = Vector2(90.0, size.y - 198.0)
	for item: Array in [["UP", Vector2(0, -1)], ["LEFT", Vector2(-1, 0)], ["DOWN", Vector2(0, 1)], ["RIGHT", Vector2(1, 0)]]:
		buttons.append({"action": item[0], "rect": Rect2(center + item[1] * 50.0 - Vector2(24, 24), Vector2(48, 48))})

func _process(delta: float) -> void:
	if get_viewport_rect().size != last_size:
		_layout()
	var dt: float = minf(delta, 0.05)
	var direction: Vector2 = Vector2.ZERO
	if Input.is_physical_key_pressed(KEY_W) or _held("UP"):
		direction.y -= 1.0
	if Input.is_physical_key_pressed(KEY_S) or _held("DOWN"):
		direction.y += 1.0
	if Input.is_physical_key_pressed(KEY_A) or _held("LEFT"):
		direction.x -= 1.0
	if Input.is_physical_key_pressed(KEY_D) or _held("RIGHT"):
		direction.x += 1.0
	var turning: float = 0.0
	if Input.is_physical_key_pressed(KEY_Q) or _held("TURN L"):
		turning -= 1.0
	if Input.is_physical_key_pressed(KEY_E) or _held("TURN R"):
		turning += 1.0
	camera.angle = wrapf(camera.angle + turning * dt * 1.2, -PI, PI)
	if not direction.is_zero_approx():
		route.clear()
		world.move_by(camera.screen_direction(direction) * dt * 2.8)
	elif not route.is_empty():
		var vector: Vector2 = route[0] - world.player
		if vector.length() < 0.04:
			route.remove_at(0)
		else:
			world.move_by(vector.limit_length(dt * 2.8))
	queue_redraw()

func _held(action: String) -> bool:
	return action in held.values()

func _input(event: InputEvent) -> void:
	if capture_running:
		return
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_HOME:
			_action("HOME")
		elif event.keycode == KEY_ESCAPE:
			held.clear()
			fingers.clear()
			multi_gesture = false
			route.clear()
	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_LEFT:
			if event.pressed:
				_pointer_down(100, event.position)
			else:
				_pointer_up(100, event.position)
		elif event.button_index == MOUSE_BUTTON_RIGHT:
			right_drag = event.pressed
		elif event.pressed and event.button_index == MOUSE_BUTTON_WHEEL_UP:
			camera.transform_at(event.position, 0.0, 1.1)
		elif event.pressed and event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			camera.transform_at(event.position, 0.0, 1.0 / 1.1)
	elif event is InputEventMouseMotion:
		if right_drag:
			camera.angle = wrapf(camera.angle + event.relative.x * 0.008, -PI, PI)
		_pointer_move(100, event.position)
	elif event is InputEventScreenTouch:
		if event.pressed:
			_pointer_down(event.index, event.position)
		else:
			_pointer_up(event.index, event.position)
	elif event is InputEventScreenDrag:
		_pointer_move(event.index, event.position)

func _pointer_down(id: int, position: Vector2) -> void:
	for button: Dictionary in buttons:
		if button.rect.has_point(position):
			held[id] = button.action
			_action(button.action)
			return
	if position.y < 114.0 or position.y > last_size.y - 94.0:
		return
	fingers[id] = {"position": position, "start": position, "moved": false}
	if fingers.size() > 1:
		multi_gesture = true
		for key: Variant in fingers:
			fingers[key].moved = true

func _pointer_move(id: int, position: Vector2) -> void:
	if not fingers.has(id):
		return
	var old: Vector2 = fingers[id].position
	var ids: Array = fingers.keys()
	ids.sort()
	if ids.size() >= 2:
		var a: Vector2 = fingers[ids[0]].position
		var b: Vector2 = fingers[ids[1]].position
		fingers[id].position = position
		var new_a: Vector2 = fingers[ids[0]].position
		var new_b: Vector2 = fingers[ids[1]].position
		var before: Vector2 = b - a
		var after: Vector2 = new_b - new_a
		if before.length() > 12.0 and after.length() > 12.0:
			camera.transform_at((a + b) * 0.5, wrapf(after.angle() - before.angle(), -PI, PI), after.length() / before.length(), (new_a + new_b - a - b) * 0.5)
	else:
		fingers[id].position = position
		if position.distance_to(fingers[id].start) > 12.0:
			fingers[id].moved = true
		if fingers[id].moved:
			camera.origin += position - old

func _pointer_up(id: int, position: Vector2) -> void:
	held.erase(id)
	if fingers.has(id):
		if not fingers[id].moved and not multi_gesture:
			_tap(position)
		fingers.erase(id)
	if fingers.is_empty():
		multi_gesture = false

func _action(action: String) -> void:
	if action in ["MOVE", "PLACE", "ERASE"]:
		mode = action
		status = "Mode: " + action + " | Tap a ground tile"
	elif action == "HOME":
		camera.angle = PI / 4.0
		camera.zoom = 1.0
		camera.origin = Vector2(last_size.x * 0.5, last_size.y * 0.52)
	elif action == "+" or action == "-":
		camera.transform_at(Vector2(last_size.x * 0.5, last_size.y * 0.52), 0.0, 1.15 if action == "+" else 1.0 / 1.15)
	elif action == "SAVE":
		status = "Lab state saved locally" if world.save_to(SAVE_PATH) else world.last_error
	elif action == "LOAD":
		route.clear()
		status = "Lab state restored" if world.load_from(SAVE_PATH) else world.last_error

func _tap(position: Vector2) -> void:
	selected = camera.cell_at(position)
	if not world.in_bounds(selected):
		status = "Outside the 11 x 11 diagnostic grid"
		return
	if mode == "PLACE":
		route.clear()
		status = "Test column placed" if world.place(selected) else "Blocked tile or player overlap: placement refused"
	elif mode == "ERASE":
		route.clear()
		status = "Test column removed" if world.erase(selected) else "Only user-placed columns can be removed"
	else:
		route = world.path_to(selected)
		status = "Walking on world coordinates" if not route.is_empty() else "No walkable route"

func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_PAUSED or what == NOTIFICATION_APPLICATION_FOCUS_OUT:
		held.clear()
		fingers.clear()
		multi_gesture = false
		right_drag = false
		if is_inside_tree() and not capture_running:
			world.save_to(SAVE_PATH)

func _text(value: String, at: Vector2, size: int = 18, color: Color = INK) -> void:
	draw_string(ThemeDB.fallback_font, at, value, HORIZONTAL_ALIGNMENT_LEFT, -1.0, size, color)

func _draw() -> void:
	var unit: float = camera.SCALE * camera.zoom
	for y in range(world.SIZE):
		for x in range(world.SIZE):
			var cell: Vector2i = Vector2i(x, y)
			var polygon: PackedVector2Array = camera.polygon(cell)
			var color: Color = Color("28483f") if (x + y) % 2 == 0 else Color("2d5146")
			draw_colored_polygon(polygon, color)
			draw_polyline(PackedVector2Array([polygon[0], polygon[1], polygon[2], polygon[3], polygon[0]]), Color("436156"), 1.0, true)
	if world.in_bounds(selected):
		draw_colored_polygon(camera.polygon(selected), Color(0.8, 0.8, 0.3, 0.35))
	for point: Vector2 in route:
		draw_circle(camera.project(point), 3.0 * camera.zoom, ACCENT)
	var objects: Array[Dictionary] = []
	for cell: Vector2i in world.FIXED:
		objects.append({"position": Vector2(cell) + Vector2(0.5, 0.5), "height": 1.45, "color": Color("a9b7ae"), "player": false})
	for cell: Vector2i in world.markers:
		objects.append({"position": Vector2(cell) + Vector2(0.5, 0.5), "height": 0.65, "color": Color("d8ab68"), "player": false})
	objects.append({"position": world.player, "height": 0.0, "color": ACCENT, "player": true})
	objects.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return camera.depth(a.position) < camera.depth(b.position))
	for object: Dictionary in objects:
		var p: Vector2 = camera.project(object.position)
		draw_set_transform(p, 0.0, Vector2(1.0, camera.SQUASH))
		draw_circle(Vector2.ZERO, unit * 0.35, Color(0.01, 0.02, 0.02, 0.22))
		draw_set_transform(Vector2.ZERO)
	for object: Dictionary in objects:
		if object.player:
			_draw_player()
		else:
			_draw_column(object.position, object.height, object.color)
	# A small foot ring preserves location readability when geometry covers the marker.
	draw_arc(camera.project(world.player), unit * 0.2, 0, TAU, 24, ACCENT, 2.0, true)
	for label: Array in [["N", Vector2(5.5, -0.45)], ["E", Vector2(11.45, 5.5)], ["S", Vector2(5.5, 11.45)], ["W", Vector2(-0.45, 5.5)]]:
		_text(label[0], camera.project(label[1]), 20, ACCENT)
	_draw_ui()

func _draw_column(center: Vector2, height: float, base: Color) -> void:
	var corners: Array[Vector2] = [center + Vector2(-0.43, -0.43), center + Vector2(0.43, -0.43), center + Vector2(0.43, 0.43), center + Vector2(-0.43, 0.43)]
	var low: PackedVector2Array = PackedVector2Array()
	var high: PackedVector2Array = PackedVector2Array()
	for point: Vector2 in corners:
		low.append(camera.project(point))
		high.append(camera.project(point, height))
	var hull: PackedVector2Array = Geometry2D.convex_hull(low + high)
	if camera.depth(world.player) < camera.depth(center) + 0.6 and Geometry2D.is_point_in_polygon(camera.project(world.player, 0.45), hull):
		base.a = 0.35
	var normals: Array[Vector2] = [Vector2.UP, Vector2.RIGHT, Vector2.DOWN, Vector2.LEFT]
	var viewer: Vector2 = Vector2(sin(camera.angle), cos(camera.angle))
	for i in range(4):
		if normals[i].dot(viewer) > 0.0:
			var j: int = (i + 1) % 4
			var shade: Color = base.darkened(0.22 if i % 2 == 0 else 0.38)
			shade.a = base.a
			draw_colored_polygon(PackedVector2Array([low[i], low[j], high[j], high[i]]), shade)
	draw_colored_polygon(high, base)
	draw_polyline(PackedVector2Array([high[0], high[1], high[2], high[3], high[0]]), Color(0.9, 0.96, 0.92, base.a * 0.45), 1.5, true)

func _draw_player() -> void:
	var scale: float = camera.zoom
	var foot: Vector2 = camera.project(world.player)
	var chest: Vector2 = camera.project(world.player, 0.34)
	var head: Vector2 = camera.project(world.player, 0.62)
	draw_line(foot, chest, ACCENT.darkened(0.3), 13.0 * scale, true)
	draw_circle(chest, 9.0 * scale, ACCENT)
	draw_circle(head, 10.0 * scale, Color("edf0cc"))
	draw_circle(head + Vector2(3, -2) * scale, 3.0 * scale, Color("607c78"))

func _draw_ui() -> void:
	draw_rect(Rect2(0, 0, last_size.x, 114), Color("0f2428"))
	draw_rect(Rect2(0, last_size.y - 96, last_size.x, 96), Color("0f2428"))
	_text("FARM : INFINITE  /  CAMERA LAB", Vector2(25, 35), 25, ACCENT)
	_text("PRE-JAM TECHNICAL EXERCISE  |  v0.1.0  |  NOT A COMPETITION BUILD", Vector2(25, 62), 16, MUTED)
	_text(status, Vector2(25, 94), 18)
	_text("Yaw %03d   Zoom %.2f   FPS %d" % [int(fposmod(rad_to_deg(camera.angle), 360.0)), camera.zoom, Engine.get_frames_per_second()], Vector2(last_size.x - 345, 34), 18, ACCENT)
	_text("Cell %s   Objects %d" % [str(selected), world.markers.size() + world.FIXED.size()], Vector2(last_size.x - 345, 61), 17, MUTED)
	for button: Dictionary in buttons:
		var active: bool = mode == button.action or _held(button.action)
		var rect: Rect2 = button.rect
		draw_rect(rect, Color("326755") if active else Color("1c393e"))
		draw_rect(rect, ACCENT if active else Color("365258"), false, 1.5)
		var size: int = 16 if rect.size.x > 60 else 12
		var text_size: Vector2 = ThemeDB.fallback_font.get_string_size(button.action, HORIZONTAL_ALIGNMENT_LEFT, -1.0, size)
		_text(button.action, rect.position + Vector2((rect.size.x - text_size.x) * 0.5, rect.size.y * 0.5 + 6), size)
	_text("Drag: pan  |  Two fingers: rotate + zoom  |  Q/E: rotate  |  WASD: move", Vector2(232, last_size.y - 109), 16, MUTED)

func _capture(directory: String) -> void:
	DirAccess.make_dir_recursive_absolute(directory)
	# Exercise the same pointer router used by real touches, not a fake screenshot renderer.
	mode = "PLACE"
	var target: Vector2 = camera.project(Vector2(8.5, 3.5))
	_pointer_down(0, target)
	_pointer_up(0, target)
	if not world.markers.has(Vector2i(8, 3)):
		push_error("LAB_UI_FAIL: tap placement")
		get_tree().quit(1)
		return
	var count: int = world.markers.size()
	_pointer_down(0, camera.project(Vector2(1.5, 5.5)))
	_pointer_down(1, camera.project(Vector2(2.5, 5.5)))
	_pointer_move(1, camera.project(Vector2(2.7, 5.2)))
	_pointer_up(1, Vector2.ZERO)
	_pointer_up(0, Vector2.ZERO)
	if count != world.markers.size():
		push_error("LAB_UI_FAIL: pinch caused placement")
		get_tree().quit(1)
		return
	_action("HOME")
	mode = "MOVE"
	for degrees: int in [45, 135, 225, 315]:
		camera.angle = deg_to_rad(float(degrees))
		status = "Automated engine capture | %d degrees | TapPlay NOT tested" % degrees
		queue_redraw()
		await get_tree().process_frame
		await RenderingServer.frame_post_draw
		var image: Image = get_viewport().get_texture().get_image()
		var result: Error = image.save_png(directory.path_join("view_%03d.png" % degrees))
		if result != OK:
			get_tree().quit(1)
			return
	print("LAB_CAPTURE_OK: real engine renders at four angles; pointer placement and pinch suppression passed")
	get_tree().quit(0)
