"""Regression of two changed argument checks and unchanged underlying guards.
No physical success; synthetic metadata mutations only. Existing full native
stream math must be identical except the explicit new parameter binding.
"""
from pathlib import Path
import sys,json,ast,copy,hashlib,datetime
w=Path(__file__).resolve().parent;sys.path[:0]=[str(w),str(w.parents[1])]
import numpy as np
from tilt05_diagnostic_contract import verify_configuration,verify_episode
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();files=[Path(__file__),w/'tilt05_diagnostic_contract.py'];regressed=[]
for a,b in [('audit_micro_clearance_live.py','audit_tilt05_micro_clearance_live.py'),('audit_box_inward_pose_height.py','audit_tilt05_box_inward_pose_height.py')]:
 s=(w/b).read_text().replace("args['expert_top_tilt_recontact_rad']==.05","args['expert_top_tilt_recontact_rad']==.03").replace('from tilt05_diagnostic_contract import verify_episode\n\n','').replace(' tilt05_binding=verify_episode(ep)\n','').replace('tilt05_configuration_binding=tilt05_binding,','')
 assert ast.dump(ast.parse(s))==ast.dump(ast.parse((w/a).read_text()));regressed.append(b);files.extend([w/a,w/b])
r=w/'box_inward_groups_r1';ep=r/'case_840001/layout_840001_push_box_to_bin';args=json.loads((ep.parent/'provenance.json').read_text())['args'];plan=json.loads((ep/'frontal_bypass.json').read_text())['plan']
with np.load(ep/'raw.npz') as z:meta=json.loads(str(z['collect_meta']))
try:verify_episode(ep)
except AssertionError as e:assert str(e)=='explicit0.05 internal withdrawal required'
else:raise AssertionError('Actual0.03 source admitted as0.05')
a=copy.deepcopy(args);p=copy.deepcopy(plan);m=copy.deepcopy(meta);a['expert_top_tilt_recontact_rad']=.05;p['contact_stability_candidate']['tilt_recontact_rad']=.05;m['frontal_bypass_plan']=copy.deepcopy(p);verify_configuration(a,p,m)
negative=[]
for name,mutate in [
 ('old_argument',lambda a,p,m:a.update(expert_top_tilt_recontact_rad=.03)),
 ('missing_argument',lambda a,p,m:a.pop('expert_top_tilt_recontact_rad')),
 ('changed_formal_gate',lambda a,p,m:p['contact_stability_candidate'].update(original_pose_max_tilt_rad=.25)),
 ('old_plan_threshold',lambda a,p,m:p['contact_stability_candidate'].update(tilt_recontact_rad=.03)),
 ('raw_mismatch',lambda a,p,m:m['frontal_bypass_plan']['contact_stability_candidate'].update(tilt_recontact_rad=.04)),
 ('non_diagnostic',lambda a,p,m:a.update(role='pilot')),
 ('assist',lambda a,p,m:m.update(assist_frames=1)),
 ('push_assist',lambda a,p,m:m.update(push_assist=True))]:
 aa,pp,mm=copy.deepcopy((a,p,m));mutate(aa,pp,mm)
 try:verify_configuration(aa,pp,mm)
 except AssertionError:negative.append(name)
 else:raise AssertionError(('accepted mutation',name))
files.extend([ep.parent/'provenance.json',ep/'raw.npz',ep/'frontal_bypass.json',w/'audit_micro_clearance_return.py',w/'audit_box_inward_source_contract.py',r/'PROTOCOL.json'])
expectations=w/'TILT05_SOURCE_EXPECTATIONS.json';files.append(expectations)
for row in json.loads(expectations.read_text())['rows']:
 q=Path(row['path']);assert sha(q)==row['sha256'];files.append(q)
 if row['included_in_parent_protocol']:assert sha(q)==json.loads((r/'PROTOCOL.json').read_text())['frozen_files_sha256'][str(q)]
# Exact executable gate stays0.20; don't pretend the parent's manifest included it.
assert 'upright&=tilt<=.20' in (w.parents[1]/'simfoundry/data/search_reward.py').read_text()
assert 'original_pose_tilt_gate_rad=.20' in (w/'audit_contact_stability_control.py').read_text()
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,same_mathematics_versions=regressed,synthetic_metadata_configuration_only=True,actual_old_parameter_rejected=True,negative_metadata_rejected=negative,original_micro_return_tilt_remains_rad=.03,formal_quality_tilt_remains_rad=.20,source_sha256={str(p):sha(p) for p in files},physical_validation=False,training_ready=False)
(w/'TILT05_DIAGNOSTIC_CONTRACT_CHECK.json').write_text(json.dumps(out,indent=2));print('PASS2 AST identical except explicit binding;8 metadata rejections;old actual rejected')
