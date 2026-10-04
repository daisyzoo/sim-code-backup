"""Complete independent window force/geometry/loss lifecycle stream audit.
Original source, substep sequence and pressure/route/planner/final-command audits
remain required; this adds the window-specific stream, never replaces the224.
"""
from pathlib import Path
import sys,json,hashlib,datetime
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_contact_window_v2';sys.path[:0]=[str(S),str(W),str(ROOT)]
from front_contact_window_stage_source_binding_v2 import verify_observation_binding
from front_contact_window_observation_audit_v1 import force_interval,verify_interval
from front_contact_window_loss_lifecycle_v2 import verify_stream
from audit_substep_contacts import verify_arrays
from clearance_runtime import ClearanceGuard
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def inspect(episode):
 ep=Path(episode).resolve();binding=verify_observation_binding(ep);sources=dict(binding['source_sha256'])
 def read(p):sources[str(p)]=sha(p);return json.loads(p.read_text())
 def arrays(p,keys=None):
  sources[str(p)]=sha(p)
  with np.load(p,allow_pickle=False) as z:return {k:z[k].copy() for k in (z.files if keys is None else keys)}
 provenance=read(ep.parent/'provenance.json');args=provenance['args'];selected=binding['window_structure']['selected_front'];out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episode=ep.name,enabled=args['front_contact_window'],selected_front=selected,training_ready=False)
 if selected:
  raw=arrays(ep/'raw.npz',['q','task_id']);n=len(raw['q']);side,key,other,actor=('right','box','mailer','parcel_box') if str(raw['task_id'])=='push_box_to_bin' else ('left','mailer','box','mailer')
  fr=read(ep/'frontal_bypass.json');rowmap={r['step']:r for r in fr['rows']};trace=arrays(ep/'trace.npz',[key]);ori=arrays(ep/'parcel_orientation.npz',[key]);record=read(ep/'SUBSTEP_CONTACT_RECORDING.json');assert record['recording_sha256']==sha(ep/'substep_contacts.npz');substeps=arrays(ep/'substep_contacts.npz');packets=read(ep/'solved_contact_forces.json')['rows'];substep_proof=verify_arrays(substeps,record,packets,n)
  log=read(ep/'front_contact_window.json');intervals={r['step']:r for r in log['rows']};assert len(intervals)==len(log['rows'])==n-1
  mesh=read(ROOT/'assets/robots/g1_hand_support_vertices.json');asset=ROOT/mesh['source_path'];assert sha(asset)==mesh['source_sha256'];sources[str(asset)]=sha(asset)
  guard=ClearanceGuard(ROOT,S);core=fr['plan']['front_cop_slip_following']['edge_speed']['actual_core_size_xyz'];observations=[];loads={};additional={}
  for t in range(1,n):
   i=intervals[t];assert rowmap[t]['contact_window_interval']=={k:v for k,v in i.items() if k!='step'}
   values,load=force_interval(substeps,record['metadata'],packets[t-1],t,side,actor);T,_,_=guard.model.fk(side,raw['q'][t,12:23]);r=verify_interval(interval=i,step=t,values=values,current=load,target_xyz=trace[key][t],target_quat=ori[key][t],core=core,vertices=mesh['vertices'][side],fk_pose=T,original_row=rowmap[t]);observations.append(r);loads[t]=load;additional[t]=r['additional']
  pressure={r['action_step']:r for r in read(ep/'peak_load_updates.json')['rows']};initial={r['step']:r for r in read(ep/'front_initial_center.json')['rows']};recovery={r['step']:r for r in read(ep/'front_recontact_center.json')['rows']}
  history=verify_stream(rows=fr['rows'],pressure=pressure,initial=initial,recovery=recovery,xyz=trace[key],quats=ori[key],loads=loads,args=args,plan=fr['plan'],intervals=intervals,additional=additional)
  out.update(frames=n,intervals=len(observations),additional_loss_observations=sum(r['additional_contact'] for r in history),substep_proof=substep_proof,observations=observations,loss_lifecycle=history)
 for module in list(sys.modules.values()):
  p=getattr(module,'__file__',None)
  if p:
   p=Path(p).resolve()
   if p.is_file() and p.suffix=='.py' and p.is_relative_to(ROOT):sources[str(p)]=sha(p)
 sources[str(Path(__file__))]=sha(__file__)
 out.update(source_sha256=sources,original_full_audit_family_required=True,task_success_proven=False,training_admission=False)
 return out

if __name__=='__main__':
 ep=Path(sys.argv[1]);report=inspect(ep)
 with (ep/'FRONT_CONTACT_WINDOW_STREAM_AUDIT_V1.json').open('x') as f:json.dump(report,f,indent=2)
 print(json.dumps({k:v for k,v in report.items() if k not in ['source_sha256','observations','loss_lifecycle','scope']}))
