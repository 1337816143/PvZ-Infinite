extends RefCounted
## Orthographic 2.5D ray/footprint test, independent of origin and zoom.
## Along the viewer ray, planar depth increases t and height increases SQUASH*t.
static func ray_hits(point: Vector2, height: float, footprint: Rect2, top: float, angle: float, squash: float = 0.55) -> bool:
	if top <= height or squash <= 0.0 or not footprint.has_area():
		return false
	var direction: Vector2 = Vector2(sin(angle), cos(angle))
	var near_t: float = 0.0001
	var far_t: float = (top - height) / squash
	for axis: int in range(2):
		if absf(direction[axis]) < 0.00001:
			if point[axis] < footprint.position[axis] or point[axis] > footprint.end[axis]:
				return false
		else:
			var a: float = (footprint.position[axis] - point[axis]) / direction[axis]
			var b: float = (footprint.end[axis] - point[axis]) / direction[axis]
			near_t = maxf(near_t, minf(a, b))
			far_t = minf(far_t, maxf(a, b))
	return far_t >= near_t

static func covers_player(point: Vector2, footprint: Rect2, top: float, angle: float) -> bool:
	# Multiple sample heights catch head, torso and feet; this is readability fading,
	# not a claim of pixel-perfect occlusion for arbitrary artwork or overhangs.
	for h: float in [0.12, 0.34, 0.62]:
		if ray_hits(point, h, footprint, top, angle):
			return true
	return false
