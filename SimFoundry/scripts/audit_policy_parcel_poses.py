#!/usr/bin/env python3
"""Supplement original policy quality with recorded all-frame footprint/tilt checks.

Never replaces original quality or actual image review. Wait parcels are hidden,
so their table footprint is not applicable. Missing push poses fail this audit.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation


def pose_metrics(xyz, quat, size):
    xyz, quat = np.asarray(xyz), np.asarray(quat)
    if xyz.ndim != 2 or xyz.shape[1] != 3 or quat.shape != (len(xyz), 4) or not len(xyz):
        raise ValueError('Pose shape mismatch')
    if not np.isfinite(xyz).all() or not np.isfinite(quat).all() or np.max(np.abs(np.linalg.norm(quat, axis=-1)-1)) > 1e-4:
        raise ValueError('Invalid pose values')
    rot = Rotation.from_quat(quat).as_matrix()
    corners = np.asarray(list(itertools.product([-1, 1], repeat=3))) * np.asarray(size)/2
    points = np.einsum('tij,kj->tki', rot, corners) + xyz[:, None, :]
    margins = np.stack([points[..., 0]-.28, .88-points[..., 0], points[..., 1]+.75, .75-points[..., 1]], axis=-1).min(axis=(1, 2))
    tilts = np.arccos(np.clip(rot[:, 2, 2], -1, 1))
    return dict(support=bool(np.all(margins >= 0)), upright=bool(np.all(tilts <= .20)),
                min_margin_m=float(margins.min()), max_tilt_rad=float(tilts.max()),
                peak_tilt_frame=int(tilts.argmax()), minimum_margin_frame=int(margins.argmin()),
                outside_footprint_frames=np.flatnonzero(margins < 0).tolist(),
                over_tilt_frames=np.flatnonzero(tilts > .20).tolist(), frames=len(xyz))


def main():
    p=argparse.ArgumentParser();p.add_argument('--summary',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():raise FileExistsError(a.out)
    report=json.loads(a.summary.read_text());rows=[]
    for row in report['rows']:
        folder=Path(row['path']);quality=json.loads((folder/'quality.json').read_text())
        if quality['passed']!=row['passed']:raise ValueError('Summary differs from saved quality')
        entry={k:row[k] for k in ['seed','layout_id','task','path']}
        entry.update(original_numeric_passed=quality['passed'])
        if row['task']=='wait_no_package':
            entry.update(pose_gate_applicable=False,reason='Parcels hidden during empty-table wait',combined_numeric_passed=quality['passed'])
        else:
            with np.load(folder/'parcel_orientation.npz') as ori, np.load(folder/'trace.npz') as trace:
                metrics={k:pose_metrics(trace[k],ori[k],sz) for k,sz in [('box',[.14,.09,.045]),('mailer',[.15,.145,.04])]}
            if any(m['frames']!=quality['frames'] for m in metrics.values()):raise ValueError('Pose frame coverage mismatch')
            entry.update(pose_gate_applicable=True,objects=metrics,combined_numeric_passed=bool(quality['passed'] and all(m['support'] and m['upright'] for m in metrics.values())),source_sha256={n:hashlib.sha256((folder/n).read_bytes()).hexdigest() for n in ['raw.npz','trace.npz','parcel_orientation.npz','quality.json']})
        rows.append(entry)
    a.out.write_text(json.dumps(dict(rows=rows,total=len(rows),original_numeric_pass=sum(r['original_numeric_passed'] for r in rows),combined_numeric_pass=sum(r['combined_numeric_passed'] for r in rows),summary_sha256=hashlib.sha256(a.summary.read_bytes()).hexdigest(),scope='All recorded pre-action parcel poses, nominal cuboid footprint and .20 rad tilt; original quality unchanged. Not contact force proof or actual visual review.',visual_review='pending',goal_complete=False),indent=2))
    print('Pose audit:',len(rows),'episodes;',sum(r['combined_numeric_passed'] for r in rows),'combined numeric passes')

if __name__=='__main__':main()
