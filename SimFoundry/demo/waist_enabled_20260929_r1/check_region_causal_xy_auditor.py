"""Audit helpers against all20 surrogate histories plus corruptions; no real-data claims."""
from pathlib import Path
import json,sys,copy,hashlib
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_region_causal_xy_response';sys.path[:0]=[str(w),str(stage),str(repo)]
from audit_region_causal_xy_live import verify_record,inspect_geometry
from causal_unloaded_response import response_parameters
from articulated_hand_geometry import ArticulatedHandGeometry
model=ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json');data=json.loads((w/'causal_xy_objective_screen_r1/RESULT.json').read_text());cases=[r for r in data['rows'] if r['variant']=='response_centered_xy_objective'];params=json.loads((stage/'causal_response_parameters.json').read_text());records=[];corruptions=0
for case in cases:
 ep=Path(case['episode']);t=case['actual_start_frame'];task='push_box_to_bin' if 'push_box' in ep.name else 'nudge_mailer_to_bin';key='box' if task=='push_box_to_bin' else 'mailer';side='right' if key=='box' else 'left';other='mailer' if key=='box' else 'box';size=np.array([.14,.09,.045] if key=='box' else [.15,.145,.04]);osize=(.15,.145,.04) if key=='box' else (.14,.09,.045);scale=np.array([.96,.96,1.] if key=='box' else [.90,.88,1.]);a=np.array(params['tasks'][task]['decay'])
 with np.load(ep/'raw.npz') as z:previous_q=z['q'][t-1,12:23].astype(float)
 with np.load(ep/'trace.npz') as z:target=z[key][t].astype(float);obstacle=z[other][t].astype(float)
 with np.load(ep/'parcel_orientation.npz') as z:quat=z[key][t];oquat=z[other][t]
 anchor=next(r['inactive_anchor'] for r in json.loads((ep/'coordination.json').read_text()) if r['step']==t);checked=0
 for h in case['history']:
  q=np.array(h['measured_q']);u0=np.array(h['previous_command']);gain,offset=response_parameters(q,previous_q,u0,a);record=dict(current_q=q.tolist(),previous_q=previous_q.tolist(),previous_command=u0.tolist(),decay=a.tolist(),gain=gain.tolist(),offset=offset.tolist(),core_scale=scale.tolist(),command_change_damping=True,response_centered_xy_objective=True);g,b,errors=verify_record(record,q,previous_q,u0,a,scale);assert not errors and np.max(abs(g-gain))<1e-14 and np.max(abs(b-offset))<1e-14
  cmd=np.array(h['solver']['next_q']);assert np.max(abs(cmd-u0))<=.055002
  if h['solver']['reached']:
   final=inspect_geometry(model,side,q,target,quat,obstacle,oquat,size,osize,scale,anchor);assert not final['errors'],(ep,final)
  else:
   for value in [cmd,g*cmd+b]:
    geometry=inspect_geometry(model,side,value,target,quat,obstacle,oquat,size,osize);assert not geometry['errors'],(ep,h['step'],geometry)
  checked+=1;previous_q=q
 # Every record field must be independently binding, including previous observation.
 for name in ['current_q','previous_q','previous_command','decay','gain','offset','core_scale']:
  bad=copy.deepcopy(record);bad[name][0]+=.001;assert verify_record(bad,q,np.array(record['previous_q']),u0,a,scale)[2],name;corruptions+=1
 for bad in [{},dict(record,response_centered_xy_objective=False),dict(record,command_change_damping=False),dict(record,previous_q=[float('nan')]*11)]:
  assert verify_record(bad,q,np.array(record['previous_q']),u0,a,scale)[2];corruptions+=1
 badq=q.copy();badq[0]=1.01;assert 'joint_bounds' in inspect_geometry(model,side,badq,target,quat,obstacle,oquat,size,osize)['errors'];corruptions+=1
 assert 'minimum_height' in inspect_geometry(model,side,q,target+np.array([0,0,.1]),quat,obstacle,oquat,size,osize)['errors'];corruptions+=1
 assert 'inside_region' in inspect_geometry(model,side,q,target,quat,obstacle,oquat,size,osize,scale*.5,anchor)['errors'];corruptions+=1
 records.append(dict(episode=str(ep),plant=case['plant'],history_steps=checked,core_handover=final))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();out=dict(passed=True,histories=records,steps_checked=sum(r['history_steps'] for r in records),corruptions_rejected=corruptions,source_sha256={str(p):sha(p) for p in [Path(__file__),w/'audit_region_causal_xy_live.py',w/'audit_region_causal_xy_continuity_live.py',w/'causal_xy_objective_screen_r1/RESULT.json',stage/'causal_unloaded_response.py',stage/'causal_response_parameters.json']},scope='Independent auditor record equations and raw FK guards exercised on all20 approximate histories, against actual response helper; perhistory14corruptions rejected. No fake episodes written, no new real physical success.',training_ready=False);(stage/'INDEPENDENT_AUDITOR_CHECK.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k not in ['histories','source_sha256']})
