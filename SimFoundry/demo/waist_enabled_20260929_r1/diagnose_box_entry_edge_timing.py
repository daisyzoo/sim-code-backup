"""Existing10mm trigger timing versus actual tilt exits; not new policy validation."""
from pathlib import Path
import json,hashlib,datetime
import numpy as np
w=Path(__file__).resolve().parent;r=w/'box_entry_lift_groups_r1';ep=r/'case_840001/layout_840001_push_box_to_bin';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();wr=json.loads((r/'FIVE_VARIANT_BOX_CONTACT_WRENCH_DIAGNOSTIC.json').read_text());bouts=next(x for x in wr['episodes'] if x['run']==r.name)['bouts'];fr=json.loads((ep/'frontal_bypass.json').read_text());fs={f['step']:f for f in fr['rows']};size=np.array(fr['plan']['region_causal_response']['actual_core']['collision_core_size_xyz']);rows=[]
for b in bouts:
 if b['exit_reason']!='incipient_tilt_independent':continue
 loaded=[x for x in b['last8'] if 'hand_cop_local_mm' in x];last=loaded[-1];m=size[:2]/2-np.abs(np.array(last['hand_cop_local_mm'])[:2]/1000)
 rows.append(dict(exit_step=b['exit_step'],last_loaded_step=last['step'],last_local_xy_margin_mm=(m*1000).tolist(),last8_loaded_frames=len(loaded),last8_joint_feedback=[dict(step=x['step'],margin_mm=((size[:2]/2-np.abs(np.array(x['hand_cop_local_mm'])[:2]/1000))*1000).tolist(),reason=fs[x['step']].get('rear_joint_xy_progress',{}).get('reason'),override=fs[x['step']].get('rear_joint_xy_progress',{}).get('override')) for x in loaded]))
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,core_size_m=size.tolist(),trigger_inset_m=.010,rows=rows,source_sha256={str(p):sha(p) for p in [Path(__file__),ep/'frontal_bypass.json',r/'FIVE_VARIANT_BOX_CONTACT_WRENCH_DIAGNOSTIC.json',w/'staged_box_entry_lift/rear_joint_xy_progress.py',w/'staged_box_entry_lift/rear_coupled_progress.py']},training_ready=False);(r/'EDGE_FEEDBACK_TIMING_DIAGNOSTIC.json').write_text(json.dumps(out,indent=2))
for x in rows:print('tilt',x['exit_step'],'last_margin_mm',x['last_local_xy_margin_mm'],'last8_overrides',sum(y['override'] is True for y in x['last8_joint_feedback']),'reasons',sorted(set(y['reason'] for y in x['last8_joint_feedback'])))
