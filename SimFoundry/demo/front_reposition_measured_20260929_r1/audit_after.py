#!/usr/bin/env python3
"""Audit physical component motion separately from unchanged sorting quality."""
import argparse,collections,hashlib,itertools,json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
protocol=json.loads((a.root/'PROTOCOL.json').read_text());rows=[]
sizes={'box':np.array([.14,.09,.045]),'mailer':np.array([.15,.145,.04])}
for layout in protocol['layouts']:
 lid=layout['layout_id'];case=a.root/f'case_{lid}'
 if not (case/'INTEGRITY.json').exists():continue
 for raw in sorted(case.glob('layout_*/raw.npz')):
  task=raw.parent.name.split('_',2)[2];target='box' if task=='push_box_to_bin' else 'mailer';other='mailer' if target=='box' else 'box'
  with np.load(raw) as z:
   meta=json.loads(str(z['collect_meta']));assert meta['layout']==json.loads(Path(layout['path']).read_text());assert meta['assist_frames']==0
   assert len(z['q'])==160 and np.abs(z['q'][0,12:]).max()<1e-4 and np.abs(z['action'][0,12:]).max()<1e-4 and np.all(z['action'][:,12]==0)
   maxstep=float(np.max(np.abs(np.diff(z['action'],axis=0))))
  control=json.loads((raw.parent/'expert_control.json').read_text())
  with np.load(raw.parent/'trace.npz') as trace,np.load(raw.parent/'parcel_orientation.npz') as ori:
   support={};tilt={}
   for key in ['box','mailer']:
    q=ori[key];xyz=trace[key];assert q.shape==(160,4) and xyz.shape==(160,3)
    assert np.isfinite(q).all() and np.max(np.abs(np.linalg.norm(q,axis=1)-1))<1e-4
    initial=np.array(meta[key+'_quat_xyzw']);assert min(np.linalg.norm(q[0]-initial),np.linalg.norm(q[0]+initial))<1e-6
    assert np.max(np.abs(xyz[0]-meta[key+'_xyz']))<1e-6
    rotation=Rotation.from_quat(q).as_matrix();local=np.array(list(itertools.product([-1,1],repeat=3)))*sizes[key]/2
    world=np.einsum('tij,kj->tki',rotation,local)+xyz[:,None,:]
    margins=np.stack([world[:,:,0]-.28,.88-world[:,:,0],world[:,:,1]+.75,.75-world[:,:,1]],axis=-1)
    support[key]=float(margins.min());tilt[key]=float(np.max(np.arccos(np.clip(rotation[:,2,2],-1,1))))
   t=trace[target];o=trace[other];dx=float(t[0,0]-t[-1,0]);yexc=float(np.max(np.abs(t[:,1]-t[0,1])));nontarget=float(np.max(np.linalg.norm(o[:,:2]-o[0,:2],axis=1)));stable=float(np.linalg.norm(t[-1,:2]-t[-10,:2]))
   retreat=[i for i,c in enumerate(control) if c['mode']=='retreat_x']
   palmstroke=None;commandstroke=None;anchor_error=None
   if retreat:
    first,last=retreat[0],retreat[-1];hand='palm_right' if target=='box' else 'palm_left'
    palmstroke=float(trace[hand][first,0]-trace[hand][last,0])
    commandstroke=float(control[first]['target_xyz'][0]-control[last]['target_xyz'][0])
    anchor_error=abs(float(control[first]['target_xyz'][0])-float(trace[hand][first,0]))
    if meta.get('front_reposition_measured_start'):
     anchor=float(control[first]['front_reposition_start_x'])
     assert anchor_error<1e-6 and abs(anchor-float(trace[hand][first,0]))<1e-6
     assert all(abs(float(control[i]['front_reposition_start_x'])-anchor)<1e-8 for i in retreat)
     if len(retreat)==58:assert abs(commandstroke-meta['front_reposition_distance'])<1e-6
  applies=bool(meta['front_reposition_distance']);q=json.loads((raw.parent/'quality.json').read_text());assert not q['training_ready']
  metrics=dict(actual_palm_retreat_m=palmstroke,commanded_palm_retreat_m=commandstroke,initial_palm_anchor_error_m=anchor_error,frontward_progress_m=dx,max_target_y_excursion_m=yexc,non_target_max_xy_m=nontarget,last10_xy_displacement_m=stable,footprint_table_min_margin_m=support,max_tilt_from_upright_rad=tilt,max_action_step_rad=maxstep)
  checks=dict(frontward20mm=dx>=.02,y_excursion20mm=yexc<=.02,non_target15mm=nontarget<=.015,stable10mm=stable<=.01,complete_footprint_support=min(support.values())>=0,action08=maxstep<=.08)
  if meta.get('front_reposition_measured_start'):
   checks['actual_palm_retreat20mm']=palmstroke is not None and palmstroke>=.02
  # Keep every original non-zone quality failure as a component failure too.
  other_reasons=[x for x in q['reasons'] if x!='target did not finish stably beyond +/-0.20 m with >=0.15 m progress']
  checks['original_non_zone_gates']=not other_reasons
  row=dict(layout_id=lid,task=task,primitive_applies=applies,raw_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),orientation_sha256=hashlib.sha256((raw.parent/'parcel_orientation.npz').read_bytes()).hexdigest(),sorting_passed=q['passed'],sorting_reasons=q['reasons'],metrics=metrics,component_checks=checks,numeric_component_passed=applies and all(checks.values()),modes=dict(collections.Counter(c['mode'] for c in json.loads((raw.parent/'expert_control.json').read_text()))));rows.append(row)
  print(lid,task,'primitive',applies,'component',row['numeric_component_passed'],'dx',dx,'mode',row['modes'],flush=True)
a.out.write_text(json.dumps(dict(rows=rows,scope='Component-only diagnostic. Both original sorting pass/fail and component predicates retained. Pre-action orientation aligns to meta at first frame and trace by collector ordering, not an independent per-frame synchronization measurement. Full 3D nominal parcel box corners used for projected tabletop support; not contact-force measurement.',training_ready=False,goal_complete=False),indent=2))
