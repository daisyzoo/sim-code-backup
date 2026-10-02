"""Corruption and constraint rejection checks for the independent KKT verifier."""
from pathlib import Path
import sys,json,hashlib,copy,datetime
import numpy as np
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_rear_corridor_recovery_guarded';sys.path[:0]=[str(W),str(ROOT)]
from rear_corridor_stationarity import verify
from audit_rear_corridor_command_records import RecoveryVerifier
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();verifier=RecoveryVerifier(ROOT,S);full=json.loads((W/'REAR_CORRIDOR_JOINT_RECOVERY_FULL_CHECK.json').read_text());lifts=json.loads((W/'REAR_CORRIDOR_UNLOAD_CHECK.json').read_text());lookup={(r['episode'],r['step']):r['result'] for r in lifts['rows']};report=json.loads((W/'REAR_CORRIDOR_STATIONARITY_CHECK.json').read_text());assert report['status']=='complete' and report['passed'];checks=[];sources={}
for kind in ['loaded_recovery','unload']:
 sample=next(r for r in report['rows'] if r['kind']==kind);ep=W/sample['episode'];t=sample['step'];fr=json.loads((ep/'frontal_bypass.json').read_text());row=next(r for r in fr['rows'] if r['step']==t);coord=next(r for r in json.loads((ep/'coordination.json').read_text()) if r['step']==t);parent=next(r for item in full['episodes'] if item['episode']==sample['episode'] for r in item['rows'] if r['step']==t)['result'];result=parent if kind=='loaded_recovery' else lookup[(sample['episode'],t)];cmd=np.array(next(a['command'] for a in result['attempts'] if a['accepted']));key='box' if coord['active_side']=='right' else 'mailer';other='mailer' if key=='box' else 'box';sizes={'box':[.14,.09,.045],'mailer':[.15,.145,.04]}
 with np.load(ep/'trace.npz') as z:pos={k:z[k][t].copy() for k in sizes}
 with np.load(ep/'parcel_orientation.npz') as z:rot={k:Rotation.from_quat(z[k][t]).as_matrix() for k in sizes}
 with np.load(ep/'raw.npz') as z:prev=z['action'][t-1,12:23].copy()
 geometry=dict(target_xyz=pos[key],obstacle_xyz=pos[other],target_rotation=rot[key],obstacle_rotation=rot[other],target_size=sizes[key],obstacle_size=sizes[other],core_size=fr['plan']['rear_cop_centering']['actual_core_size_xyz']);args=dict(row=row,coordinate=coord,current=coord['upper_q'],previous=prev,command=cmd,kind=kind,geometry=geometry);good=verify(verifier,**args);assert good['passed'];checks.append(dict(kind=kind,test='untampered',passed=True,residual=good['stationarity_residual']))
 bad=copy.deepcopy(coord);bad['task_inputs']['error']=(np.array(bad['task_inputs']['error'])+np.arange(1,10)*.03).tolist();out=verify(verifier,**dict(args,coordinate=bad));assert not out['passed'] and out['reason']=='stationarity_failure';checks.append(dict(kind=kind,test='changed_objective_rejected',residual=out['stationarity_residual']))
 out=verify(verifier,**dict(args,command=cmd+1.));assert not out['passed'] and out['reason']=='original_primal_constraint_failure';checks.append(dict(kind=kind,test='invalid_command_rejected'))
 try:verify(verifier,**dict(args,previous=prev+.001))
 except AssertionError:checks.append(dict(kind=kind,test='causal_mismatch_rejected'))
 else:raise AssertionError('Invalid prior command accepted')
 for n in ['frontal_bypass.json','coordination.json','trace.npz','parcel_orientation.npz','raw.npz']:sources[str(ep/n)]=sha(ep/n)
sources.update({str(p):sha(p) for p in [Path(__file__),W/'rear_corridor_stationarity.py',W/'support_vertex_stationarity.py',W/'REAR_CORRIDOR_STATIONARITY_CHECK.json']});out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,checks=checks,source_sha256=sources,training_ready=False);dest=W/'REAR_CORRIDOR_STATIONARITY_NEGATIVE_CHECK.json';assert not dest.exists();dest.write_text(json.dumps(out,indent=2));print(json.dumps(checks,indent=2))
