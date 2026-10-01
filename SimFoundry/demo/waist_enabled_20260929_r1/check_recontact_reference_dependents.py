"""Original reference and terminal input math retained with verified capture
updates. Full eight unchanged parent episodes through the new script entries.
"""
from pathlib import Path
import sys,json,ast,hashlib,subprocess,copy
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)]
from audit_recontact_region_reference import audit as reference
from audit_region_reference_live import audit as original_reference
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
s=(w/'audit_recontact_region_reference.py').read_text().replace(' from recontact_audit_context import verified_events\n verified_recontacts=verified_events(ep)\n','').replace("  event=verified_recontacts.get(r['step'])\n  if event is not None and event['kind']=='handover':\n   from recontact_audit_context import selected_after_capture\n   selected=np.asarray(selected_after_capture(r,selected,verified_recontacts));center=np.asarray(event['captured_center_local'])\n",'').replace('RECONTACT_REGION_REFERENCE_AUDIT.json','REGION_REFERENCE_LIVE_AUDIT.json')
assert ast.dump(ast.parse(s),include_attributes=False)==ast.dump(ast.parse((w/'audit_region_reference_live.py').read_text()),include_attributes=False)
s=(w/'audit_recontact_terminal_inputs.py').read_text().replace('audit_recontact_region_reference','audit_region_reference_live').replace('RECONTACT_TERMINAL_INPUT_AUDIT.json','TERMINAL_HOLD_INPUT_AUDIT.json');assert ast.dump(ast.parse(s),include_attributes=False)==ast.dump(ast.parse((w/'audit_terminal_hold_inputs.py').read_text()),include_attributes=False)
chain=json.loads((w/'staged_recontact_pose/REGION_CHAIN_CHECK.json').read_text());results=[]
for case in chain['parent_replays']:
 ep=Path(case['fixture']);original=w/'rear_short_recovery_groups_r1'/ep.parent.name/ep.name
 assert reference(ep)==original_reference(original)
 for script,report in [('audit_recontact_terminal_inputs.py','RECONTACT_TERMINAL_INPUT_AUDIT.json'),('audit_recontact_normal_live.py','RECONTACT_NORMAL_LIVE_AUDIT.json')]:
  result=subprocess.run([sys.executable,str(w/script),str(ep)],capture_output=True,text=True);(ep/(script+'.log')).write_text(result.stdout+'\n'+result.stderr);assert result.returncode==0,(ep,script,result.stderr)
 t=json.loads((ep/'RECONTACT_TERMINAL_INPUT_AUDIT.json').read_text());old=json.loads((original/'TERMINAL_HOLD_INPUT_AUDIT.json').read_text())
 for key in ['summary','errors','records','calibrated_reference_frames']:assert t[key]==old[key],(ep.name,key)
 n=json.loads((ep/'RECONTACT_NORMAL_LIVE_AUDIT.json').read_text());assert n['passed'] and n['frames']==1199 and n['joint_path_frames']==0
 results.append(dict(episode=ep.name,terminal_frames=t['summary']['checked_frames'],normal_frames=n['normal_frames']));print(ep.name,'reference/terminal/normal passed',flush=True)
assert len(results)==8
sources=[Path(__file__),w/'audit_recontact_region_reference.py',w/'audit_region_reference_live.py',w/'audit_recontact_terminal_inputs.py',w/'audit_terminal_hold_inputs.py',w/'audit_recontact_normal_live.py',w/'recontact_audit_context.py',w/'audit_recontact_pose_normal.py']
out=dict(passed=True,scope=__doc__,original_reference_math_ast_exact=True,original_terminal_math_ast_exact=True,episodes=results,chain_fixture_sha256=sha(w/'staged_recontact_pose/REGION_CHAIN_CHECK.json'),source_sha256={str(p):sha(p) for p in sources},physical_validation=False,training_ready=False)
(w/'staged_recontact_pose/REFERENCE_DEPENDENTS_CHECK.json').write_text(json.dumps(out,indent=2));print('PASS',len(results),flush=True)
