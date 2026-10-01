"""Real CLI acceptance/rejection on isolated fixtures; no source data mutation."""
from pathlib import Path
import sys,json,copy,hashlib,tempfile,shutil,subprocess
import numpy as np
w=Path(__file__).resolve().parent;stage=w/'staged_joint_edge_command';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();fixtures=json.loads((stage/'ENTRY_FIXTURES.json').read_text());script=w/'audit_joint_edge_execution_live.py';results=[]

def write_json(path,doc):
 if path.is_symlink():path.unlink()
 path.write_text(json.dumps(doc))

def modify_raw(ep,change):
 with np.load(ep/'raw.npz') as z:d={n:z[n].copy() for n in z.files}
 change(d);np.savez(ep/'raw.npz',**d)

with tempfile.TemporaryDirectory(prefix='joint_edge_entry_') as temp:
 root=Path(temp)
 def run(name,item,edit=None,expected=True,expected_stderr=None):
  source=Path(item['fixture']);case=root/name;shutil.copytree(source.parent,case,symlinks=True);ep=case/source.name
  for p in ep.glob('*AUDIT*.json'):p.unlink()
  if edit:edit(case,ep)
  ret=subprocess.run([sys.executable,str(script),str(ep)],capture_output=True,text=True)
  assert (ret.returncode==0)==expected,(name,ret.stdout[-500:],ret.stderr[-1700:])
  if expected_stderr:assert expected_stderr in ret.stderr,(name,ret.stderr[-1700:])
  report=ep/'JOINT_EDGE_EXECUTION_LIVE_AUDIT.json'
  if expected:
   a=json.loads(report.read_text());assert a['passed'] and a['auditor_sha256']==sha(script)
   for n,h in a.get('source_sha256',{}).items():assert sha(ep/n)==h
  results.append(dict(name=name,expected_accept=expected,returncode=ret.returncode,independent_report_written=report.exists()));print(name,ret.returncode,flush=True)
 box,bag,front=fixtures['rows']
 for name,item in [('box_enabled',box),('bag_enabled',bag),('front_excluded',front)]:run(name,item)
 def config(field,value):
  def edit(case,ep):
   p=ep/'frontal_bypass.json';a=json.loads(p.read_text());a['plan']['rear_joint_edge_command'][field]=value;write_json(p,a)
  return edit
 for field,value in [('enabled',1),('core_inset_m',.02),('waist_command_limit_rad',1.08),('final_slew_rad',.08),('first_loaded_preserved',False),('original_guard_priority',False),('fallback','ignore'),('reference','physical_contact')]:run('config_'+field,box,config(field,value),False)
 def declaration(case,ep):
  p=case/'provenance.json';a=json.loads(p.read_text());a['args']['rear_joint_edge_command']=False;write_json(p,a)
 run('declaration_mismatch',box,declaration,False)
 def archive(case,ep):
  prov=json.loads((case/'provenance.json').read_text());n=next(n for n in prov['source_sha256'] if n.endswith('/joint_edge_command.py'));p=case/'source_snapshot'/n;data=p.read_bytes();assert p.is_symlink();p.unlink();p.write_bytes(data+b'\n# corrupted fixture\n')
 run('archive_corruption',box,archive,False)
 def coord_mutator(kind):
  def edit(case,ep):
   p=ep/'coordination.json';a=json.loads(p.read_text());c=next(c for c in a if c.get('joint_edge_refinement',{}).get('override'));tr=c['joint_edge_refinement']
   if kind=='parent':tr['parent_final_upper_command'][2]+=.001
   elif kind=='previous':tr['previous_upper_command'][2]+=.001
   elif kind=='missing':del c['joint_edge_refinement']
   elif kind=='eligibility':tr['input_selected']=False
   elif kind=='claim_direction':tr['nominal_edge_inward_m'][0]+=.001
   elif kind=='stationarity':
    t=c['step'];j=4;value=float(np.float32(tr['command'][j]+.001));tr['command'][j]=tr['final_upper_command'][j]=value
    modify_raw(ep,lambda d:d['action'].__setitem__((t,j+12),value))
    # The changed coordinate is on the inactive arm: active FK claims remain identical.
   write_json(p,a)
  return edit
 for kind in ['parent','previous','missing','eligibility','claim_direction']:run('trace_'+kind,box,coord_mutator(kind),False)
 run('nonstationary_inactive_joint',box,coord_mutator('stationarity'),False,'stationarity')
 def corrupt_raw(case,ep):modify_raw(ep,lambda d:d['action'].__setitem__((0,12),.001))
 run('nonzero_first_action',box,corrupt_raw,False)
 def stale_residual(case,ep):
  source=Path(box['source'])/'region_approach.json';p=ep/'region_approach.json';write_json(p,json.loads(source.read_text()))
 run('stale_prior_action_residual',box,stale_residual,False)
 def force(case,ep):
  p=ep/'solved_contact_forces.json';a=json.loads(p.read_text());coord=json.loads((ep/'coordination.json').read_text());t=next(c['step'] for c in coord if c.get('joint_edge_refinement',{}).get('override'));packet=next(x for x in a['rows'] if x['after_action_step']==t-1)
  for c in packet['parcel_contacts']:
   if any('/parcel_box/' in s for s in c['shapes']) and any('right_wrist' in s for s in c['shapes']):c['position_world'][0]+=.002
  write_json(p,a)
 run('raw_contact_corruption',box,force,False)
 for item in fixtures['rows']:
  source=Path(item['source'])
  for n,h in item['source_sha256'].items():assert sha(source/n)==h
out=dict(passed=True,rows=results,fixtures_sha256=sha(stage/'ENTRY_FIXTURES.json'),auditor_sha256=sha(script),checker_sha256=sha(Path(__file__)),training_ready=False,scope='Actual CLI includes unchanged original region/causal/current-residual/continuity/measured-domain/XY audits. Positive shadows propagate modified ACTUAL commands and matching algebraic residual logs, but hold physical observations fixed and omit RGB; no physical execution or quality claim. Corruption cases reject without modifying original sources or lowering audits.')
(stage/'AUDITOR_ENTRY_CHECK.json').write_text(json.dumps(out,indent=2));print('PASSED',len(results))
