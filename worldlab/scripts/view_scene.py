#!/usr/bin/env python3
"""Isaac Sim 6.1 scene viewer, RTX capture and PhysX contact acceptance."""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from worldlab.scenes import resolve_scene
from worldlab.assets import digest, save_json


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--scene',required=True)
    parser.add_argument('--headless',action='store_true')
    parser.add_argument('--capture',action='store_true')
    parser.add_argument('--physics-test',action='store_true')
    parser.add_argument('--mode',choices=['visual','collision','overlay'],default='visual')
    parser.add_argument('--camera',default=None)
    parser.add_argument('--video-seconds',type=float,default=0)
    parser.add_argument('--demo-seconds',type=float,default=0)
    parser.add_argument('--demo-repeats',type=int,default=1)
    parser.add_argument('--demo-delay',type=float,default=5)
    parser.add_argument('--output')
    args=parser.parse_args()
    if args.demo_repeats<1 or min(args.video_seconds,args.demo_seconds,args.demo_delay)<0:
        parser.error('Invalid duration/repeats')
    cfg,stage_path,manifest=resolve_scene(args.scene)
    camera_name=args.camera or next(iter(cfg['cameras']))
    if camera_name not in cfg['cameras']:parser.error('Unknown camera')
    version=importlib.metadata.version('isaacsim')
    if version!='6.1.0.0':raise RuntimeError(f'Wrong runtime: {version}')
    output=Path(args.output).resolve() if args.output else ROOT/'outputs'/args.scene/time.strftime('%Y%m%d_%H%M%S')
    output.mkdir(parents=True,exist_ok=True)
    report={'scene':args.scene,'isaacsim':version,'mode':args.mode,'status':'running',
            'build_id':manifest['build_id'],'stage':str(stage_path),'stage_sha256':digest(stage_path),
            'config':cfg,'viewer_sha256':digest(Path(__file__)), 'runtime_modules_sha256': {name:digest(ROOT/'src/worldlab'/name) for name in ('scene_physics.py','scene_tour.py','scenes.py','assets.py')},'manifest':manifest,'images':[]}
    os.environ['OMNI_KIT_ACCEPT_EULA']='YES'
    sys.argv=[sys.argv[0],'--/renderer/multiGpu/enabled=false','--/exts/isaacsim.physics.newton/auto_switch_on_startup=false',
              '--/exts/isaacsim.core.simulation_manager/default_engine=physx']
    from isaacsim import SimulationApp
    render=cfg['render'];started=time.monotonic()
    app=SimulationApp({'headless':args.headless,'width':render['width'],'height':render['height'],
                       'multi_gpu':False,'renderer':'RayTracedLighting'})
    try:
        import numpy as np
        import carb
        import omni.usd
        import omni.replicator.core as rep
        from pxr import Gf,Usd,UsdGeom,UsdShade,UsdLux,Sdf
        from PIL import Image
        from worldlab.assets import look_at
        settings=carb.settings.get_settings()
        settings.set('/rtx/post/tonemap/op',render['tonemap_op'])
        settings.set('/rtx/post/tonemap/filmIso',render['film_iso'])
        settings.set('/rtx/post/histogram/enabled',False)
        context=omni.usd.get_context()
        if not context.open_stage(str(stage_path)):raise RuntimeError('Could not open stage')
        stage=context.get_stage();stage.SetEditTarget(stage.GetSessionLayer())
        targets=set(manifest['collision_paths'])
        if args.mode!='visual':
            if cfg['representation']=='gaussian_static':
                UsdGeom.Imageable(stage.GetPrimAtPath('/World/Environment/Visual')).GetVisibilityAttr().Set('invisible' if args.mode=='collision' else 'inherited')
                UsdGeom.Imageable(stage.GetPrimAtPath('/World/Environment/Collision')).GetVisibilityAttr().Set('inherited')
            material=UsdShade.Material.Define(stage,'/World/Debug/Material')
            shader=UsdShade.Shader.Define(stage,'/World/Debug/Material/Shader');shader.CreateIdAttr('UsdPreviewSurface')
            shader.CreateInput('diffuseColor',Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(0.2,0.7,0.4))
            shader.CreateInput('emissiveColor',Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(0.12))
            shader.CreateInput('roughness',Sdf.ValueTypeNames.Float).Set(0.8)
            if args.mode=='overlay':shader.CreateInput('opacity',Sdf.ValueTypeNames.Float).Set(0.35)
            material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(),'surface')
            for path in targets:UsdShade.MaterialBindingAPI.Apply(stage.GetPrimAtPath(path)).Bind(material)
            for i,pose in enumerate(cfg['cameras'].values()):
                light=UsdLux.SphereLight.Define(stage,f'/World/Debug/Fill{i}')
                light.CreateRadiusAttr(0.2);light.CreateIntensityAttr(250)
                light.AddTranslateOp().Set(Gf.Vec3d(*pose['eye']))
        camera_path=f'/World/Cameras/{camera_name}'
        from omni.kit.viewport.utility import get_active_viewport
        viewport=get_active_viewport()
        if viewport:viewport.set_active_camera(camera_path)
        for _ in range(render['warmup_frames']):app.update()
        # Stage loading can reset renderer settings. Pin the validated values afterwards.
        settings.set('/rtx/post/tonemap/op',render['tonemap_op'])
        settings.set('/rtx/post/tonemap/filmIso',render['film_iso'])
        settings.set('/rtx/post/histogram/enabled',False)
        for _ in range(16):app.update()
        report['startup_and_warmup_seconds']=time.monotonic()-started
        def gpu_info():
            return subprocess.run(['nvidia-smi','--query-gpu=name,driver_version,memory.used,memory.total','--format=csv,noheader'],
                                  capture_output=True,text=True,timeout=15).stdout.strip()
        report['gpu_after_warmup']=gpu_info()
        report['render_settings']={key:settings.get(key) for key in ['/rtx/rendermode','/renderer/multiGpu/enabled','/rtx/post/tonemap/op','/rtx/post/tonemap/filmIso','/rtx/rtpt/gaussian/skipTonemapping/enabled','/rtx/post/histogram/enabled']}
        rgb=rep.AnnotatorRegistry.get_annotator('rgb');product=None
        def select_camera(path):
            nonlocal product
            if product is not None:rgb.detach([product]);product.destroy()
            product=rep.create.render_product(path,(render['width'],render['height']),force_new=True)
            rgb.attach([product])
            for _ in range(30):app.update()
        def frame():
            rep.orchestrator.step(rt_subframes=4,pause_timeline=False)
            pixels=np.asarray(rgb.get_data())
            if pixels.ndim!=3 or pixels.shape[2]<3:raise RuntimeError(f'Invalid RGB {pixels.shape}')
            return pixels[:,:,:3].copy()
        def image_metrics(pixels):
            mean=float(pixels.mean());std=float(pixels.std())
            return {'mean':mean,'std':std,'shape':list(pixels.shape),'passed':20<mean<235 and std>8}
        if args.capture:
            for name in cfg['cameras']:
                select_camera(f'/World/Cameras/{name}');pixels=frame()
                path=f'{name}_{args.mode}.png';Image.fromarray(pixels).save(output/path)
                metrics={'camera':name,'path':path,**image_metrics(pixels)}
                report['images'].append(metrics);save_json(output/'report.json',report)
                if not metrics['passed']:raise RuntimeError(f'Invalid exposure: {metrics}')
        select_camera(camera_path)
        camera=UsdGeom.Camera(stage.GetPrimAtPath(camera_path))
        from worldlab.scene_tour import tour_pose
        route=cfg['tour']
        def pose_at(fraction):
            look_at(camera,*tour_pose(route,fraction))
        if args.video_seconds:
            import imageio.v2 as imageio
            count=max(2,round(args.video_seconds*24));times=[];checks=[]
            with imageio.get_writer(output/'tour.mp4',fps=24,macro_block_size=1) as writer:
                for i in range(count):
                    pose_at(i/(count-1));start=time.perf_counter();pixels=frame()
                    writer.append_data(pixels);times.append(time.perf_counter()-start)
                    if i in (0,count//2,count-1):
                        Image.fromarray(pixels).save(output/f'video_{i:04d}.png');checks.append(image_metrics(pixels))
            report['video']={'path':'tour.mp4','frames':count,'fps':24,'capture_seconds_per_frame':float(np.mean(times)),
                             'keyframes':checks,'passed':all(x['passed'] for x in checks)}
            if not report['video']['passed']:raise RuntimeError('Invalid tour frame')
            look_at(camera,cfg['cameras'][camera_name]['eye'],cfg['cameras'][camera_name]['target'])
        if args.physics_test:
            from worldlab.scene_physics import test_contacts
            report['physics']=test_contacts(app,stage,cfg,targets)
            save_json(output/'report.json',report)
            if not report['physics']['passed']:raise RuntimeError('Physics contact acceptance failed')
        if args.demo_seconds:
            pose_at(0);ready=time.monotonic()
            while app.is_running() and time.monotonic()-ready<args.demo_delay:app.update()
            laps=[]
            for lap in range(args.demo_repeats):
                start=time.monotonic();elapsed=0
                while app.is_running():
                    elapsed=time.monotonic()-start;pose_at(min(1,elapsed/args.demo_seconds));app.update()
                    if elapsed>=args.demo_seconds:break
                    time.sleep(1/120)
                laps.append({'seconds':time.monotonic()-start,'completed':elapsed>=args.demo_seconds})
            report['live_demo']={'laps':laps,'camera_collision_constrained':False}
        report['gpu_after_checks']=gpu_info()
        report['status']='passed';save_json(output/'report.json',report)
        print('WORLDLAB_REPORT',output/'report.json',flush=True)
        while app.is_running() and not args.headless:app.update()
    except Exception as exc:
        import traceback
        traceback.print_exc();report['status']='failed';report['error']=repr(exc)
        save_json(output/'report.json',report)
        raise
    finally:
        app.close(exit_code=0 if report['status']=='passed' else 1)


if __name__=='__main__':main()
