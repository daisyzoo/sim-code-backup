#!/usr/bin/env python3
"""Material-preserving GLB conversion in the pinned Isaac Sim process."""
import argparse
import asyncio
import importlib.metadata
import json
import hashlib
import os
from pathlib import Path
import sys

p = argparse.ArgumentParser()
p.add_argument('source'); p.add_argument('destination')
args = p.parse_args()
source, destination = Path(args.source).resolve(), Path(args.destination).resolve()
destination.parent.mkdir(parents=True, exist_ok=True)
assert importlib.metadata.version('isaacsim') == '6.1.0.0'
os.environ['OMNI_KIT_ACCEPT_EULA'] = 'YES'
sys.argv = [sys.argv[0], '--/renderer/multiGpu/enabled=false']
from isaacsim import SimulationApp
app = SimulationApp({'headless': True, 'multi_gpu': False})
success = False
try:
    from isaacsim.core.utils.extensions import enable_extension
    enable_extension('omni.kit.asset_converter')
    import omni.kit.asset_converter as converter
    context = converter.AssetConverterContext()
    context.ignore_materials = False
    context.ignore_camera = False
    context.single_mesh = False
    context.merge_all_meshes = False
    context.export_preview_surface = True
    context.use_meter_as_world_unit = True
    context.convert_stage_up_z = True
    async def convert():
        task = converter.get_instance().create_converter_task(str(source), str(destination), None, context)
        if not await task.wait_until_finished():
            raise RuntimeError(task.get_error_message())
    future = asyncio.ensure_future(convert())
    while not future.done():
        app.update()
    future.result()
    from pxr import Usd, UsdGeom, UsdShade
    stage = Usd.Stage.Open(str(destination))
    report = {'source': str(source), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'isaacsim': '6.1.0.0', 'up_axis': str(UsdGeom.GetStageUpAxis(stage)),
              'meters_per_unit': UsdGeom.GetStageMetersPerUnit(stage),
              'default_prim': str(stage.GetDefaultPrim().GetPath()),
              'meshes': sum(x.IsA(UsdGeom.Mesh) for x in stage.Traverse()),
              'materials': sum(x.IsA(UsdShade.Material) for x in stage.Traverse()),
              'cameras': sum(x.IsA(UsdGeom.Camera) for x in stage.Traverse()), 'context': context.to_dict()}
    (destination.parent/'conversion.json').write_text(json.dumps(report, indent=2)+'\n')
    print('WORLDLAB_CONVERTED', json.dumps(report), flush=True)
    success = True
finally:
    app.close(exit_code=0 if success else 1)
