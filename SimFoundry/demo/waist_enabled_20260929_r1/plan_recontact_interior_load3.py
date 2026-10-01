"""Single-factor3N versus5N plan using identical frozen interior controller/auditors.
Draft validation may run while parent collects. --prepare requires fully closed
parent and stopped parent jobs. Never starts physics or admits training data.
"""
from pathlib import Path
import sys,json,hashlib,copy,datetime,subprocess,os
w=Path(__file__).resolve().parent;repo=w.parents[1];parent=w/'recontact_interior_groups_r1';run=w/'recontact_interior_load3_groups_r1';draft=w/'recontact_interior_load3_plan';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def planned():
 old=json.loads((parent/'PROTOCOL.json').read_text())
 for name,h in old['frozen_files_sha256'].items():assert sha(name)==h,name
 commands=copy.deepcopy(old['commands'])
 for before,c in zip(old['commands'],commands):
  c['args']=[x.replace(str(parent),str(run)) for x in c['args']]
  i=c['args'].index('--expert-frontal-top-load-n')+1;assert float(c['args'][i])==5.;c['args'][i]='3.'
  restored=[x.replace(str(run),str(parent)) for x in c['args']];restored[i]=before['args'][i];assert restored==before['args']
  assert all(c[k]==before[k] for k in c if k!='args')
 assert len(commands)==6 and sum(len(c['tasks']) for c in commands if not c['wait'])==8 and sum(len(c['tasks']) for c in commands if c['wait'])==2
 return old,commands

def preflight():
 old,commands=planned();draft.mkdir(exist_ok=True);checks=[]
 binding=json.loads((draft/'PRESSURE_BINDING_PREFLIGHT.json').read_text());assert binding['passed'] and len(binding['rows'])>=4 and all(x['wrong3N_label_rejected'] for x in binding['rows'])
 assert binding['script_sha256']==sha(w/'verify_top_pressure_setting.py')
 env=os.environ.copy();env.update(OMNI_KIT_ACCEPT_EULA='yes',CONDA_PREFIX='/home/user/miniconda3/envs/env_isaaclab',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
 for c in commands:
  # Layout paths still point to parent for parser-only checking; physical draft
  # keeps new paths and prepare copies identical layout bytes when parent closes.
  args=[x.replace(str(run/'layouts'),str(parent/'layouts')) for x in c['args']]+['--out-dir','/tmp/interior_load3_prelaunch_no_physics']
  code="from pathlib import Path\nimport sys,types\np=Path("+repr(old['collector'])+")\ns=p.read_text().split('app = AppLauncher(args, enable_cameras=True).app')[0]\nm=types.ModuleType('__pressure_prelaunch__');sys.modules[m.__name__]=m;m.__dict__['__file__']=str(p)\nexec(compile(s,str(p),'exec'),m.__dict__)\na=m.args\nassert a.expert_frontal_top_load_n==3. and a.recontact_interior_preference and a.unloaded_recontact_pose\nassert a.horizon==10 and not hasattr(a,'push_assist') and not a.push_force_n and not a.wait_force_n\nprint('LOAD3_PRELAUNCH_OK')\n"
  p=subprocess.run([sys.executable,'-c',code,*args],capture_output=True,text=True,env=env,cwd=repo);(draft/f"prelaunch_{c['layout_id']}.log").write_text(p.stdout+'\n'+p.stderr)
  assert p.returncode==0 and 'LOAD3_PRELAUNCH_OK' in p.stdout,(c['layout_id'],p.stdout[-1000:],p.stderr[-2000:])
  checks.append(dict(layout_id=c['layout_id'],wait=c['wait'],passed=True));print('actual_prelaunch_passed',c['layout_id'],flush=True)
 sys.path.insert(0,str(w));from interior_run_contract import controls,ADDITIONAL,primary
 controls_count=0
 # Completed parent-of-parent supplies unchanged route classification inventory.
 inventory=w/'recontact_pose_groups_r1'
 for c in commands:
  for task in c['tasks']:
   if not c['wait']:controls_count+=len(controls(json.loads((inventory/f"case_{c['layout_id']}"/f"layout_{c['layout_id']}_{task}"/'frontal_bypass.json').read_text())['plan']))
 assert controls_count==80 and len(ADDITIONAL)*8==56
 out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,scope=__doc__,parent_protocol_sha256=sha(parent/'PROTOCOL.json'),collector=old['collector'],commands=commands,actual_prelaunch_commands=checks,control_invocations=80,additional_invocations=56,original_primary_per_push=len(primary(False)),original_primary_per_wait=len(primary(True)),source_sha256={str(Path(__file__).resolve()):sha(__file__),str(w/'verify_top_pressure_setting.py'):sha(w/'verify_top_pressure_setting.py'),str(draft/'PRESSURE_BINDING_PREFLIGHT.json'):sha(draft/'PRESSURE_BINDING_PREFLIGHT.json'),**old['frozen_files_sha256']},only_parameter_change={'expert_frontal_top_load_n':{'old':5.,'new':3.}},source_control_changes=False,physical_validation=False,training_ready=False)
 (draft/'PREFLIGHT.json').write_text(json.dumps(out,indent=2));print('PASS same source sixCLI original8push2wait80+56',flush=True)

