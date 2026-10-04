"""Compare causal one-step predictions with actual next states and observed scenes.
Read-only diagnosis of a completed, source-bound physical episode. No solver,
no fitting, no continuation from an unexecuted command, no training admission.
Endpoint observations do not certify continuous physical paths or task success.
"""
from pathlib import Path
import argparse, collections, datetime, hashlib, importlib.util, json, sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--episode',required=True);ap.add_argument('--output',required=True);args=ap.parse_args()
 ep=Path(args.episode).resolve();out=Path(args.output).resolve();assert not out.exists();run=ep.parent.parent;sources={}
 def read(p):
  sources[str(p)]=sha(p);return json.loads(p.read_text())
 protocol=read(run/'PROTOCOL.json');ready=read(ep/'READY_FOR_AUDIT.json')
 assert ready['episode']==ep.name and not ready['wait'] and ready['executed_frames']==ready['requested_frames']==1200
 assert ready['training_ready'] is False
 for f,h in ready['source_sha256'].items():assert sha(f)==h,f
 stage=Path(protocol['plan']['collector']).parent
 for p in stage.glob('*.py'):assert protocol['frozen_files_sha256'][str(p)]==sha(p),p
 sys.path[:0]=[str(stage),str(W),str(ROOT)]
 spec=importlib.util.spec_from_file_location('diagnostic_joint_paths',stage/'joint_transport_paths.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 geometry=module.JointTransportPaths(ROOT,stage);labels=geometry.labels
 params=read(stage/'causal_response_parameters.json');records=read(ep/'joint_transport_clearance.json')['rows'];fr=read(ep/'frontal_bypass.json');front={x['step']:x for x in fr['rows']}
 with np.load(ep/'raw.npz',allow_pickle=False) as z:
  q=z['q'][:,12:23].astype(float);u=z['action'][:,12:23].astype(float);task=str(z['task_id'])
 sources[str(ep/'raw.npz')]=sha(ep/'raw.npz');assert q.shape==u.shape==(1200,11)
 assert [x['step'] for x in records]==list(range(1200));assert (q[0]==0).all() and (u[0]==0).all()
 decay=np.asarray(params['tasks'][task]['decay']);assert decay.shape==(11,)
 post={x['step']:x for x in read(ep/'self_clearance.json')['rows'] if x['phase']=='post'}
 rows=[]
 for t in range(1,len(q)-1):
  rec=records[t];ctx=rec['collector_context'];scene=ctx['scene'];nextscene=records[t+1]['collector_context']['scene']
  np.testing.assert_array_equal(ctx['current'],q[t]);np.testing.assert_array_equal(ctx['previous_q'],q[t-1]);np.testing.assert_array_equal(ctx['previous_command'],u[t-1]);np.testing.assert_array_equal(rec['output_command'],u[t]);np.testing.assert_allclose(post[t]['upper_q'],q[t+1],atol=1e-6,rtol=0)
  if not rec['selected']:continue
  np.testing.assert_array_equal(ctx['decay'],decay)
  bias=q[t]-u[t-1]-decay*(q[t-1]-u[t-1]);prediction=(1-decay)*u[t]+decay*q[t]+bias
  if rec['applied']:np.testing.assert_array_equal(rec['proposal']['predicted_q'],prediction)
  mm={name:(1000*geometry.margins(state,s)).tolist() for name,state,s in [('measured',q[t],scene),('predicted',prediction,scene),('actual_with_previous_scene',q[t+1],scene),('actual',q[t+1],nextscene)]}
  mm['prediction_minus_actual_same_scene']=(np.asarray(mm['predicted'])-np.asarray(mm['actual_with_previous_scene'])).tolist()
  mm['scene_motion_effect']=(np.asarray(mm['actual'])-np.asarray(mm['actual_with_previous_scene'])).tolist()
  failed=[labels[i] for i,x in enumerate(mm['actual']) if x<-.0002]
  rows.append(dict(step=t,mode=front[t]['mode'],applied=rec['applied'],reason=rec['reason'],proposal_reason=rec.get('proposal',{}).get('reason'),margins_mm=mm,actual_next_violations=failed,observed_load_n=front[t].get('contact_load',{}).get('observed_vertical_load_n')))
 stats={}
 for name,rs in [('all_selected',rows),('applied',[x for x in rows if x['applied']]),('parent_fallback',[x for x in rows if not x['applied']])]:
  stats[name]=dict(frames=len(rs),actual_violation_frames=sum(bool(x['actual_next_violations']) for x in rs),first_violation=next((x for x in rs if x['actual_next_violations']),None),minimum_actual_margin_mm={k:min(x['margins_mm']['actual'][i] for x in rs) for i,k in enumerate(labels)} if rs else {},maximum_optimistic_same_scene_error_mm={k:max(x['margins_mm']['prediction_minus_actual_same_scene'][i] for x in rs) for i,k in enumerate(labels)} if rs else {})
 for mod in list(sys.modules.values()):
  f=getattr(mod,'__file__',None)
  if f:
   p=Path(f).resolve()
   if p.is_file() and p.suffix=='.py' and p.is_relative_to(ROOT):sources[str(p)]=sha(p)
 for p in [Path(__file__),stage/'joint_transport_paths.py',ROOT/'assets/robots/g1_hand_support_vertices.json',ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf']:sources[str(p)]=sha(p)
 for f,h in ready['source_sha256'].items():assert sha(f)==h,f
 result=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episode=ep.name,physical_recorded_transitions=True,geometry_margin_labels=labels,frames=1200,selected_transitions=len(rows),reason_counts=dict(collections.Counter(x['reason'] for x in rows)),stats=stats,rows=rows,source_sha256=sources,training_ready=False,goal_complete=False)
 with out.open('x') as f:json.dump(result,f,indent=2)
 print(json.dumps({k:v for k,v in result.items() if k not in ['rows','source_sha256','scope']},indent=2))
if __name__=='__main__':main()
