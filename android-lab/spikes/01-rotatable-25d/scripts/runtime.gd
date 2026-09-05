extends "res://scripts/main.gd"
## Lifecycle/input hardening around the existing camera experiment, not a new game.
const SaveStore = preload("res://scripts/save_store.gd")
var store = SaveStore.new()
var save_path: String = SAVE_PATH
var application_active: bool = true
var autosave_elapsed: float = 0.0
var probe_elapsed: float = 0.0
var probe_enabled: bool = false
var session_id: String = ""
var last_checkpoint_ok: bool = true

func _ready() -> void:
	session_id = str(Time.get_unix_time_from_system()) + ":" + str(Time.get_ticks_usec())
	super._ready()
	get_tree().auto_accept_quit = false
	# Tests opt out of touching the user's default checkpoint.
	var isolated: bool = "--lab-unit-tests" in OS.get_cmdline_user_args()
	probe_enabled = OS.is_debug_build() and FileAccess.file_exists("user://ci_probe.enabled")
	if not capture_running and not isolated and store.has_any(save_path):
		if store.load_into(save_path, world):
			status = "Checkpoint restored (" + store.recovered_from + ") | Local lab only"
		else:
			status = store.last_error
	_write_probe()

func _process(delta: float) -> void:
	if application_active:
		super._process(delta)
		if not capture_running:
			autosave_elapsed += delta
			if autosave_elapsed >= 2.0:
				autosave_elapsed = 0.0
				_checkpoint()
	else:
		if get_viewport_rect().size != last_size:
			_layout()
		queue_redraw()
	if probe_enabled:
		probe_elapsed += delta
		if probe_elapsed >= 0.5:
			probe_elapsed = 0.0
			_write_probe()

func _reset_input() -> void:
	held.clear()
	fingers.clear()
	multi_gesture = false
	right_drag = false
	route.clear()

func _checkpoint() -> void:
	last_checkpoint_ok = store.save(save_path, world)
	if not last_checkpoint_ok:
		status = store.last_error

func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_PAUSED or what == NOTIFICATION_APPLICATION_FOCUS_OUT:
		application_active = false
		_reset_input()
		if is_inside_tree() and not capture_running:
			_checkpoint()
			_write_probe()
	elif what == NOTIFICATION_APPLICATION_RESUMED or what == NOTIFICATION_APPLICATION_FOCUS_IN:
		application_active = true
		_reset_input()
	elif what == NOTIFICATION_WM_CLOSE_REQUEST or what == NOTIFICATION_WM_GO_BACK_REQUEST:
		_reset_input()
		if not capture_running:
			_checkpoint()
			_write_probe()
		get_tree().quit()

func _action(action: String) -> void:
	if action == "SAVE":
		_checkpoint()
		status = "Verified checkpoint saved locally" if last_checkpoint_ok else store.last_error
	elif action == "LOAD":
		_reset_input()
		status = "Checkpoint restored (" + store.recovered_from + ")" if store.load_into(save_path, world) else store.last_error
	else:
		super._action(action)

func _tap(position: Vector2) -> void:
	super._tap(position)
	if mode in ["PLACE", "ERASE"] and not capture_running:
		_checkpoint()

func _ground_input(position: Vector2) -> bool:
	if position.x < 0.0 or position.x >= last_size.x or position.y < 114.0 or position.y > last_size.y - 94.0:
		return false
	for button: Dictionary in buttons:
		if button.rect.has_point(position):
			return false
	return true

func _pointer_down(id: int, position: Vector2) -> void:
	# A new press cannot inherit a lost release for the same pointer id.
	_pointer_cancel(id)
	super._pointer_down(id, position)

func _pointer_move(id: int, position: Vector2) -> void:
	if held.has(id):
		var captured: String = held[id]
		var inside: bool = false
		for button: Dictionary in buttons:
			if button.action == captured and button.rect.has_point(position):
				inside = true
		if not inside:
			held.erase(id)
		return # Never turn a dragged button press into a ground gesture.
	super._pointer_move(id, position)

func _pointer_cancel(id: int) -> void:
	held.erase(id)
	fingers.erase(id)
	if fingers.is_empty():
		multi_gesture = false

func _pointer_up(id: int, position: Vector2) -> void:
	if fingers.has(id) and (not _ground_input(position) or position.distance_to(fingers[id].start) > 12.0):
		fingers[id].moved = true
	super._pointer_up(id, position)

func _input(event: InputEvent) -> void:
	if capture_running or not application_active:
		return
	if event is InputEventScreenTouch and event.canceled:
		_pointer_cancel(event.index)
		return
	if event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_ESCAPE:
		_reset_input()
		return
	super._input(event)

func _text(value: String, at: Vector2, size: int = 18, color: Color = INK) -> void:
	# Version comes from the export project; inherited v0.1 diagnostic UI stays reusable.
	if value.begins_with("PRE-JAM TECHNICAL EXERCISE  |  v"):
		value = "PRE-JAM TECHNICAL EXERCISE  |  v" + str(ProjectSettings.get_setting("application/config/version")) + "  |  NOT A COMPETITION BUILD"
	super._text(value, at, size, color)

func _write_probe() -> void:
	# Explicitly enabled only in debuggable CI installs. No networking or remote commands.
	if not probe_enabled or not is_inside_tree():
		return
	var controls: Dictionary = {}
	for button: Dictionary in buttons:
		var point: Vector2 = button.rect.get_center()
		controls[button.action] = [point.x, point.y]
	var fixture: Vector2 = camera.project(Vector2(8.5, 3.5))
	var destination: Vector2 = camera.project(Vector2(8.5, 8.5))
	var report: Dictionary = {"session": session_id, "version": ProjectSettings.get_setting("application/config/version"), "snapshot": world.snapshot(), "active": application_active, "held": held.size(), "fingers": fingers.size(), "route": route.size(), "angle": camera.angle, "zoom": camera.zoom, "viewport": [last_size.x, last_size.y], "buttons": controls, "fixture": [fixture.x, fixture.y], "destination": [destination.x, destination.y], "recovered_from": store.recovered_from, "checkpoint_ok": last_checkpoint_ok}
	var file: FileAccess = FileAccess.open("user://lab_diagnostics.json", FileAccess.WRITE)
	if file != null:
		file.store_string(JSON.stringify(report))
		file.close()
