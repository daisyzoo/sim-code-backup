"""Check geometric governor against previously independent LP screen and fixtures."""
from pathlib import Path
import sys,json,hashlib,copy
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;stage=w/'staged_rear_coupled_progress_probe';sys.path.insert(0,str(stage));from rear_coupled_progress import govern_rear_progress
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();screen=json.loads((w/'REAR_COUPLED_PROGRESS_SCREEN.json').read_text());reports=[];all_frames=0
for episode in screen['episodes']:
 ep=next((w/episode['run']).glob('case_*/'+episode['episode']));key='box' if 'push_box' in ep.name else 'mailer'
 for n,h in episode['source_sha256'].items():assert sha(ep/n)==h
 fr=json.loads((ep/'frontal_bypass.json').read_text());size=fr['plan']['rear_cop_centering']['actual_core_size_xyz'];rows=fr['rows'];samples={x['step']:x for x in episode['samples']}
 with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z[key]).as_matrix()
 with np.load(ep/'trace.npz') as z:xyz=z[key]
 checks=changed=0
 for prev,row in zip(rows,rows[1:]):
  t=row['step'];f=row.get('rear_cop_centering',{});cop=rot[t].T@(np.array(f['cop_world'])-xyz[t]) if f.get('override') else None
  kw=dict(mode=row['mode'],previous_xyz=prev['target_xyz'],parent_xyz=row['target_xyz'],object_rotation=rot[t],core_size=size,cop_local=cop,normal_load_n=5. if cop is not None else 0.,direction=-1 if key=='box' else 1)
  assert govern_rear_progress(enabled=False,**kw)==dict(override=False,reason='disabled');all_frames+=1
  if t not in samples:continue
  expected=samples[t];got=govern_rear_progress(enabled=True,**kw);checks+=1
  should_change=expected['status']=='reduced';assert got['override']==should_change,(t,got,expected)
  if should_change:
   changed+=1;assert abs(got['scale']-expected['scale'])<1e-8
   delta=np.array(got['command_xyz'])-np.array(prev['target_xyz']);assert np.max(abs(delta*1000-np.array(expected['candidate_delta_mm'])))<1e-7
   assert np.array_equal(np.array(got['command_xyz'])[[0,2]],np.array(row['target_xyz'])[[0,2]])
  elif expected['status']=='no_Y_only_direction':assert got['reason']=='no_Y_only_direction'
 assert checks==episode['summary']['overrides'];reports.append(dict(run=episode['run'],episode=ep.name,checked=checks,changed=changed))
base=dict(enabled=True,mode='top_push',previous_xyz=[.5,0,.8],parent_xyz=[.5005,-.003,.8],object_rotation=Rotation.from_euler('z',.5).as_matrix(),core_size=[.12,.10,.04],cop_local=[-.055,0,.02],normal_load_n=5.,direction=-1)
fixtures=[]
for side in [-1,1]:
 for axis in [0,1]:
  k=copy.deepcopy(base);k['cop_local']=[0,0,.02];k['cop_local'][axis]=side*(k['core_size'][axis]/2-.003)
  for direction in [-1,1]:
   k['direction']=direction;k['parent_xyz'][1]=direction*.003;g=govern_rear_progress(**k)
   if g['override']:
    movement=k['object_rotation'].T@(np.array(g['command_xyz'])-k['previous_xyz']);assert side*movement[axis]<=1e-10
   fixtures.append(dict(side=side,axis=axis,direction=direction,result=g))
for delta,reason in [({'mode':'top_lift'},'original_non_push_mode'),({'mode':'top_release'},'original_non_push_mode'),({'cop_local':None},'no_valid_loaded_contact'),({'normal_load_n':.29},'no_valid_loaded_contact'),({'cop_local':[0,0,.02]},'no_near_core_edge'),({'parent_xyz':[.5005,.003,.8]},'parent_nonforward_preserved'),({'object_rotation':np.eye(3),'parent_xyz':[.4995,-.003,.8]},'no_Y_only_direction')]:
 g=govern_rear_progress(**{**base,**delta});assert not g['override'] and g['reason']==reason;fixtures.append(dict(expected=reason))
negatives=0
for delta in [{'enabled':1},{'enabled':None},{'normal_load_n':float('nan')},{'normal_load_n':-1},{'direction':0},{'direction':True},{'core_size':[.02,.1,.04]},{'core_size':[.12,.1,0]},{'parent_xyz':[float('nan'),0,0]},{'cop_local':[0,0]},{'object_rotation':np.zeros((3,3))}]:
 try:govern_rear_progress(**{**base,**delta})
 except ValueError:negatives+=1
 else:raise AssertionError(delta)
result=dict(passed=True,rows=reports,total_default_frames=all_frames,total_lp_checked=sum(r['checked'] for r in reports),total_changed=sum(r['changed'] for r in reports),fixtures=fixtures,negative_cases=negatives,screen_sha256=sha(w/'REAR_COUPLED_PROGRESS_SCREEN.json'),source_sha256=sha(stage/'rear_coupled_progress.py'),checker_sha256=sha(Path(__file__)),collector_wired=False,physical_started=False,training_ready=False,scope='Helper parity against independent LP screen from actual audited X commands, 15 direction/guard fixtures and11negative inputs. Scalar normal5N here gates already audited loaded samples; not raw-force reconstruction or dynamic validation, wrapper lifecycle separate.')
p=stage/'CHECK.json';assert not p.exists();p.write_text(json.dumps(result,indent=2));print({k:v for k,v in result.items() if k not in ['rows','fixtures']})
