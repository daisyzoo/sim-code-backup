"""Scene registry, cached source conversion and layered USD assembly (CPU)."""
from pathlib import Path
import importlib.metadata
import json
import os
import hashlib
from .assets import ROOT, digest, save_json, validate_splats, load_mesh, convert_collider, look_at


def config_path(scene):
    if scene not in ('hallway1_elegant', 'hallway1_modern', 'hallway2', 'hallway2_blend'):
        raise ValueError(f'Unknown scene: {scene}')
    return ROOT / 'configs/scenes' / f'{scene}.json'


def load_scene(scene):
    cfg = json.loads(config_path(scene).read_text())
    if cfg['source_to_world'] is None:
        raise ValueError('Scene alignment is not configured')
    for source in cfg['sources'].values():
        path = (ROOT / source).resolve()
        if not path.is_relative_to(ROOT / 'World') or not path.is_file():
            raise ValueError(f'Invalid source path: {source}')
    return cfg


def set_transform(prim, transform):
    from pxr import Gf, UsdGeom
    xf = UsdGeom.Xformable(prim)
    xf.AddTranslateOp().Set(Gf.Vec3d(*transform['translate']))
    xf.AddRotateXYZOp().Set(Gf.Vec3f(*transform['rotate_xyz_deg']))
    xf.AddScaleOp().Set(Gf.Vec3f(transform.get('scale', 1)))


