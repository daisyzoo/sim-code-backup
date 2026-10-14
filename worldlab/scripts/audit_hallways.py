#!/usr/bin/env python3
"""Read-only source audit; does not build USD or assert runtime readiness."""
from pathlib import Path
import gzip
import importlib.metadata
import json
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from worldlab.assets import digest, load_mesh, save_json, validate_splats
from usd_convert_gsplat import read_spz


def main():
    report = {'scope': 'CPU source audit only; no Isaac Sim runtime acceptance',
              'converter_version': importlib.metadata.version('usd-convert-gsplat'), 'assets': []}
    paths = sorted((ROOT / 'World/Environment').glob('hallway*/*'))
    for path in paths:
        if path.suffix not in ('.spz', '.glb', '.blend'):
            continue
        info = {'path': str(path.relative_to(ROOT)), 'bytes': path.stat().st_size,
                'sha256': digest(path)}
        if path.suffix == '.spz':
            with gzip.open(path, 'rb') as stream:
                magic, version, count, degree, fractional, flags, reserved = struct.unpack('<IIIBBBB', stream.read(16))
            if magic != 0x5053474e or version not in (2, 3):
                raise ValueError(f'Unsupported SPZ header: {path.name}')
            info['header'] = {'version': version, 'count': count, 'sh_degree': degree,
                              'fractional_bits': fractional, 'flags': flags}
            data = read_spz(str(path))
            info['decoded'] = validate_splats(data)
            del data
        elif path.suffix == '.glb':
            with path.open('rb') as stream:
                magic, version, length = struct.unpack('<III', stream.read(12))
                if magic != 0x46546c67 or version != 2 or length != path.stat().st_size:
                    raise ValueError(f'Invalid GLB header: {path.name}')
                size, chunk_type = struct.unpack('<II', stream.read(8))
                if chunk_type != 0x4e4f534a:
                    raise ValueError('Expected GLB JSON chunk')
                gltf = json.loads(stream.read(size))
            info['gltf'] = {key: len(gltf.get(key, [])) for key in ('nodes','meshes','materials','images','cameras')}
            info['extensions_used'] = gltf.get('extensionsUsed', [])
            info['node_names'] = [node.get('name') for node in gltf.get('nodes', [])]
            mesh = load_mesh(path)
            info['geometry'] = {'vertices': len(mesh.vertices), 'triangles': len(mesh.faces),
                                'bounds_with_node_transforms': mesh.bounds.tolist()}
        else:
            info['status'] = 'hashed only; Blender scene not opened'
        report['assets'].append(info)
    output = ROOT / 'outputs/source_audit/hallways.json'
    save_json(output, report)
    print(output)


if __name__ == '__main__':
    main()