def prepare():
 assert not run.exists();old,commands=planned();check=json.loads((draft/'PREFLIGHT.json').read_text());assert check['passed'] and check['commands']==commands and check['parent_protocol_sha256']==sha(parent/'PROTOCOL.json')
 for name,h in check['source_sha256'].items():assert sha(name)==h,name
 result=json.loads((parent/'RESULT.json').read_text());assert result['status']=='diagnostic_closed_not_training_admission' and result['push_total']==8 and len(result['rows'])==10 and result['actual_sampled_visual_review_complete'] and result['original_control_invocations']==80 and result['additional_invocations']==56 and not result['training_ready']
 for name in ['STATUS.json','CONTROL_EVIDENCE_EXECUTION.json','ADDITIONAL_AUDIT_EXECUTION.json']:
  d=json.loads((parent/name).read_text());assert not Path(f"/proc/{d['pid']}/cmdline").exists()
 files=copy.deepcopy(old['frozen_files_sha256']);files.update(check['source_sha256']);files[str(draft/'PREFLIGHT.json')]=sha(draft/'PREFLIGHT.json');files[str(parent/'RESULT.json')]=sha(parent/'RESULT.json')
 run.mkdir();(run/'layouts').mkdir()
 for p in (parent/'layouts').glob('*.json'):
  dest=run/'layouts'/p.name;dest.write_bytes(p.read_bytes());files[str(dest)]=sha(dest)
 out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),collector=old['collector'],commands=commands,frozen_files_sha256=files,parent_protocol_sha256=sha(parent/'PROTOCOL.json'),parent_result_sha256=sha(parent/'RESULT.json'),scope='Full same8push2wait, same collector/auditors/camera/layouts/seeds/order/budgets/20mm preference. Only configured top desired pressure5N->3N. No task-IK precision integration. Original80+56 audits,10actual image reviews, original task andh10gates. Lower pressure can reduce friction and worsen slipping; no claimed benefit.',training_ready=False)
 (run/'PROTOCOL.json').write_text(json.dumps(out,indent=2));(run/'INPUT_COMPARISON.json').write_text(json.dumps(dict(same_source=True,same_tasks_layouts_seeds_horizons_order=True,only_parameter_change=check['only_parameter_change'],commands=6,control_invocations=80,additional_invocations=56,training_ready=False),indent=2));print('prepared_not_started',run,len(files))
if __name__=='__main__':
 if sys.argv[1:]==['--prepare']:prepare()
 else:assert not sys.argv[1:];preflight()
