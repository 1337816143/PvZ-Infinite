extends SceneTree
const Scene = preload("res://main.tscn")
var checks: int = 0
var failures: int = 0

func check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		printerr("BATCH_FAIL: " + message)

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var app = Scene.instantiate()
	app.capture_running = true
	root.add_child(app)
	await process_frame
	app.prepare_ground_mesh()
	var original: ArrayMesh = app.ground_mesh
	for degree: int in range(0,360,5):
		for zoom: float in [0.22, 0.55, 1.0, 1.7]:
			app.camera.angle = deg_to_rad(degree)
			app.camera.zoom = zoom
			app.camera.origin = Vector2(713,287)
			app.camera.focus = Vector2(4.3,6.1)
			var transform: Transform2D = app.ground_transform()
			for point: Vector2 in [Vector2.ZERO, Vector2(11,11), Vector2(8.5,3.5), Vector2(4.3,6.1)]:
				check((transform * point).distance_to(app.camera.project(point)) < 0.001, "mesh transform matches original projection")
			app.prepare_ground_mesh()
			check(app.ground_mesh == original and app.ground_mesh_builds == 1, "rotating cannot rebuild immutable world mesh")
	var arrays: Array = app.ground_mesh.surface_get_arrays(0)
	check(arrays[Mesh.ARRAY_VERTEX].size() == 484, "121 tiles retain four vertices each")
	check(arrays[Mesh.ARRAY_INDEX].size() == 726, "two triangles per tile")
	check(arrays[Mesh.ARRAY_COLOR].size() == 484, "checker colors retained")
	for index: int in arrays[Mesh.ARRAY_INDEX]:
		check(index >= 0 and index < 484, "triangle index bounded")
	var snapshot: Dictionary = app.world.snapshot()
	app.batch_terrain_enabled = false
	check(app.metrics().terrain_submit_calls == 242, "reference submission count")
	app.batch_terrain_enabled = true
	check(app.metrics().terrain_submit_calls == 2, "batched mesh plus grid submission count")
	check(app.world.snapshot() == snapshot, "renderer switch cannot mutate saved world")
	app.free()
	print("LAB_BATCH_RESULT: checks=%d failures=%d" % [checks,failures])
	quit(0 if failures == 0 else 1)
