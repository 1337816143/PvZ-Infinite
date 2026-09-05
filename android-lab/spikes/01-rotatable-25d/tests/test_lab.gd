extends SceneTree

const Projection = preload("res://scripts/projection.gd")
const World = preload("res://scripts/world.gd")
var checks: int = 0
var failures: int = 0

func check(condition: bool, label: String) -> void:
	checks += 1
	if not condition:
		failures += 1
		if failures < 15:
			printerr("FAIL: " + label)

func _init() -> void:
	var camera = Projection.new()
	for degrees in range(0, 360, 5):
		camera.angle = deg_to_rad(float(degrees))
		for zoom: float in [0.55, 1.0, 1.7]:
			camera.zoom = zoom
			for y in range(World.SIZE):
				for x in range(World.SIZE):
					for offset: Vector2 in [Vector2(0.5, 0.5), Vector2(0.08, 0.08), Vector2(0.92, 0.08), Vector2(0.92, 0.92), Vector2(0.08, 0.92)]:
						var world_point: Vector2 = Vector2(x, y) + offset
						var screen: Vector2 = camera.project(world_point)
						check(camera.unproject(screen).distance_to(world_point) < 0.0001, "projection round trip")
						check(camera.cell_at(screen) == Vector2i(x, y), "cell picking after rotation")
			for axis: Vector2 in [Vector2.UP, Vector2.DOWN, Vector2.LEFT, Vector2.RIGHT]:
				var projected: Vector2 = camera.project(camera.focus + camera.screen_direction(axis)) - camera.project(camera.focus)
				check(projected.normalized().dot(axis) > 0.9999, "screen-relative movement")
	var anchor: Vector2 = Vector2(535, 320)
	var expected: Vector2 = camera.unproject(anchor)
	camera.transform_at(anchor, 0.43, 1.1, Vector2(10, -5))
	check(camera.unproject(anchor + Vector2(10, -5)).distance_to(expected) < 0.0001, "gesture anchor")
	var world = World.new()
	check(not world.place(Vector2i(4, 4)), "fixed blocker protected")
	check(not world.place(Vector2i(2, 2)), "player overlap refused")
	check(not world.place(Vector2i(-1, 0)), "out of bounds refused")
	check(world.place(Vector2i(8, 3)), "valid placement")
	check(not world.place(Vector2i(8, 3)), "duplicate refused")
	var route: PackedVector2Array = world.path_to(Vector2i(8, 8))
	check(not route.is_empty(), "path exists around blockers")
	for point: Vector2 in route:
		check(world.can_stand(point), "path walkable")
	world.player = Vector2(3.5, 4.5)
	world.move_by(Vector2(3, 0))
	check(world.player.x < 4.0, "large move cannot tunnel")
	var copy = World.new()
	check(copy.restore(world.snapshot()), "snapshot restores")
	check(copy.player.is_equal_approx(world.player) and copy.markers == world.markers, "snapshot equality")
	var before: Dictionary = copy.snapshot()
	check(not copy.restore({"schema": 99}), "unknown schema rejected")
	check(copy.snapshot() == before, "failed load preserves state")
	check(not copy.restore({"schema": 1, "purpose": "prejam-camera-lab", "player": [4.5, 4.5], "markers": []}), "blocked player rejected")
	check(copy.snapshot() == before, "blocked load transactional")
	var save_path: String = "user://lab_automated_test.json"
	check(world.save_to(save_path), "save file write")
	check(copy.load_from(save_path), "save file read")
	check(copy.snapshot() == world.snapshot(), "file round trip")
	DirAccess.remove_absolute(save_path)
	print("LAB_TEST_RESULT: checks=%d failures=%d" % [checks, failures])
	quit(0 if failures == 0 else 1)
