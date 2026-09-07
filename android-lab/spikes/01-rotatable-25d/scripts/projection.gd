extends RefCounted
## Pure ground-plane projection. Heights are drawing offsets, not 3D gameplay.

const SCALE: float = 64.0
const SQUASH: float = 0.55
var angle: float = PI / 4.0
var zoom: float = 1.0
var origin: Vector2 = Vector2(640.0, 365.0)
var focus: Vector2 = Vector2(5.5, 5.5)

func project(point: Vector2, height: float = 0.0) -> Vector2:
	var r: Vector2 = (point - focus).rotated(angle)
	return origin + Vector2(r.x, r.y * SQUASH - height) * SCALE * zoom

func unproject(point: Vector2) -> Vector2:
	var r: Vector2 = (point - origin) / (SCALE * zoom)
	return Vector2(r.x, r.y / SQUASH).rotated(-angle) + focus

func cell_at(point: Vector2) -> Vector2i:
	var p: Vector2 = unproject(point)
	return Vector2i(floori(p.x), floori(p.y))

func depth(point: Vector2) -> float:
	return (point - focus).rotated(angle).y

func screen_direction(direction: Vector2) -> Vector2:
	if direction.is_zero_approx():
		return Vector2.ZERO
	return Vector2(direction.x, direction.y / SQUASH).rotated(-angle).normalized()

func transform_at(anchor: Vector2, rotation: float, factor: float, shift: Vector2 = Vector2.ZERO) -> void:
	var world_anchor: Vector2 = unproject(anchor)
	angle = wrapf(angle + rotation, -PI, PI)
	zoom = clampf(zoom * factor, 0.22, 1.7)
	origin += anchor + shift - project(world_anchor)

func polygon(cell: Vector2i, height: float = 0.0) -> PackedVector2Array:
	var p: Vector2 = Vector2(cell)
	return PackedVector2Array([project(p, height), project(p + Vector2.RIGHT, height), project(p + Vector2.ONE, height), project(p + Vector2.DOWN, height)])
