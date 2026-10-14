#!/usr/bin/env python3
"""One-window recording playlist with scene labels and timed closed walking tours."""
import argparse
import importlib.metadata
import os
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from worldlab.assets import digest,save_json
from worldlab.scenes import resolve_scene
from worldlab.scene_tour import tour_pose

TITLES={
    'hallway1_elegant':('ELEGANT HALLWAY',0xffffd580,'SPZ + GLB'),
    'hallway1_modern':('MODERN HALLWAY',0xff90e0a0,'SPZ + GLB'),
    'hallway2':('HALLWAY 2 / GLB IMPORT',0xff80c0ff,'GLB -> USD / Isaac Sim 6.1'),
    'hallway2_blend':('HALLWAY 2 / DIRECT BLEND',0xffffa8e0,'BLEND -> USDC / Isaac Sim 6.1'),
}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--scenes',nargs='+',choices=list(TITLES),default=['hallway1_elegant','hallway1_modern','hallway2'])
    parser.add_argument('--seconds',type=float,default=15)
    parser.add_argument('--repeats',type=int,default=3)
    parser.add_argument('--prepare',type=float,default=8)
    parser.add_argument('--exit-after',action='store_true')
    parser.add_argument('--output',default=str(ROOT/'outputs/recording_tour'/time.strftime('%Y%m%d_%H%M%S')))
    args=parser.parse_args()
    if args.seconds<=0 or args.repeats<1 or args.prepare<0:parser.error('Invalid duration/repeats')
    if importlib.metadata.version('isaacsim')!='6.1.0.0':raise RuntimeError('Use worldlab Isaac Sim 6.1 environment')
    scenes=[resolve_scene(scene) for scene in args.scenes]
    output=Path(args.output).resolve()
    output.mkdir(parents=True,exist_ok=False)
    report={'isaacsim':'6.1.0.0','status':'running','seconds_per_lap':args.seconds,'repeats':args.repeats,
            'script_sha256':digest(Path(__file__)),'scenes':[],
            'camera_collision_constrained':False,'display_labels':True}
    save_json(output/'report.json',report)
    os.environ['OMNI_KIT_ACCEPT_EULA']='YES'
    sys.argv=[sys.argv[0],'--/renderer/multiGpu/enabled=false',
              '--/exts/isaacsim.physics.newton/auto_switch_on_startup=false',
              '--/exts/isaacsim.core.simulation_manager/default_engine=physx']
    from isaacsim import SimulationApp
    app=SimulationApp({'headless':False,'width':1280,'height':720,'multi_gpu':False,'renderer':'RayTracedLighting'})
    try:
        import carb
        import omni.usd
        import omni.ui as ui
        import omni.kit.renderer.capture
        from omni.kit.viewport.utility import get_active_viewport_window
        from pxr import UsdGeom
        from worldlab.assets import look_at
        context=omni.usd.get_context()
        settings=carb.settings.get_settings()
        capture=omni.kit.renderer.capture.acquire_renderer_capture_interface()
        def update():
            if not app.is_running():raise RuntimeError('Recording tour interrupted: window closed')
            app.update()
        window=get_active_viewport_window()
        if window is None:raise RuntimeError('Recording requires a visible viewport')
        hud=window.get_frame('worldlab_recording_tour')
        with hud:
            with ui.VStack():
                ui.Spacer(height=12)
                with ui.HStack(height=82):
                    ui.Spacer(width=12)
                    with ui.ZStack(width=650):
                        ui.Rectangle(style={'background_color':0xe5222222,'border_radius':6})
                        with ui.VStack(spacing=4,style={'margin':10}):
                            title=ui.Label('WORLDLAB',height=32,style={'font_size':26,'color':0xffffffff})
                            status=ui.Label('Loading...',height=26,style={'font_size':20,'color':0xffffffff})
                    ui.Spacer()
                ui.Spacer()
        for index,((cfg,path,manifest),scene) in enumerate(zip(scenes,args.scenes),1):
            display,color,source=TITLES[scene]
            title.text=f'{index}/{len(scenes)}  {display}'
            title.style={'font_size':26,'color':color}
            status.text=f'{scene} | Loading scene...'
            update()
            if not context.open_stage(str(path)):raise RuntimeError(f'Cannot open {path}')
            stage=context.get_stage();stage.SetEditTarget(stage.GetSessionLayer())
            camera_path='/World/Cameras/'+next(iter(cfg['cameras']))
            camera=UsdGeom.Camera(stage.GetPrimAtPath(camera_path))
            window.viewport_api.set_active_camera(camera_path)
            look_at(camera,*tour_pose(cfg['tour'],0))
            for _ in range(cfg['render']['warmup_frames']):update()
            settings.set('/rtx/post/tonemap/op',cfg['render']['tonemap_op'])
            settings.set('/rtx/post/tonemap/filmIso',cfg['render']['film_iso'])
            settings.set('/rtx/post/histogram/enabled',False)
            for _ in range(16):update()
            item={'scene':scene,'title':display,'build_id':manifest['build_id'],
                  'stage_sha256':digest(path),'route_yaw_degrees':cfg['tour'][-1]['yaw']-cfg['tour'][0]['yaw'],
                  'laps':[]}
            report['scenes'].append(item)
            start=time.monotonic()
            print('WORLDLAB_TOUR_READY',scene,flush=True)
            while time.monotonic()-start<args.prepare:
                remaining=max(0,args.prepare-(time.monotonic()-start))
                status.text=f'{source} | Recording starts in {remaining:04.1f}s'
                update();time.sleep(1/120)
            for lap in range(1,args.repeats+1):
                start=time.monotonic();frames=0
                print('WORLDLAB_TOUR_LAP',scene,lap,flush=True)
                evidence_requested=False
                while True:
                    elapsed=time.monotonic()-start
                    fraction=min(1,elapsed/args.seconds)
                    look_at(camera,*tour_pose(cfg['tour'],fraction))
                    status.text=f'{source} | TAKE {lap}/{args.repeats} | {max(0,args.seconds-elapsed):04.1f}s / {args.seconds:g}s'
                    update();frames+=1
                    if not evidence_requested and elapsed>0.3:
                        capture.capture_next_frame_swapchain(str(output/f'{scene}_take{lap}.png'))
                        evidence_requested=True
                    if elapsed>=args.seconds:break
                    time.sleep(1/120)
                item['laps'].append({'lap':lap,'seconds':time.monotonic()-start,'viewport_updates':frames,'completed':True})
                capture.wait_async_capture()
                save_json(output/'report.json',report)
            status.text=f'{source} | COMPLETE: {args.repeats} takes x {args.seconds:g}s'
            update();print('WORLDLAB_TOUR_SCENE_COMPLETE',scene,flush=True)
        report['status']='passed'
        report['completed_laps']=sum(len(scene['laps']) for scene in report['scenes'])
        report['actual_tour_seconds']=sum(lap['seconds'] for scene in report['scenes'] for lap in scene['laps'])
        save_json(output/'report.json',report)
        print('WORLDLAB_TOUR_COMPLETE',output/'report.json',flush=True)
        while app.is_running() and not args.exit_after:app.update()
    except Exception as exc:
        import traceback
        traceback.print_exc();report['status']='failed';report['error']=repr(exc)
        save_json(output/'report.json',report)
        raise
    finally:
        app.close(exit_code=0 if report['status']=='passed' else 1)


if __name__=='__main__':main()
