extends SceneTree
const LabWorld = preload("res://scripts/world.gd")
const Store = preload("res://scripts/save_store.gd")
const Scene = preload("res://main.tscn")
var checks: int = 0
var failures: int = 0
const PATH: String = "user://hardening-test.json"

func check(condition: bool, label: String) -> void:
	checks += 1
	if not condition:
		failures += 1
		printerr("HARDENING_FAIL: " + label)

func cleanup(path: String) -> void:
	for suffix: String in ["", ".tmp", ".bak", ".bak.tmp"]:
		if FileAccess.file_exists(path + suffix):
			DirAccess.remove_absolute(path + suffix)

func write_text(path: String, text: String) -> void:
	var f: FileAccess = FileAccess.open(path, FileAccess.WRITE)
	check(f != null, "test fixture writable")
	if f != null:
		f.store_string(text)
		f.close()

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	cleanup(PATH)
	var world = LabWorld.new()
	var store = Store.new()
	check(not store.load_into(PATH, world), "missing save rejected")
	var first: Dictionary = world.snapshot()
	check(store.save(PATH, world), "initial verified write")
	check(store._read(PATH) == first, "verified payload roundtrip")
	check(world.place(Vector2i(8, 3)), "second snapshot placement")
	var second: Dictionary = world.snapshot()
	check(store.save(PATH, world), "replacement write")
	check(store._read(PATH + ".bak") == first, "previous generation preserved")
	check(store.save(PATH, world), "identical checkpoint succeeds")
	check(store._read(PATH + ".bak") == first, "identical checkpoint does not rotate backup")
	write_text(PATH, "{truncated")
	check(store.load_into(PATH, world), "corrupt primary recovered")
	check(store.recovered_from == "bak" and world.snapshot() == first, "backup selected explicitly")
	world.restore(second)
	check(store.save(PATH, world), "repair corrupt primary with valid state")
	check(store._read(PATH + ".bak") == first, "corrupt primary never overwrites good backup")
	var f: FileAccess = FileAccess.open(PATH, FileAccess.READ)
	var envelope: Dictionary = JSON.parse_string(f.get_as_text())
	f.close()
	envelope["sha256"] = "incorrect"
	write_text(PATH, JSON.stringify(envelope))
	check(store._read(PATH).is_empty(), "checksum mismatch rejected")
	check(store.load_into(PATH, world) and store.recovered_from == "bak", "checksum failure recovers backup")
	cleanup(PATH)
	write_text(PATH, JSON.stringify(second))
	check(store.load_into(PATH, world) and world.snapshot() == second, "legacy v0.1 snapshot readable")
	cleanup(PATH)
	write_text(PATH + ".tmp", JSON.stringify(first))
	check(store.load_into(PATH, world) and store.recovered_from == "tmp", "orphan temporary checkpoint recoverable")
	write_text(PATH, "x".repeat(Store.MAX_BYTES + 1))
	check(store._read(PATH).is_empty(), "oversized file rejected before parse")
	write_text(PATH + ".bak", "broken")
	write_text(PATH + ".tmp", "broken")
	var before: Dictionary = world.snapshot()
	check(not store.load_into(PATH, world), "all corrupt files rejected")
	check(world.snapshot() == before, "failed recovery is transactional")
	for payload: Variant in [null, [], {}, {"schema":99}, {"schema":1,"purpose":"prejam-camera-lab","player":[1e99,2],"markers":[]}, {"schema":1,"purpose":"prejam-camera-lab","player":[2.5,2.5],"markers":[[1e99,2]]}, {"schema":1,"purpose":"prejam-camera-lab","player":[2.5,2.5],"markers":[[8,3],[8,3]]}, {"schema":1,"purpose":"prejam-camera-lab","player":[4.5,4.5],"markers":[]}, {"schema":1,"purpose":"prejam-camera-lab","player":[2.5,2.5],"markers":[[8.2,3]]}, {"schema":1,"purpose":"prejam-camera-lab","player":[true,2],"markers":[]}]:
		check(not store._valid(payload), "invalid payload rejected")
	world.player = Vector2(INF, 2)
	check(not store.save(PATH, world), "nonfinite state never saved")
	cleanup(PATH)
	# Instantiate the actual runtime scene and use its real pointer routing methods.
	var app = Scene.instantiate()
	app.save_path = PATH
	root.add_child(app)
	await process_frame
	app.application_active = true
	app.mode = "PLACE"
	var target: Vector2 = app.camera.project(Vector2(8.5, 3.5))
	app._pointer_down(0, target)
	app._pointer_cancel(0)
	app._pointer_up(0, target)
	check(app.world.markers.is_empty(), "cancelled touch cannot place")
	app._pointer_down(0, target)
	app._pointer_up(0, Vector2(target.x, 40))
	check(app.world.markers.is_empty(), "release over HUD cannot place")
	app._pointer_down(0, target)
	app._pointer_up(0, target + Vector2(35, 0))
	check(app.world.markers.is_empty(), "large release displacement is not a tap")
	var button_point: Vector2 = Vector2.ZERO
	for button: Dictionary in app.buttons:
		if button.action == "TURN L":
			button_point = button.rect.get_center()
	app._pointer_down(3, button_point)
	check(app._held("TURN L"), "turn press captured")
	app._pointer_move(3, target)
	check(not app._held("TURN L"), "leaving button stops turn")
	app._pointer_up(3, target)
	check(app.world.markers.is_empty(), "button drag cannot place on ground")
	app._pointer_down(0, target)
	app._pointer_down(1, target + Vector2(45, 20))
	app._pointer_move(1, target + Vector2(60, 30))
	app._pointer_up(1, target + Vector2(60, 30))
	app._pointer_up(0, target)
	check(app.world.markers.is_empty(), "pinch release cannot place")
	app._action("HOME")
	target = app.camera.project(Vector2(8.5, 3.5))
	app._pointer_down(0, target)
	app._pointer_up(0, target)
	check(app.world.markers.has(Vector2i(8, 3)), "normal tap still places")
	check(not store._read(PATH).is_empty(), "placement creates verified checkpoint")
	app.route = app.world.path_to(Vector2i(8, 8))
	app.held[2] = "UP"
	app.right_drag = true
	# Object.notification dispatches to every inherited script; calling the virtual
	# _notification method directly bypasses the inherited lifecycle handlers.
	# See Godot 4.5 Object.notification and Object._notification documentation.
	app.wall_frame_usec = 12345
	app.notification(Node.NOTIFICATION_APPLICATION_PAUSED)
	check(not app.application_active and app.held.is_empty() and app.fingers.is_empty() and app.route.is_empty() and not app.right_drag, "pause clears all input and route")
	check(app.wall_frame_usec == 0, "pause resets wall-clock measurement")
	var player_before: Vector2 = app.world.player
	app._process(0.1)
	check(app.world.player == player_before, "paused scene cannot keep walking")
	app.wall_frame_usec = 67890
	app.notification(Node.NOTIFICATION_APPLICATION_RESUMED)
	check(app.application_active and app.held.is_empty(), "resume has no stuck input")
	check(app.wall_frame_usec == 0, "resume does not count suspended time as a frame")
	app.free()
	cleanup(PATH)
	print("LAB_HARDENING_RESULT: checks=%d failures=%d" % [checks, failures])
	quit(0 if failures == 0 else 1)
