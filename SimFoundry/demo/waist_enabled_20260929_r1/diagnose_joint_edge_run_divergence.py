"""Locate actual parent/new divergence; no counterfactual efficacy claim."""
from pathlib import Path
import json,hashlib,collections
import numpy as np
w=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parent=w/'rear_joint_xy_groups_r1';new=w/'joint_edge_groups_r1'
pa=json.loads((parent/'case_840001/provenance.json').read_text());pb=json.loads((new/'case_840001/provenance.json').read_text())
args={k:[pa['args'].get(k),pb['args'].get(k)] for k in pa['args'].keys()|pb['args'].keys() if pa['args'].get(k)!=pb['args'].get(k)}
normalized=[]
for run,prov in [(parent,pa),(new,pb)]:
 mapping={}
 for path,digest in prov['source_sha256'].items():
  assert sha(run/'case_840001/source_snapshot'/path)==digest
  key=('STAGE/'+Path(path).name) if '/staged_' in path else path
  assert key not in mapping
  mapping[key]=digest
 normalized.append(mapping)
sources={k:[normalized[0].get(k),normalized[1].get(k)] for k in normalized[0].keys()|normalized[1].keys() if normalized[0].get(k)!=normalized[1].get(k)}
assert set(sources)=={'STAGE/collect_paired_sorting.py','STAGE/joint_edge_command.py','STAGE/joint_edge_adapter.py'}
assert set(args)<= {'out_dir','diagnostic_layout_json','rear_joint_edge_command'}
assert pa['physics']==pb['physics']
assert sha(parent/'layouts/840001.json')==sha(new/'layouts/840001.json')
results=[]
for task,key,direction in [('push_box_to_bin','box',-1),('nudge_mailer_to_bin','mailer',1)]:
 eps=[r/'case_840001'/('layout_840001_'+task) for r in [parent,new]];records=[];raw=[];tr=[];fr=[]
 for ep in eps:
  with np.load(ep/'raw.npz') as z:raw.append({k:z[k].copy() for k in ['q','action']})
  with np.load(ep/'trace.npz') as z:tr.append(z[key].copy())
  f=json.loads((ep/'frontal_bypass.json').read_text());fr.append(f)
  coords=json.loads((ep/'coordination.json').read_text());joint_changed=[c['step'] for c in coords if c.get('joint_edge_refinement',{}).get('override')]
  quality=json.loads((ep/'quality.json').read_text());rows=f['rows'];exits=collections.Counter(('terminal_release' if rows[i]['mode']=='top_release' else rows[i].get('last_recontact_reason')) for i in range(1,len(rows)) if rows[i-1]['mode']=='top_push' and rows[i]['mode']!='top_push')
  records.append(dict(run=ep.parent.parent.name,progress_mm=quality['metrics']['target_final_progress_m']*1000,quality_passed=quality['passed'],final10_min_signed_y_mm=float(min(direction*tr[-1][-10:,1])*1000),exit_counts=dict(exits),rear_enabled=f['plan'].get('rear_joint_edge_command',{}).get('enabled',False),first_final_joint_changed_step=joint_changed[0] if joint_changed else None,first_rear_changed_step=next((r['step'] for r in rows if r.get('rear_joint_xy_progress',{}).get('override')),None),source_sha256={n:sha(ep/n) for n in ['quality.json','raw.npz','trace.npz','frontal_bypass.json','coordination.json']}))
 def first(a,b,threshold):
  err=np.max(abs(a.astype(float)-b.astype(float)),axis=1);t=np.flatnonzero(err>threshold)
  return dict(step=int(t[0]),max_abs_difference=float(err[t[0]])) if len(t) else None
 diffs={}
 for label,a,b,thresholds in [('q_rad',raw[0]['q'],raw[1]['q'],[0,1e-6,1e-4,.001]),('action_rad',raw[0]['action'],raw[1]['action'],[0,1e-6,1e-4,.001]),('object_xyz_m',tr[0],tr[1],[0,1e-6,.0001,.001])]:
  diffs[label]={str(t):first(a,b,t) for t in thresholds}
 a={r['step']:r for r in fr[0]['rows']};b={r['step']:r for r in fr[1]['rows']}
 mode=next((dict(step=t,parent=a[t]['mode'],new=b[t]['mode']) for t in sorted(a.keys()&b.keys()) if a[t]['mode']!=b[t]['mode']),None)
 plans={k:[fr[0]['plan'].get(k),fr[1]['plan'].get(k)] for k in fr[0]['plan'].keys()|fr[1]['plan'].keys() if fr[0]['plan'].get(k)!=fr[1]['plan'].get(k)}
 results.append(dict(task=task,rows=records,first_differences=diffs,first_mode_difference=mode,plan_differences=plans))
out=dict(argument_differences=args,source_differences=sources,physics_equal=True,layout_bytes_equal=True,episodes=results,checker_sha256=sha(Path(__file__)),training_ready=False,scope='Observed two same-seed runs. Earlier-than-override divergence rules out attributing entire trajectory difference to new final joint direction refinement; does not prove source of physics nondeterminism or measure causal effect. No failure data admitted.')
p=new/'RUN_DIVERGENCE_DIAGNOSIS.json';p.write_text(json.dumps(out,indent=2))
print(json.dumps({'source_differences':list(sources),'physics_equal':True,'layout_bytes_equal':True,'episodes':[{'task':r['task'],'first_differences':r['first_differences'],'first_mode_difference':r['first_mode_difference'],'plan_difference_keys':list(r['plan_differences'])} for r in results]},indent=2))
