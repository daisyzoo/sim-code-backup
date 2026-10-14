#!/usr/bin/env python3
"""Interactive viewer and repeatable RGB/physics acceptance run for Isaac Sim 6.1."""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import time
import subprocess

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(ROOT / "configs/kitchen.json"))
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--mode", choices=["visual", "collision", "overlay"], default="visual")
    parser.add_argument("--camera", default="kitchen")
    parser.add_argument("--capture", action="store_true", help="Capture every configured camera")
    parser.add_argument("--video-seconds", type=float, default=0)
    parser.add_argument("--demo-seconds", type=float, default=0, help="Seconds per eye-level camera tour, then keep the GUI open")
    parser.add_argument("--demo-repeats", type=int, default=1)
    parser.add_argument("--demo-delay", type=float, default=5, help="Recording preparation time in seconds")
    parser.add_argument("--tour-preview", action="store_true", help="Capture nine route viewpoints for inspection")
    parser.add_argument("--physics-test", action="store_true")
    parser.add_argument("--max-frames", type=int, default=0)
    parser.add_argument("--output", default=str(ROOT / "outputs" / time.strftime("run_%Y%m%d_%H%M%S")))
    args = parser.parse_args()
    if args.demo_repeats < 1 or args.demo_seconds < 0 or args.demo_delay < 0:
        parser.error("Tour repeats must be positive and durations nonnegative")
    cfg = json.loads(Path(args.config).read_text())
    if args.camera not in cfg["cameras"]:
        parser.error("Unknown camera")
    version = importlib.metadata.version("isaacsim")
    if version != "6.1.0.0":
        raise RuntimeError(f"Expected Isaac Sim 6.1.0.0, got {version}; use worldlab/.venv/bin/python")
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    stage_path = ROOT / cfg["output"] / "kitchen.usda"
    if not stage_path.exists():
        raise FileNotFoundError("Run scripts/build_kitchen.py with .venv-tools first")
    os.environ.setdefault("OMNI_KIT_ACCEPT_EULA", "YES")
    # Launch-time flags must be in place BEFORE loading any USD/Omniverse modules.
    sys.argv = [sys.argv[0], "--/renderer/multiGpu/enabled=false",
                "--/exts/isaacsim.physics.newton/auto_switch_on_startup=false",
                "--/exts/isaacsim.core.simulation_manager/default_engine=physx"]
    from isaacsim import SimulationApp
    settings = cfg["render"]
    app = SimulationApp({"headless": args.headless, "width": settings["width"],
                         "height": settings["height"], "multi_gpu": False,
                         "renderer": "RayTracedLighting"})
    report = {"isaacsim": version, "stage": str(stage_path), "mode": args.mode,
              "config": cfg, "status": "running", "images": []}
    try:
        import numpy as np
        import omni.usd
        import omni.replicator.core as rep
        import carb
        render_settings = carb.settings.get_settings()
        render_settings.set("/rtx/post/tonemap/op", 4)
        render_settings.set("/rtx/post/tonemap/filmIso", 200.0)
        render_settings.set("/rtx/post/histogram/enabled", False)
        from pxr import Gf, Usd, UsdGeom, UsdPhysics
        from PIL import Image
        from worldlab.assets import look_at, save_json
        from worldlab.assets import digest
        report["stage_sha256"] = digest(stage_path)
        report["viewer_sha256"] = digest(Path(__file__))
        report["render_settings"] = {
            path: render_settings.get(path) for path in
            ("/rtx/rendermode", "/rtx/post/tonemap/op", "/rtx/post/tonemap/filmIso",
             "/rtx/post/histogram/enabled",
             "/rtx/rtpt/gaussian/skipTonemapping/enabled", "/renderer/multiGpu/enabled")
        }
        context = omni.usd.get_context()
        if not context.open_stage(str(stage_path)):
            raise RuntimeError("Could not open kitchen USD")
        stage = context.get_stage()
        # All viewer changes go to session layer, never mutate generated assets.
        stage.SetEditTarget(stage.GetSessionLayer())
        visual = UsdGeom.Imageable(stage.GetPrimAtPath("/World/Kitchen/Visual"))
        collision = UsdGeom.Imageable(stage.GetPrimAtPath("/World/Kitchen/Collision"))
        visual.GetVisibilityAttr().Set("invisible" if args.mode == "collision" else "inherited")
        collision.GetVisibilityAttr().Set("inherited" if args.mode != "visual" else "invisible")
        if args.mode != "visual":
            # Neutral diagnostic material plus interior fill makes the collision
            # geometry legible; changes live only in the session layer.
            from pxr import Sdf, UsdLux, UsdShade
            mesh = stage.GetPrimAtPath("/World/Kitchen/Collision/Mesh")
            material = UsdShade.Material.Define(stage, "/World/Debug/Material")
            shader = UsdShade.Shader.Define(stage, "/World/Debug/Material/Surface")
            shader.CreateIdAttr("UsdPreviewSurface")
            color = (0.05, 0.8, 0.25) if args.mode == "overlay" else (0.55, 0.55, 0.55)
            shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*color))
            shader.CreateInput("emissiveColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(0.04))
            shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.8)
            shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(0.25 if args.mode == "overlay" else 1.0)
            material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
            UsdShade.MaterialBindingAPI.Apply(mesh).Bind(material)
            for i, position in enumerate(((0, 0.5, 1.5), (0, 2, 1.5))):
                light = UsdLux.SphereLight.Define(stage, f"/World/Debug/Fill_{i}")
                light.CreateRadiusAttr(0.2)
                light.CreateIntensityAttr(150)
                light.AddTranslateOp().Set(Gf.Vec3d(*position))
        camera_path = f"/World/Cameras/{args.camera}"
        from omni.kit.viewport.utility import get_active_viewport
        viewport = get_active_viewport()
        if viewport:
            viewport.set_active_camera(camera_path)
        for _ in range(settings["warmup_frames"]):
            app.update()
        gpu = subprocess.run(["nvidia-smi", "--query-gpu=name,driver_version,memory.used,memory.total",
                              "--format=csv,noheader"], capture_output=True, text=True, timeout=15)
        report["gpu_after_warmup"] = gpu.stdout.strip()
        product = rep.create.render_product(camera_path, (settings["width"], settings["height"]), force_new=True)
        rgb = rep.AnnotatorRegistry.get_annotator("rgb")
        rgb.attach([product])
        current_camera = camera_path

        def select_camera(path):
            nonlocal product, current_camera
            if path != current_camera:
                rgb.detach([product])
                product.destroy()
                product = rep.create.render_product(path, (settings["width"], settings["height"]), force_new=True)
                rgb.attach([product])
                current_camera = path
            for _ in range(30):
                app.update()

        def frame():
            rep.orchestrator.step(rt_subframes=4, pause_timeline=False)
            pixels = np.asarray(rgb.get_data())
            if pixels.ndim != 3 or pixels.shape[2] < 3 or not pixels.size:
                raise RuntimeError(f"Invalid RGB shape: {pixels.shape}")
            return pixels[:, :, :3].copy()

        if args.capture:
            for name in cfg["cameras"]:
                # A dedicated product avoids stale Hydra camera/exposure state
                # when replacing only the camera relationship in a live product.
                select_camera(f"/World/Cameras/{name}")
                pixels = frame()
                Image.fromarray(pixels).save(output / f"{name}_{args.mode}.png")
                metrics = {"camera": name, "mean": float(pixels.mean()), "std": float(pixels.std()),
                           "path": f"{name}_{args.mode}.png", "shape": list(pixels.shape)}
                if not 30 < metrics["mean"] < 220 or metrics["std"] < 5:
                    raise RuntimeError(f"Dark, overexposed or flat frame: {metrics}")
                report["images"].append(metrics)
                save_json(output / "report.json", report)

        if args.video_seconds > 0:
            import imageio.v2 as imageio
            select_camera(camera_path)
            cam = UsdGeom.Camera(stage.GetPrimAtPath(camera_path))
            original = cfg["cameras"][args.camera]
            durations = []
            with imageio.get_writer(output / "kitchen_tour.mp4", fps=24, macro_block_size=1) as writer:
                for index in range(max(1, int(args.video_seconds * 24))):
                    angle = np.sin(index / max(1, args.video_seconds * 24 - 1) * 2 * np.pi)
                    eye = np.array(original["eye"]) + [0.12 * angle, 0, 0]
                    look_at(cam, eye.tolist(), original["target"])
                    start = time.perf_counter()
                    writer.append_data(frame())
                    durations.append(time.perf_counter() - start)
            look_at(cam, original["eye"], original["target"])
            report["video"] = {"path": "kitchen_tour.mp4", "frames": len(durations), "fps": 24,
                               "capture_frame_seconds_mean": float(np.mean(durations))}

        if args.physics_test:
            from pxr import PhysicsSchemaTools, PhysxSchema
            from isaacsim.core.simulation_manager import SimulationManager
            import omni.physx
            import omni.timeline
            SimulationManager.switch_physics_engine("physx")
            if SimulationManager.get_active_physics_engine() != "physx":
                raise RuntimeError("Could not select PhysX for the collision test")
            SimulationManager.setup_simulation(dt=cfg["physics"]["dt"], device="cpu")
            SimulationManager.enable_fabric(False)
            timeline = omni.timeline.get_timeline_interface()
            timeline.play()
            app.update()
            SimulationManager.step(steps=10)
            hits = []
            for x, y in cfg["physics"]["test_xy"]:
                hit = omni.physx.get_physx_scene_query_interface().raycast_closest((x, y, 1.9), (0, 0, -1), 5)
                if not hit["hit"]:
                    raise RuntimeError(f"No floor/counter below ({x}, {y})")
                hits.append((x, y, float(hit["position"][2]), str(hit["collision"])))
            timeline.stop()
            app.update()
            spheres = []
            for i, (x, y, z, path) in enumerate(hits):
                sphere = UsdGeom.Sphere.Define(stage, f"/World/CollisionProbe_{i}")
                sphere.CreateRadiusAttr(0.06)
                sphere.AddTranslateOp().Set(Gf.Vec3d(x, y, z + 0.45))
                UsdPhysics.CollisionAPI.Apply(sphere.GetPrim())
                UsdPhysics.RigidBodyAPI.Apply(sphere.GetPrim())
                UsdPhysics.MassAPI.Apply(sphere.GetPrim()).CreateMassAttr(0.1)
                PhysxSchema.PhysxContactReportAPI.Apply(sphere.GetPrim()).CreateThresholdAttr(0)
                spheres.append(sphere)
            contacts = {str(s.GetPath()): 0 for s in spheres}

            def on_contacts(headers, data):
                for header in headers:
                    paths = [str(PhysicsSchemaTools.intToSdfPath(header.collider0)),
                             str(PhysicsSchemaTools.intToSdfPath(header.collider1))]
                    if "/World/Kitchen/Collision/Mesh" in paths and header.num_contact_data:
                        for path in paths:
                            if path in contacts:
                                contacts[path] += int(header.num_contact_data)

            subscription = omni.physx.get_physx_simulation_interface().subscribe_contact_report_events(on_contacts)
            timeline.play()
            app.update()
            trajectories = [[] for _ in spheres]
            for _ in range(24):
                SimulationManager.step(steps=10)
                omni.physx.get_physx_interface().update_transformations(False, True, True, False)
                for sphere, trajectory in zip(spheres, trajectories):
                    trajectory.append(list(UsdGeom.Xformable(sphere).ComputeLocalToWorldTransform(
                        Usd.TimeCode.Default()).ExtractTranslation()))
            results = []
            for sphere, (x, y, z, path), trajectory in zip(spheres, hits, trajectories):
                end = UsdGeom.Xformable(sphere).ComputeLocalToWorldTransform(Usd.TimeCode.Default()).ExtractTranslation()
                support_hits = []

                def collect_support(hit):
                    if str(hit.collision) == "/World/Kitchen/Collision/Mesh":
                        support_hits.append(float(hit.position[2]))
                    return True

                omni.physx.get_physx_scene_query_interface().raycast_all(
                    (float(end[0]), float(end[1]), float(end[2]) + 0.1), (0, 0, -1), 5, collect_support)
                support_z = max(support_hits) if support_hits else None
                contact_count = contacts[str(sphere.GetPath())]
                passed = (np.isfinite(trajectory).all() and contact_count > 0
                          and support_z is not None and abs(end[2] - support_z - 0.06) < 0.09
                          and z + 0.45 - end[2] > 0.15)
                results.append({"initial_xy": [x, y], "surface_z": z, "collider": path,
                                "final_xyz": list(end), "final_support_z": support_z,
                                "mesh_contact_count": contact_count, "trajectory_every_10_steps": trajectory,
                                "passed": bool(passed)})
            subscription = None
            report["physics"] = {"backend": "physx", "steps": 240, "probes": results,
                                 "passed": all(x["passed"] for x in results)}
            if not report["physics"]["passed"]:
                save_json(output / "report.json", report)
                raise RuntimeError("Collision drop test failed")
            timeline.stop()
            app.update()
        from worldlab.tour import tour_pose, KEYFRAMES
        if args.tour_preview or args.demo_seconds > 0:
            select_camera(camera_path)
            camera = UsdGeom.Camera(stage.GetPrimAtPath(camera_path))
            if viewport:
                viewport.set_active_camera(camera_path)
            if args.tour_preview:
                report["tour_previews"] = []
                for index, key in enumerate(KEYFRAMES):
                    look_at(camera, *tour_pose(key[0]))
                    for _ in range(8):
                        app.update()
                    path = f"tour_{index:02d}.png"
                    Image.fromarray(frame()).save(output / path)
                    report["tour_previews"].append(path)
            look_at(camera, *tour_pose(0))
        if args.demo_seconds > 0:
            print(f"WORLDLAB_DEMO_READY delay={args.demo_delay}", flush=True)
            ready = time.monotonic()
            while app.is_running() and time.monotonic() - ready < args.demo_delay:
                app.update()
                time.sleep(1 / 120)
            laps = []
            print("WORLDLAB_DEMO_START", flush=True)
            for lap in range(args.demo_repeats):
                if not app.is_running():
                    break
                print(f"WORLDLAB_DEMO_LAP {lap + 1}/{args.demo_repeats}", flush=True)
                start = time.monotonic()
                elapsed = 0.0
                while app.is_running():
                    elapsed = time.monotonic() - start
                    look_at(camera, *tour_pose(min(elapsed / args.demo_seconds, 1)))
                    app.update()
                    if elapsed >= args.demo_seconds:
                        break
                    time.sleep(1 / 120)
                laps.append({"lap": lap + 1, "seconds": time.monotonic() - start,
                             "completed": elapsed >= args.demo_seconds})
            completed = len(laps) == args.demo_repeats and all(lap["completed"] for lap in laps)
            report["live_demo"] = {"seconds_per_lap": args.demo_seconds,
                                   "requested_repeats": args.demo_repeats, "laps": laps,
                                   "completed": completed, "route": KEYFRAMES,
                                   "camera_collision_constrained": False}
            print("WORLDLAB_DEMO_COMPLETE" if completed else "WORLDLAB_DEMO_INTERRUPTED", flush=True)
        report["status"] = "passed"
        save_json(output / "report.json", report)
        print("WORLDLAB_REPORT", output / "report.json", flush=True)
        # Headless invocations always terminate unless an explicit frame budget is set.
        frames = 0
        while app.is_running() and (not args.headless or args.max_frames > 0):
            if args.max_frames and frames >= args.max_frames:
                break
            app.update()
            frames += 1
    except Exception as exc:
        import traceback
        traceback.print_exc()
        report["status"] = "failed"
        report["error"] = repr(exc)
        (output / "report.json").write_text(json.dumps(report, indent=2))
        raise
    finally:
        # Kit 6.1 may terminate the process inside close(); preserve failed QA status.
        app.close(exit_code=0 if report["status"] == "passed" else 1)


if __name__ == "__main__":
    main()
