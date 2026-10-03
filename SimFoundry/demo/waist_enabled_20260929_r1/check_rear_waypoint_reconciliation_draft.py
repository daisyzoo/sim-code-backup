"""Four actual histories, one post-commit proposal each; no chained replay.
Current action is unchanged, future changed dynamics are never claimed.
"""
from pathlib import Path
import sys,json,hashlib,datetime,importlib.util
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];draft=w/'rear_waypoint_reconciliation_draft_r1';sys.path[:0]=[str(draft),str(repo)]
from reconcile_rear_waypoint import reconcile
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
r=w/'front_corridor_midpoint_physical_r1';diagnosis=r/'REAR_BOX_CURRENT_EDGE_COMMAND_RESIDUAL_DIAGNOSTIC.json';d=json.loads(diagnosis.read_text());sources={str(diagnosis):sha(diagnosis)}
for path,h in d['source_sha256'].items():assert sha(path)==h,path;sources[path]=h
results=[];example=None
for run in d['results']:
 ep=w/run['run']/'case_840023/layout_840023_push_box_to_bin';rows=json.loads((ep/'frontal_bypass.json').read_text());fr={x['step']:x for x in rows['rows']};cs={x['step']:x for x in json.loads((ep/'coordination.json').read_text())};clearpath=ep/'self_clearance.json';clear=json.loads(clearpath.read_text());sources[str(clearpath)]=sha(clearpath);guards={x['step']:x for x in clear['rows'] if x['phase']=='final_command'}
 provpath=ep.parent/'provenance.json';prov=json.loads(provpath.read_text());sources[str(provpath)]=sha(provpath);name=next(n for n in prov['source_sha256'] if n.endswith('/articulated_hand_geometry.py'));p=ep.parent/'source_snapshot'/name;assert sha(p)==prov['source_sha256'][name]
 spec=importlib.util.spec_from_file_location('archived_geo',p);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);model=mod.ArticulatedHandGeometry(repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf',repo/'assets/robots/g1_hand_support_vertices.json')
 with np.load(ep/'raw.npz') as z:actions=z['action'][:,12:23].astype(float)
 proposals=[]
 for row in run['records']:
  t=row['step'];f=fr[t];edge=cs[t]['joint_edge_refinement'];assert guards[t]['accepted'];U=model.fk('right',actions[t])[0];point=U[:3,3]+U[:3,:3]@np.array(f['control_offset_local']);requested=np.array(f['target_xyz']);np.testing.assert_allclose((requested-point)*1000,row['unrealized_waypoint_minus_commanded_reference_mm'],rtol=0,atol=1e-10)
  args=dict(side='right',mode=f['mode'],rear_selected=rows['plan']['rear_cop_centering']['enabled'],edge_selected=edge['input_selected'],edge_override=edge['override'],command_accepted=guards[t]['accepted'],requested_xyz=requested,committed_reference_xyz=point,normal_load_n=row['normal_load_n'])
  assert reconcile(**args)['reason']=='disabled';proposal=reconcile(enabled=True,**args)
  if proposal['override']:
   assert edge['override'] and edge['input_selected'];assert np.array_equal(actions[t],np.asarray(edge['final_upper_command']))
   after=np.array(proposal['next_state_command_xyz']);assert np.array_equal(after[[0,2]],requested[[0,2]]) and after[1]==point[1] and after[1]>requested[1]
   assert np.array_equal(requested,np.array(f['target_xyz'])) # input untouched
   proposals.append(dict(step=t,**proposal))
   if example is None:example=args
 results.append(dict(run=run['run'],observations=len(run['records']),disabled_identity_count=len(run['records']),post_commit_y_proposals=len(proposals),median_cursor_reduction_mm=float(np.median([x['removed_unrealized_forward_y_m']*1000 for x in proposals])) if proposals else None,proposals=proposals))
 print({k:v for k,v in results[-1].items() if k!='proposals'},flush=True)
assert example is not None
negative=[]
for key,value in [('side','left'),('rear_selected',False),('mode','top_lift'),('edge_selected',False),('edge_override',False),('command_accepted',False),('normal_load_n',.2)]:
 out=reconcile(enabled=True,**{**example,key:value});assert not out['override'];negative.append(dict(field=key,value=value,reason=out['reason']))
for key,value in [('enabled',1),('side','bad'),('normal_load_n',float('nan')),('requested_xyz',[1,2]),('committed_reference_xyz',[0,float('nan'),0])]:
 args={**example,'enabled':True,key:value}
 try:reconcile(**args)
 except ValueError:negative.append(dict(field=key,invalid_rejected=True))
 else:raise AssertionError('Invalid candidate input accepted '+key)
for lead in [0.,-.001]:
 point=np.asarray(example['requested_xyz']).copy();point[1]+=lead;out=reconcile(enabled=True,**{**example,'committed_reference_xyz':point});assert not out['override'];negative.append(dict(field='no_forward_unrealized_cursor',value=lead,reason=out['reason']))
for path in [Path(__file__),draft/'reconcile_rear_waypoint.py',r/'REAR_BOX_EDGE_SWITCHING_FINDINGS.json']:sources[str(path)]=sha(path)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,scope=__doc__,results=results,negative_checks=negative,source_sha256=sources,collector_connected=False,new_physics=False,training_ready=False,remaining=['Independent next-update bookkeeping replay and full default-off integration/command binding.','Explicit state-transition audit; no bypass of original motion/quality/source gates.','Full original matched category-exchange groups and actual visuals; unexecuted proposals cannot claim improvement.'])
with (draft/'HISTORICAL_POST_COMMIT_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print('negative_checks',len(negative),'passed',True,flush=True)
