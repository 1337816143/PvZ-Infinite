extends SceneTree
const Scene = preload("res://main.tscn")
var output: String = ""
var report: Dictionary = {"kind":"same-process Linux software renderer A/B, NOT phone or TapPlay", "stages":[]}

func _initialize() -> void:
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--batch-dir="):
			output = arg.trim_prefix("--batch-dir=")
	_run.call_deferred()

func measure(app, count: int, batch: bool, seconds: float, turning: bool) -> Dictionary:
	app.batch_terrain_enabled = batch
	app.stress_count = count
	app.stress_time = 0.0
	app.camera.angle = PI / 4.0
	app._action("HOME")
	app.status = "A/B terrain only | %s | %d unchanged FX markers" % ["B1" if batch else "REFERENCE", count]
	await create_timer(2.0).timeout
	app.frame_ms.clear()
	app.sample_cursor = 0
	var start: Dictionary = app.metrics()
	var began: int = Time.get_ticks_usec()
	var previous: int = began
	while float(Time.get_ticks_usec() - began) / 1000000.0 < seconds:
		var now: int = Time.get_ticks_usec()
		if turning:
			app.camera.angle = wrapf(app.camera.angle + float(now-previous) / 1000000.0 * 0.3, -PI, PI)
		previous = now
		await process_frame
	var result: Dictionary = app.metrics()
	result["elapsed_ms"] = float(Time.get_ticks_usec()-began) / 1000.0
	result["frames_measured"] = result.frame_total - start.frame_total
	result["observed_fps"] = float(result.frames_measured)*1000.0 / result.elapsed_ms
	result["memory_delta_bytes"] = result.static_bytes-start.static_bytes
	result["node_delta"] = result.nodes-start.nodes
	result["turning"] = turning
	return result

func grid_matches_camera(app) -> bool:
	if app.grid_segments.size() != 48:
		return false
	for i: int in range(12):
		var points: Array[Vector2] = [Vector2(i,0), Vector2(i,11), Vector2(0,i), Vector2(11,i)]
		for j: int in range(4):
			if app.grid_segments[i*4+j].distance_to(app.camera.project(points[j])) > 0.001:
				return false
	return true

func _run() -> void:
	if output.is_empty():
		quit(1)
		return
	DirAccess.make_dir_recursive_absolute(output)
	var app = Scene.instantiate()
	app.capture_running = true
	root.add_child(app)
	app.application_active = true
	root.size = Vector2i(1280,720)
	await process_frame
	for count: int in [0,128,512]:
		var order: Array = [false,true] if count != 128 else [true,false]
		for batch: bool in order:
			report.stages.append(await measure(app,count,batch,6.0,true))
	app.stress_count = 128
	app.world.player = Vector2(4.5,2.9)
	app.camera.angle = PI/4.0
	app.set_process(false)
	for batch: bool in [false,true]:
		app.batch_terrain_enabled = batch
		app.status = "Matched visual fixture | terrain renderer: " + ("B1" if batch else "REFERENCE")
		app.queue_redraw()
		if not await app._save_capture(output.path_join("visual_b1.png" if batch else "visual_reference.png")):
			quit(1)
			return
	report["grid_alignment_after_reference_switch"] = grid_matches_camera(app)
	app.set_process(true)
	var snapshot: Dictionary = app.world.snapshot()
	var soak: Dictionary = await measure(app,512,true,60.0,true)
	report["soak_60_seconds"] = soak
	var good: bool = soak.samples <= 600 and soak.cache_entries == 121 and soak.ground_mesh_builds == 1 and soak.node_delta == 0 and app.world.snapshot() == snapshot and report.grid_alignment_after_reference_switch
	report["bounded_state_pass"] = good
	var file: FileAccess = FileAccess.open(output.path_join("report.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify(report,"  "))
	file.close()
	app.free()
	print("LAB_BATCH_RENDER_OK" if good else "BATCH_FAIL: bounded state or grid alignment")
	quit(0 if good else 1)
