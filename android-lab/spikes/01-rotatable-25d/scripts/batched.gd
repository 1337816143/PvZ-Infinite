extends "res://scripts/adaptive.gd"
## Render B1: same world, actors, input and saves; only terrain submission changes.
## ArrayMesh is drawn in the 2D canvas. No 3D scene, cameras or physics are added.
var batch_terrain_enabled: bool = true
var ground_mesh: ArrayMesh
var ground_mesh_builds: int = 0
var grid_segments: PackedVector2Array = PackedVector2Array()
var batch_cache_key: Array = []

func ground_transform() -> Transform2D:
	var s: float = camera.SCALE * camera.zoom
	var c: float = cos(camera.angle)
	var n: float = sin(camera.angle)
	var x: Vector2 = Vector2(c, n * camera.SQUASH) * s
	var y: Vector2 = Vector2(-n, c * camera.SQUASH) * s
	return Transform2D(x, y, camera.origin - x * camera.focus.x - y * camera.focus.y)

func prepare_ground_mesh() -> void:
	if ground_mesh != null:
		return
	var vertices: PackedVector2Array = PackedVector2Array()
	var colors: PackedColorArray = PackedColorArray()
	var indices: PackedInt32Array = PackedInt32Array()
	for y: int in range(world.SIZE):
		for x: int in range(world.SIZE):
			var offset: int = vertices.size()
			var p: Vector2 = Vector2(x, y)
			var color: Color = Color("28483f") if (x + y) % 2 == 0 else Color("2d5146")
			for corner: Vector2 in [p, p + Vector2.RIGHT, p + Vector2.ONE, p + Vector2.DOWN]:
				vertices.append(corner)
				colors.append(color)
			for index: int in [0, 1, 2, 0, 2, 3]:
				indices.append(offset + index)
	var arrays: Array = []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices
	arrays[Mesh.ARRAY_COLOR] = colors
	arrays[Mesh.ARRAY_INDEX] = indices
	ground_mesh = ArrayMesh.new()
	ground_mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	ground_mesh_builds += 1

func _terrain() -> void:
	if not batch_terrain_enabled:
		super._terrain()
		return
	prepare_ground_mesh()
	var key: Array = [camera.angle, camera.zoom, camera.origin, camera.focus]
	# A/B reference updates cache_key too; batch edges need their own freshness key.
	if key != cache_key or key != batch_cache_key or grid_segments.is_empty():
		terrain_cache.clear()
		for y: int in range(world.SIZE):
			for x: int in range(world.SIZE):
				terrain_cache.append(camera.polygon(Vector2i(x, y)))
		grid_segments.clear()
		for i: int in range(world.SIZE + 1):
			grid_segments.append(camera.project(Vector2(i, 0)))
			grid_segments.append(camera.project(Vector2(i, world.SIZE)))
			grid_segments.append(camera.project(Vector2(0, i)))
			grid_segments.append(camera.project(Vector2(world.SIZE, i)))
		cache_key = key
		batch_cache_key = key.duplicate()
		cache_rebuilds += 1
	draw_set_transform_matrix(ground_transform())
	draw_mesh(ground_mesh, null)
	draw_set_transform_matrix(Transform2D.IDENTITY)
	if show_grid:
		# Each grid edge once, not once for every adjoining tile. Width stays in pixels.
		draw_multiline(grid_segments, Color("436156"), 1.0, true)

func metrics() -> Dictionary:
	var result: Dictionary = super.metrics()
	result["terrain_renderer"] = "B1_batched" if batch_terrain_enabled else "v0.3_reference"
	result["ground_mesh_builds"] = ground_mesh_builds
	result["terrain_submit_calls"] = (2 if show_grid else 1) if batch_terrain_enabled else world.SIZE * world.SIZE * (2 if show_grid else 1)
	result["grid_segment_count"] = grid_segments.size() / 2
	return result
