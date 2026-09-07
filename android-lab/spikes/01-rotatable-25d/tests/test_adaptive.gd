extends SceneTree
const Layout = preload("res://scripts/lab_layout.gd")
const Occlusion = preload("res://scripts/lab_occlusion.gd")
const ProjectionModel = preload("res://scripts/projection.gd")
const Scene = preload("res://main.tscn")
var checks: int = 0
var failures: int = 0

func check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		if failures < 15:
			printerr("ADAPTIVE_FAIL: " + message)

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	for size: Vector2 in [Vector2(640,480), Vector2(960,540), Vector2(1280,720), Vector2(1600,720), Vector2(1920,1080), Vector2(1024,768), Vector2(720,1280)]:
		for inset: float in [0.0, 24.0, 48.0]:
			for density: float in [1.0, 1.4, 1.8]:
				var safe: Rect2 = Rect2(inset, 12, size.x - inset * 2, size.y - 24)
				var ui: Dictionary = Layout.make(size, safe, density)
				check(ui.buttons.size() == 16, "all controls retained")
				for i: int in range(ui.buttons.size()):
					var rect: Rect2 = ui.buttons[i].rect
					check(safe.encloses(rect), "control inside safe region %s %s" % [size, ui.buttons[i].action])
					check(rect.size.x >= 48 and rect.size.y >= 48, "minimum logical control extent")
					for j: int in range(i):
						check(not rect.intersects(ui.buttons[j].rect), "controls never overlap")
	# Ray fixtures rotate together, so expected occlusion is invariant.
	var camera = ProjectionModel.new()
	for degree: int in range(0, 360, 5):
		var angle: float = deg_to_rad(degree)
		var toward: Vector2 = Vector2(sin(angle), cos(angle))
		var player: Vector2 = Vector2(5.5, 5.5)
		var front: Vector2 = player + toward * 1.5
		var rear: Vector2 = player - toward * 1.5
		check(Occlusion.ray_hits(player, 0.34, Rect2(front - Vector2.ONE * 0.4, Vector2.ONE * 0.8), 2.0, angle), "front tall object covers torso")
		check(not Occlusion.ray_hits(player, 0.34, Rect2(rear - Vector2.ONE * 0.4, Vector2.ONE * 0.8), 2.0, angle), "rear object must not fade")
		check(not Occlusion.ray_hits(player, 0.62, Rect2(front - Vector2.ONE * 0.4, Vector2.ONE * 0.8), 0.2, angle), "short object cannot cover head")
		camera.angle = angle
		for zoom: float in [0.22, 0.35, 0.55, 1.0, 1.7]:
			camera.zoom = zoom
			for cell: Vector2 in [Vector2(0.5,0.5), Vector2(8.5,3.5), Vector2(10.5,10.5)]:
				check(camera.unproject(camera.project(cell)).distance_to(cell) < 0.0002, "new fit zoom preserves picking")
	check(Occlusion.covers_player(Vector2(2.5, 1.5), Rect2(1, 2, 3, 2), 2, 0), "3x2 rectangular footprint occlusion")
	check(not Occlusion.covers_player(Vector2(2.5, 5.5), Rect2(1, 2, 3, 2), 2, 0), "3x2 rear footprint clear")
	var app = Scene.instantiate()
	app.capture_running = true
	root.add_child(app)
	await process_frame
	app.application_active = true
	app.safe_override = Rect2(48, 24, app.last_size.x - 96, app.last_size.y - 48)
	app._layout()
	app.mode = "PLACE"
	app._pointer_down(0, Vector2(10, app.last_size.y * 0.5))
	app._pointer_up(0, Vector2(10, app.last_size.y * 0.5))
	check(app.world.markers.is_empty(), "safe inset cannot place or pan")
	var snapshot: Dictionary = app.world.snapshot()
	app._action("STRESS")
	check(app.stress_count == 128, "bounded stress first level")
	app._action("STRESS")
	check(app.stress_count == 512, "bounded stress second level")
	app._action("STRESS")
	check(app.stress_count == 0 and app.world.snapshot() == snapshot, "stress cannot mutate saved world")
	for i: int in range(1300):
		app._process(0.016)
	check(app.frame_ms.size() == 600, "telemetry ring buffer remains bounded")
	app.free()
	print("LAB_ADAPTIVE_RESULT: checks=%d failures=%d" % [checks, failures])
	quit(0 if failures == 0 else 1)
