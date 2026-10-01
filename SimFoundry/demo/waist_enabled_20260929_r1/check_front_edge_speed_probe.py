"""Check bounds, default bypass and actual recorded COP coverage; not physics."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;s=w/'staged_front_edge_speed_probe';spec=importlib.util.spec_from_file_location('edge_speed',s/'front_edge_speed.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
fixture=w/'FRONT_CONTACT_EDGE_WARNING_SCREEN.json';data=json.loads(fixture.read_text());reports=[];checked=0
for case in data['episodes']:
 ep=w/case['run']/('case_'+case['episode'].split('_')[1])/case['episode']
 for f,h in case['source_sha256'].items():assert sha(ep/f)==h
 cfg=ep.parent/'source_snapshot/simfoundry/scene_bridge/isaac_cfg.py';assert sha(cfg)==case['collision_config_sha256'];node=next(n for n in ast.walk(ast.parse(cfg.read_text())) if isinstance(n,ast.Assign) and any(isinstance(v,ast.Name) and v.id=='core_scale' for v in n.targets));key='box' if 'push_box' in ep.name else 'mailer';nominal=np.array([.14,.09,.045] if key=='box' else [.15,.145,.04]);core=nominal*np.array(ast.literal_eval(node.value.orelse if key=='box' else node.value.body))
 with np.load(ep/'parcel_orientation.npz') as z:rot=Rotation.from_quat(z[key]).as_matrix()
 affected=[];loaded=0;allsteps=[]
 for r in case['actual_contact_samples']:
  cop=np.array(r['cop_local_mm'])/1000 if 'cop_local_mm' in r else None
  kw=dict(mode=r['mode'],normal_load_n=r['normal_load_n'],cop_local=cop,object_rotation=rot[r['step']],core_size=core,axis=0 if r['stage']=='front_x' else 1,sign=-1 if r['stage']=='front_x' or key=='box' else 1)
  before=copy.deepcopy(kw);off=m.edge_speed(**kw);assert off==dict(applied=False,drive_step_m=.002,reason='disabled')
  on=m.edge_speed(enabled=True,**kw);checked+=1
  if r['mode']!='top_push' or cop is None or r['normal_load_n']<.3:assert not on['applied'] and on['drive_step_m']==.002;continue
  loaded+=1;assert .001<=on['drive_step_m']<=.002
  half=core[:2]/2;v=kw['sign']*rot[r['step']][kw['axis'],:];positive=[]
  if np.all(abs(cop[:2])<=half):
   for j in range(2):
    if abs(v[j])>1e-10:positive.append(((half[j] if v[j]>0 else -half[j])-cop[j])/v[j])
  distance=max(0,min(positive)) if positive else 0
  expected=.001+.001*min(1,distance/.010);assert abs(on['drive_step_m']-expected)<1e-12
  assert np.array_equal(before['cop_local'],kw['cop_local'])
  allsteps.append(on['drive_step_m'])
  if on['drive_step_m']<.002-1e-12:affected.append(dict(step=r['step'],stage=r['stage'],step_m=on['drive_step_m'],distance_mm=on['forward_core_distance_m']*1000))
 reports.append(dict(run=case['run'],episode=case['episode'],loaded_frames=loaded,reduced_frames=len(affected),median_loaded_drive_mm=float(np.median(allsteps)*1000),reduced_rows=affected))
 print(case['run'],case['episode'],'reduced',len(affected),'/',loaded,flush=True)
base=dict(enabled=True,mode='top_push',normal_load_n=5.,cop_local=[0.,0.,.02],object_rotation=np.eye(3),core_size=[.14,.09,.04],axis=1,sign=1)
for distance in [0.,.002,.005,.010,.025]:
 kw=dict(base,cop_local=[0.,.045-distance,.02]);a=m.edge_speed(**kw);assert abs(a['drive_step_m']-(.001+.001*min(1,distance/.01)))<1e-12
 for sign in [-1,1]:
  a=m.edge_speed(**dict(kw,sign=sign,cop_local=[0.,sign*(.045-distance),.02]));assert abs(a['drive_step_m']-(.001+.001*min(1,distance/.01)))<1e-12
negative=[]
for field,value in [('enabled',1),('nominal_step_m',float('nan')),('nominal_step_m',.0009),('normal_load_n',-1.),('axis',True),('sign',0),('cop_local',[float('nan'),0,0]),('object_rotation',np.zeros((3,3))),('core_size',[.01,.09,.04])]:
 try:m.edge_speed(**dict(base,**{field:value}))
 except ValueError:negative.append(field)
 else:raise AssertionError(field)
out=dict(passed=True,rows=reports,actual_recorded_frames_checked=checked,negative_cases_rejected=negative,geometric_mirror_cases=15,source_sha256=sha(s/'front_edge_speed.py'),fixture_sha256=sha(fixture),checker_sha256=sha(Path(__file__)),controller_wired=False,physical_started=False,training_ready=False,scope='Pure advisory scalar;1mm near edge to original2mm at>=10mm. Positive floor avoids imposed hold, but may still worsen real progress. Current fixed measured inputs only; no full controller shadow, dynamics, effectiveness or data admission.')
(s/'CHECK.json').write_text(json.dumps(out,indent=2));print('passed',checked)
