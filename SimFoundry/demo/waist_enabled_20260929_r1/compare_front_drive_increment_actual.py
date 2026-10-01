"""Compare complete front episodes under original quality gates and independent COP audits."""
from pathlib import Path
import collections,hashlib,json,sys
import numpy as np
w=Path(__file__).resolve().parent;ep=Path(sys.argv[1]).resolve();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert ep.name in ['layout_840001_nudge_mailer_to_bin','layout_840004_push_box_to_bin']
parent=w/'rear_core_slice_groups_r1'/ep.parent.name/ep.name
reports=[]
for folder in [parent,ep]:
 audit_name='FRONT_COP_LIVE_AUDIT.json' if folder==parent else 'FRONT_DRIVE_INCREMENT_LIVE_AUDIT.json'
 audit=json.loads((folder/audit_name).read_text());assert audit['passed'] and not audit['errors'] and audit['enabled']
 for f,h in audit['source_sha256'].items():assert sha(folder/f)==h
 q=json.loads((folder/'quality.json').read_text());log=json.loads((folder/'frontal_bypass.json').read_text());rows=log['rows'];key='box' if 'push_box' in ep.name else 'mailer';other='mailer' if key=='box' else 'box';direction=-1 if key=='box' else 1
 with np.load(folder/'trace.npz') as z:xyz=z[key].astype(float)
 assert len(xyz)==q['frames']==1200
 independent={r['step'] for r in audit['records']};stages=[]
 for stage in ['front_x','lateral_y']:
  rr=[r for r in rows if r['route_stage']==stage];loaded=[r for r in rr if r['step'] in independent];axis=0 if stage=='front_x' else 1;sign=-1 if axis==0 else direction
  ds=[sign*(xyz[r['step']+1,axis]-xyz[r['step'],axis])*1000 for r in loaded if r['step']+1<len(xyz)]
  stages.append(dict(stage=stage,frames=len(rr),mode_counts=dict(collections.Counter(r['mode'] for r in rr)),audited_loaded_overrides=len(loaded),loaded_active_object_median_mm=float(np.median(ds)) if ds else None,loaded_active_object_sum_mm=sum(ds),stage_signed_y_sum_mm=sum(direction*(xyz[r['step']+1,1]-xyz[r['step'],1])*1000 for r in rr if r['step']+1<len(xyz))))
 exits=collections.Counter(('terminal_release' if rows[i]['mode']=='top_release' else rows[i].get('last_recontact_reason')) for i in range(1,len(rows)) if rows[i-1]['mode']=='top_push' and rows[i]['mode']!='top_push')
 first=next((r['step'] for r in rows if r['step'] in independent),None)
 reports.append(dict(run=folder.parent.parent.name,episode=folder.name,quality_passed=q['passed'],reasons=q['reasons'],progress_mm=q['metrics']['target_final_progress_m']*1000,minimum_final10_signed_y_mm=float(min(direction*xyz[-10:,1])*1000),non_target_max_xy_mm=q['metrics'][other+'_max_xy_m']*1000,declared_drive_step_m=log['plan']['front_cop_slip_following']['drive_step_m'],first_override_step=first,first_override_object_xyz=xyz[first].tolist() if first is not None else None,stages=stages,exit_counts=dict(exits),source_sha256={f:sha(folder/f) for f in ['quality.json','trace.npz','frontal_bypass.json',audit_name]}))
out=dict(rows=reports,checker_sha256=sha(Path(__file__)),training_ready=False,scope='Same complete front conditions vs closed core-slice parent; independent original/new COP audits required. Actual recorded loaded frames and object motion, not counterfactual dynamics. Single seeds may vary before first changed command. Original progress plus final10 zone, pose and full-group gates still required.')
(ep/'FRONT_DRIVE_INCREMENT_ACTUAL_COMPARISON.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