def build_scene(scene):
    from pxr import Gf, Usd, UsdGeom, UsdLux, UsdPhysics, UsdShade
    cfg = load_scene(scene)
    base = ROOT / 'generated' / scene
    base.mkdir(parents=True, exist_ok=True)
    hashes = {key: digest(ROOT / value) for key, value in cfg['sources'].items()}
    versions = {'usd': importlib.metadata.version('usd-core'), 'gsplat': importlib.metadata.version('usd-convert-gsplat')}
    converter_code = {name: digest(ROOT / name) for name in ('src/worldlab/scenes.py', 'src/worldlab/assets.py', 'scripts/convert_gltf.py')}
    if Path(cfg['sources']['visual']).suffix.lower() == '.blend':
        converter_code['scripts/export_blend_usd.py'] = digest(ROOT/'scripts/export_blend_usd.py')
    fingerprint = {'config': cfg, 'sources': hashes, 'tools': versions, 'code': converter_code}
    build_id = hashlib.sha256(json.dumps(fingerprint, sort_keys=True).encode()).hexdigest()[:12]
    output = base / build_id
    output.mkdir(exist_ok=True)
    if cfg['representation'] == 'gaussian_static':
        from usd_convert_gsplat import read_spz, write_gaussian_splat_usd
        cache_key = hashlib.sha256(json.dumps([hashes, versions, digest(ROOT/'src/worldlab/assets.py')],sort_keys=True).encode()).hexdigest()[:12]
        cache = base / 'assets' / cache_key
        cache.mkdir(parents=True, exist_ok=True)
        visual = cache/'visual.usdc'; collision = cache/'collision.usdc'
        cache_manifest = cache/'manifest.json'
        cached = json.loads(cache_manifest.read_text()) if cache_manifest.exists() else {}
        if not all(p.exists() and digest(p) == cached.get(p.name) for p in (visual, collision)):
            cache_manifest.unlink(missing_ok=True)
            data = read_spz(str(ROOT/cfg['sources']['visual']))
            audit = validate_splats(data)
            write_gaussian_splat_usd(data, str(visual), source_file=cfg['sources']['visual'], prim_name='Visual', up_axis='Y')
            del data
            convert_collider(load_mesh(ROOT/cfg['sources']['collision']), collision)
            save_json(cache/'audit.json', audit)
            save_json(cache_manifest, {p.name:digest(p) for p in (visual,collision)})
    else:
        visual = base/'imported/visual.usdc'
        if not visual.exists():
            raise FileNotFoundError('Import the scene visual first: convert_gltf.py for GLB or export_blend_usd.py with Blender for BLEND')
        collision = None
        conversion = json.loads((visual.parent/'conversion.json').read_text())
        if conversion.get('source_sha256') != hashes['visual']:
            raise RuntimeError('Visual conversion source changed or unverified; re-import the source')
        if Path(cfg['sources']['visual']).suffix.lower() == '.blend':
            if conversion.get('exporter_sha256') != converter_code['scripts/export_blend_usd.py']:
                raise RuntimeError('Blender exporter changed; export into a fresh import directory before building')
    geometry = Usd.Stage.CreateNew(str(output/'geometry.usda'))
    UsdGeom.Xform.Define(geometry,'/World')
    env = UsdGeom.Xform.Define(geometry,'/World/Environment')
    set_transform(env.GetPrim(),cfg['source_to_world'])
    geom = geometry.DefinePrim('/World/Environment/Visual')
    geom.GetReferences().AddReference(os.path.relpath(visual,output))
    if collision:
        col = geometry.DefinePrim('/World/Environment/Collision')
        col.GetReferences().AddReference(os.path.relpath(collision,output))
        UsdGeom.Imageable(col).CreateVisibilityAttr().Set('invisible')
    geometry.GetRootLayer().Save()
    # Separate physics opinions from appearance. Mesh GLB binds physics to original meshes.
    physics = Usd.Stage.CreateNew(str(output/'physics.usda'))
    targets = []
    for prim in geometry.Traverse():
        if not prim.IsA(UsdGeom.Mesh):
            continue
        if collision and not str(prim.GetPath()).startswith('/World/Environment/Collision/'):
            continue
        if not collision:
            name = str(prim.GetPath()).lower()
            if not any(token in name for token in ('wall','floor','tread','winder','threshold','leaf','ceiling','handrail','balustr','newel','landing')):
                continue
        override = physics.OverridePrim(prim.GetPath())
        UsdPhysics.CollisionAPI.Apply(override).CreateCollisionEnabledAttr(True)
        UsdPhysics.MeshCollisionAPI.Apply(override).CreateApproximationAttr('none')
        targets.append(str(prim.GetPath()))
    if not targets:
        raise RuntimeError('No collision meshes selected')
    ps=UsdPhysics.Scene.Define(physics,'/World/PhysicsScene')
    ps.CreateGravityDirectionAttr(Gf.Vec3f(0,0,-1));ps.CreateGravityMagnitudeAttr(9.81)
    physics.GetRootLayer().Save()
    lighting = Usd.Stage.CreateNew(str(output/'lighting.usda'))
    dome=UsdLux.DomeLight.Define(lighting,'/World/Lighting/Dome');dome.CreateIntensityAttr(cfg['lighting']['dome'])
    for i,light in enumerate(cfg['lighting'].get('spheres',[])):
        lt=UsdLux.SphereLight.Define(lighting,f'/World/Lighting/Fill_{i}')
        lt.CreateRadiusAttr(light.get('radius',0.12));lt.CreateIntensityAttr(light['intensity'])
        lt.CreateColorAttr(Gf.Vec3f(1,0.95,0.88));lt.AddTranslateOp().Set(Gf.Vec3d(*light['position']))
    lighting.GetRootLayer().Save()
    cameras=Usd.Stage.CreateNew(str(output/'cameras.usda'))
    for name,pose in cfg['cameras'].items():
        cam=UsdGeom.Camera.Define(cameras,f'/World/Cameras/{name}')
        cam.CreateFocalLengthAttr(pose.get('focal_length',18));cam.CreateHorizontalApertureAttr(36)
        cam.CreateVerticalApertureAttr(20.25);cam.CreateClippingRangeAttr(Gf.Vec2f(0.03,100))
        look_at(cam,pose['eye'],pose['target'])
    cameras.GetRootLayer().Save()
    stage=Usd.Stage.CreateNew(str(output/'scene.usda'))
    stage.GetRootLayer().subLayerPaths=['physics.usda','cameras.usda','lighting.usda','geometry.usda']
    stage.SetDefaultPrim(stage.GetPrimAtPath('/World'))
    UsdGeom.SetStageUpAxis(stage,'Z');UsdGeom.SetStageMetersPerUnit(stage,1)
    stage.SetTimeCodesPerSecond(60);stage.SetStartTimeCode(0);stage.SetEndTimeCode(36000)
    stage.GetRootLayer().customLayerData={'scene_id':scene,'scale_status':cfg['scale_status']}
    stage.GetRootLayer().Save()
    assets=[visual]+([collision] if collision else [])
    if not collision:
        assets.extend(p for p in visual.parent.rglob('*') if p.is_file() and p != visual)
    files={str(p.relative_to(ROOT)):digest(p) for p in assets+list(output.glob('*.usda'))}
    fingerprint.update({'scene':scene,'build_id':build_id,'stage':str((output/'scene.usda').relative_to(ROOT)),
                        'collision_paths':targets,'output_sha256':files,'status':'built_not_runtime_validated'})
    save_json(output/'manifest.json',fingerprint)
    pointer=base/'current.json.tmp';save_json(pointer,{'stage':fingerprint['stage'],'manifest':str((output/'manifest.json').relative_to(ROOT))})
    pointer.replace(base/'current.json')
    print('WORLDLAB_BUILT',fingerprint['stage'], 'colliders',len(targets),flush=True)
    return fingerprint


def resolve_scene(scene):
    cfg=load_scene(scene)
    pointer=json.loads((ROOT/'generated'/scene/'current.json').read_text())
    manifest=json.loads((ROOT/pointer['manifest']).read_text())
    if manifest['config'] != cfg:
        raise RuntimeError('Configuration changed; rebuild scene before running')
    for source,expected in manifest['sources'].items():
        if digest(ROOT/cfg['sources'][source]) != expected:
            raise RuntimeError('Source changed; rebuild scene before running')
    for path,expected in manifest['output_sha256'].items():
        if not (ROOT/path).exists() or digest(ROOT/path) != expected:
            raise RuntimeError(f'Generated dependency changed: {path}; rebuild scene')
    return cfg, ROOT/pointer['stage'], manifest
