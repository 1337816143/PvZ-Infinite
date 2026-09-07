extends SceneTree
const Scene = preload("res://main.tscn")
var output: String = ""
var report: Dictionary = {"kind": "Linux software renderer; NOT ARM or TapPlay", "captures": [], "load_stages": []}

func _initialize() -> void:
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--matrix-dir="):
			output = arg.trim_prefix("--matrix-dir=")
	_run.call_deferred()

func _run() -> void:
	if output.is_empty():
		quit(1)
		return
	DirAccess.make_dir_recursive_absolute(output)
	var app = Scene.instantiate()
	app.capture_running = true
	root.add_child(app)
	app.application_active = true
	# Disable fixed 1280x720 stretch during direct-size desktop fixture capture only.
	root.content_scale_size = Vector2i.ZERO
	for size: Vector2i in [Vector2i(960,540), Vector2i(1280,720), Vector2i(1600,720), Vector2i(1024,768), Vector2i(720,1280)]:
		root.size = size
		await process_frame
		app.safe_override = Rect2(40, 20, size.x - 80, size.y - 40)
		app._layout()
		app._action("HOME")
		app.status = "Synthetic safe margins | %dx%d | NOT physical notch verification" % [size.x, size.y]
		var name: String = "layout_%dx%d.png" % [size.x, size.y]
		if not await app._save_capture(output.path_join(name)):
			quit(1)
			return
		report.captures.append({"file": name, "size": [size.x,size.y], "rows": app.ui.rows})
	root.size = Vector2i(1280, 720)
	await process_frame
	app.safe_override = Rect2()
	app._layout()
	app._action("HOME")
	# Place the actor just behind the L footprint, along each viewer direction.
	for degree: int in [0, 45, 90, 135, 180, 225, 270, 315]:
		app.camera.angle = deg_to_rad(degree)
		app.world.player = Vector2(4.5, 4.5) - Vector2(sin(app.camera.angle), cos(app.camera.angle)) * 1.6
		app.status = "L-footprint occlusion fixture | %d degrees | visual-only placement" % degree
		var name: String = "compound_%03d.png" % degree
		if not await app._save_capture(output.path_join(name)):
			quit(1)
			return
		report.captures.append({"file": name, "faded_blocks": app.faded_count})
	app.world.player = Vector2(2.5,2.5)
	for count: int in [0,128,512]:
		app.stress_count = count
		app.status = "Measured draw-only load | %d markers | NOT combat or ARM performance" % count
		# Warm up each stage, then measure wall-clock frames, not a synthetic dt loop.
		await create_timer(2.0).timeout
		app.frame_ms.clear()
		app.sample_cursor = 0
		var start: Dictionary = app.metrics()
		var started: int = Time.get_ticks_msec()
		while Time.get_ticks_msec() - started < 10000:
			app.camera.angle = wrapf(app.camera.angle + 0.005, -PI, PI)
			await process_frame
		var finish: Dictionary = app.metrics()
		finish["elapsed_ms"] = Time.get_ticks_msec() - started
		finish["frames_measured"] = finish.frame_total - start.frame_total
		finish["memory_delta_bytes"] = finish.static_bytes - start.static_bytes
		finish["node_delta"] = finish.nodes - start.nodes
		report.load_stages.append(finish)
		if finish.samples > 600 or finish.cache_entries != 121 or finish.node_delta > 2:
			push_error("MATRIX_FAIL: bounded state grew unexpectedly")
			quit(1)
			return
		await app._save_capture(output.path_join("stress_%d.png" % count))
	var file: FileAccess = FileAccess.open(output.path_join("report.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  "))
	file.close()
	print("LAB_RENDER_MATRIX_OK: layouts=5 compound_angles=8 load_stages=3; NOT TapPlay")
	app.free()
	quit(0)
