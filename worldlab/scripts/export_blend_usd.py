#!/usr/bin/env python3
"""Run inside a separate Blender process; never save or overwrite the source BLEND.

blender --background --factory-startup --disable-autoexec --python-exit-code 1 \
    --python scripts/export_blend_usd.py -- --source World/Environment/hallway2/hallway.blend \
    --output generated/hallway2_blend/imported
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import tempfile

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def portable_floor_materials():
    """Evaluate this asset's image × constant nodes into portable PNG images.

    This is deliberately a narrow adapter, not a general Blender shader baker.
    It preserves the original packed image's linear RGB and its UV mapping.
    All edits exist only in the disposable Blender process.
    """
    baked = []
    for material in bpy.data.materials:
        if not material.node_tree:
            continue
        tree = material.node_tree
        bsdf = next((n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if bsdf is None or not bsdf.inputs['Base Color'].is_linked:
            continue
        node = bsdf.inputs['Base Color'].links[0].from_node
        if node.type != 'MIX_RGB':
            continue
        if (node.blend_type != 'MULTIPLY' or node.inputs[0].is_linked
                or node.inputs[0].default_value != 1 or node.inputs[2].is_linked
                or not node.inputs[1].is_linked):
            raise ValueError(f'Unsupported material network: {material.name}')
        texture = node.inputs[1].links[0].from_node
        if texture.type != 'TEX_IMAGE' or texture.image is None:
            raise ValueError(f'Expected packed image in {material.name}')
        original = texture.image
        pixels = np.empty(len(original.pixels), dtype=np.float32)
        original.pixels.foreach_get(pixels)
        rgba = pixels.reshape(-1, 4)
        factor = list(node.inputs[2].default_value)[:3]
        rgba[:, :3] *= factor
        image = bpy.data.images.new(material.name.replace(' ', '_') + '_baked',
                                    width=original.size[0], height=original.size[1], alpha=True)
        image.colorspace_settings.name = original.colorspace_settings.name
        image.pixels.foreach_set(rgba.ravel())
        image.pack()
        portable = tree.nodes.new('ShaderNodeTexImage')
        portable.image = image
        portable.extension = texture.extension
        portable.interpolation = texture.interpolation
        if texture.inputs['Vector'].is_linked:
            tree.links.new(texture.inputs['Vector'].links[0].from_socket, portable.inputs['Vector'])
        tree.links.new(portable.outputs['Color'], bsdf.inputs['Base Color'])
        baked.append({'material': material.name, 'operation': 'linear RGB image * constant',
                      'factor': factor, 'source_image': original.name, 'output_image': image.name})
    return baked


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    source = Path(args.source).resolve()
    output = Path(args.output).resolve()
    if not source.is_relative_to(ROOT/'World') or source.suffix.lower() != '.blend':
        raise ValueError('Source must be a BLEND asset inside World/')
    if not output.is_relative_to(ROOT/'generated') or output.exists():
        raise ValueError('Output must be a NEW directory inside generated/')
    before = digest(source)
    bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
    if bpy.app.version < (5, 2, 0):
        raise RuntimeError('Use Blender 5.2 or later for this source data version')
    inventory = [{'name': o.name, 'type': o.type, 'hide_render': o.hide_render,
                  'modifiers': [m.type for m in o.modifiers]} for o in bpy.context.scene.objects]
    baked = portable_floor_materials()
    output.parent.mkdir(parents=True, exist_ok=True)
    options = dict(check_existing=False, selected_objects_only=False, export_animation=False,
                   export_uvmaps=True, rename_uvmaps=True, export_normals=True,
                   export_materials=True, generate_preview_surface=True,
                   generate_materialx_network=False, export_textures_mode='NEW',
                   relative_paths=True, export_lights=True, export_cameras=True,
                   export_meshes=True, export_subdivision='TESSELLATE', evaluation_mode='RENDER',
                   convert_orientation=False, convert_scene_units='METERS',
                   root_prim_path='/BlendScene', convert_world_material=False,
                   allow_unicode=False, triangulate_meshes=True)
    # Publish only after the complete export and audits succeed.
    with tempfile.TemporaryDirectory(prefix='.blend-export-', dir=output.parent) as temp:
        destination = Path(temp)/'imported'
        destination.mkdir()
        result = bpy.ops.wm.usd_export(filepath=str(destination/'visual.usdc'), **options)
        if result != {'FINISHED'}:
            raise RuntimeError(f'USD export failed: {result}')
        from pxr import Usd, UsdGeom, UsdShade, UsdLux, Sdf, Gf, Tf
        stage = Usd.Stage.Open(str(destination/'visual.usdc'))
        # Blender's exporter omits orthographic cameras. Preserve this source's
        # cutaway camera explicitly, with its original frame and world transform.
        cameras = [o for o in bpy.context.scene.objects if o.type == 'CAMERA']
        orthographic = [o for o in cameras if o.data.type == 'ORTHO']
        exported_cameras = sum(p.IsA(UsdGeom.Camera) for p in stage.Traverse())
        restored_cameras = []
        if exported_cameras != len(cameras) and exported_cameras + len(orthographic) == len(cameras):
            for obj in orthographic:
                camera = UsdGeom.Camera.Define(stage, '/BlendScene/SourceOrthographicCameras/' + Tf.MakeValidIdentifier(obj.name))
                frame = obj.data.view_frame(scene=bpy.context.scene)
                camera.CreateProjectionAttr('orthographic')
                camera.CreateHorizontalApertureAttr(10*(max(v.x for v in frame)-min(v.x for v in frame)))
                camera.CreateVerticalApertureAttr(10*(max(v.y for v in frame)-min(v.y for v in frame)))
                camera.CreateClippingRangeAttr(Gf.Vec2f(obj.data.clip_start, obj.data.clip_end))
                matrix = obj.matrix_world.transposed()
                camera.AddTransformOp().Set(Gf.Matrix4d(*[float(x) for row in matrix for x in row]))
                restored_cameras.append(obj.name)
            stage.GetRootLayer().Save()
        counts = {'meshes': sum(p.IsA(UsdGeom.Mesh) for p in stage.Traverse()),
                  'materials': sum(p.IsA(UsdShade.Material) for p in stage.Traverse()),
                  'cameras': sum(p.IsA(UsdGeom.Camera) for p in stage.Traverse()),
                  'lights': sum(p.HasAPI(UsdLux.LightAPI) for p in stage.Traverse())}
        source_counts = dict(Counter(o['type'] for o in inventory))
        if counts['meshes'] != source_counts.get('MESH') or counts['cameras'] != source_counts.get('CAMERA'):
            raise RuntimeError(f'Lost source objects: {source_counts} -> {counts}')
        if str(UsdGeom.GetStageUpAxis(stage)) != 'Z' or UsdGeom.GetStageMetersPerUnit(stage) != 1:
            raise RuntimeError('Expected Z-up / meters from Blender export')
        textures = set()
        for prim in stage.Traverse():
            for attr in prim.GetAttributes():
                if attr.GetTypeName() == Sdf.ValueTypeNames.Asset:
                    value = attr.Get()
                    if value and value.path:
                        if Path(value.path).is_absolute() or not value.resolvedPath or not Path(value.resolvedPath).is_file():
                            raise RuntimeError(f'Nonportable or missing asset: {value}')
                        textures.add(value.path)
        if not textures or not stage.GetDefaultPrim():
            raise RuntimeError('Missing portable textures or default prim')
        if digest(source) != before:
            raise RuntimeError('Source was unexpectedly modified')
        report = {'route': 'BLEND -> Blender USD exporter -> USDC; no GLB intermediate',
                  'source': str(source.relative_to(ROOT)), 'source_sha256': before,
                  'source_unchanged': True, 'blender': bpy.app.version_string,
                  'exporter_sha256': digest(__file__), 'options': options,
                  'source_counts': source_counts, 'source_inventory': inventory,
                  'orthographic_cameras_restored': restored_cameras,
                  'baked_materials': baked, 'counts': counts, 'textures': sorted(textures),
                  'up_axis': 'Z', 'meters_per_unit': 1,
                  'default_prim': str(stage.GetDefaultPrim().GetPath()),
                  'output_sha256': {str(p.relative_to(destination)): digest(p)
                                    for p in destination.rglob('*') if p.is_file()}}
        (destination/'conversion.json').write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n')
        stage = None
        destination.rename(output)
    print('WORLDLAB_BLEND_EXPORTED', output, counts, flush=True)


if __name__ == '__main__':
    main()
