"""Check isolated helper against independently solved actual geometry LP cases."""
from pathlib import Path
import json,sys,hashlib,copy
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;sys.path.insert(0,str(w/'staged_rear_joint_xy_probe'));from rear_joint_xy_progress import govern_rear_joint_xy
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();p=w/'REAR_JOINT_XY_DIRECTION_SCREEN.json';screen=json.loads(p.read_text());count=changed=0;sample=None
for case in screen['episodes']:
 ep=w/case['run']/('case_'+case['episode'].split('_')[1])/case['episode']
 for n,h in case['source_sha256'].items():assert sha(ep/n)==h
 f=json.loads((ep/'frontal_bypass.json').read_text());rows={r['step']:r for r in f['rows']};core=f['plan']['rear_cop_centering']['actual_core_size_xyz'];key='box' if 'push_box' in ep.name else 'mailer'
 with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z[key]).as_matrix()
 with np.load(ep/'trace.npz') as z:xyz=z[key].copy()
 for s in case['rows']:
  t=s['step'];r=rows[t];parent=r['rear_cop_centering']['command_xyz'];args=dict(mode=r['mode'],previous_xyz=rows[t-1]['target_xyz'],parent_xyz=parent,reference_xyz=r['observed_support_xyz'],object_rotation=rot[t],core_size=core,cop_local=rot[t].T@(np.asarray(r['rear_cop_centering']['cop_world'])-xyz[t]),normal_load_n=.3,direction=-1 if key=='box' else 1)
  # Normal validity already certified by source audit; not an independent raw-force audit.
  before=copy.deepcopy(args);assert govern_rear_joint_xy(enabled=False,**args)=={'override':False,'reason':'disabled'}
  got=govern_rear_joint_xy(enabled=True,**args);command=got.get('command_xyz',parent)
  if s['feasible']:assert np.max(abs(np.asarray(command)-s['candidate_command_xyz']))<2e-10,(t,got,s)
  else:assert not got['override']
  for n,v in before.items():assert np.array_equal(args[n],v)
  count+=1;changed+=bool(got['override']);sample=args
assert count==1153 and sample is not None
negative=0
for key,value in [('enabled','true'),('direction',True),('direction',0),('normal_load_n',float('nan')),('normal_load_n',-.1),('parent_xyz',[0,0]),('reference_xyz',[0,float('inf'),0]),('object_rotation',np.zeros((3,3))),('core_size',[.01,.1,.1]),('cop_local',[float('nan'),0,0])]:
 args=copy.deepcopy(sample);args['enabled']=True;args[key]=value
 try:govern_rear_joint_xy(**args)
 except ValueError:negative+=1
 else:raise AssertionError(key)
protected=0
for values in [dict(mode='top_lift'),dict(mode='top_release'),dict(normal_load_n=.2),dict(cop_local=None)]:
 args=copy.deepcopy(sample);args.update(values);assert not govern_rear_joint_xy(enabled=True,**args)['override'];protected+=1
out=dict(passed=True,actual_geometry_samples=count,changed_samples=changed,disabled_identity_calls=count,invalid_inputs_rejected=negative,protected_inputs_preserved=protected,helper_sha256=sha(w/'staged_rear_joint_xy_probe/rear_joint_xy_progress.py'),source_screen_sha256=sha(p),checker_sha256=sha(Path(__file__)),training_ready=False,scope='Helper geometry matches independent LP on4real streams1153inputs, all inputs unchanged. No wrapper/collector wiring, no propagated history or raw-force reconstruction, no physics.')
(w/'staged_rear_joint_xy_probe/HELPER_CHECK.json').write_text(json.dumps(out,indent=2));print(out)
