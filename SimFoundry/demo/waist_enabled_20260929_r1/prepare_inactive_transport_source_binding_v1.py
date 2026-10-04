"""Derive new-source binding retaining parent physical observation checks exactly."""
from pathlib import Path
import ast,json,hashlib,datetime
W=Path(__file__).resolve().parent;S=W/'staged_inactive_transport_v1';P=W/'front_box_recenter_stage_source_binding.py';O=W/'inactive_transport_stage_source_binding_v1.py';text=P.read_text();edits=[]
def replace(old,new):
 global text
 assert text.count(old)==1,old[:80]
 text=text.replace(old,new);edits.append(dict(old=old,new=new))
replace("S=W/'staged_front_box_recenter_v3'","S=W/'staged_inactive_transport_v1'")
for fname,body in [('verify_preparation','''def verify_preparation():
 from front_box_recenter_stage_source_binding import verify_preparation as verify_parent
 old,bound=verify_parent();prep=json.loads((S/'COLLECTOR_PREPARATION.json').read_text());parent=Path(prep['parent']);assert parent==W/'staged_front_box_recenter_v3'
 assert sha(parent/'COLLECTOR_PREPARATION.json')==prep['parent_manifest_sha256']
 for p,h in prep['source_sha256'].items():assert sha(p)==h,p
 expected=prep['stage_sha256'];helpers={'inactive_transport_clearance.py','transport_constraint_certificate.py','transport_path_certificate.py','inactive_transport_runtime.py'};geometry={'audit_front_recontact_center_events.py','audit_unloaded_wrist_prior_live.py','audit_unloaded_wrist_task_optimality.py'}
 assert len(expected)==88 and set(expected)==set(old)|helpers|geometry
 assert {n for n in old if expected[n]!=old[n]}==set(prep['changed_parent_files'])=={'collect_paired_sorting.py'}
 assert set(prep['edits'])==set(prep['changed_parent_files'])
 for n,h in expected.items():assert sha(S/n)==h,n
 for n,changes in prep['edits'].items():
  restored=(S/n).read_text()
  for e in reversed(changes):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
  assert restored==(parent/n).read_text()
 for n in helpers:assert sha(S/n)==sha(W/'inactive_transport_clearance_bilateral_draft_r1'/n)
 for n in geometry:assert sha(S/n)==sha(W/n)
 for n in ['PARSER_CHECK.json','NATIVE_HOOK_CHECK.json','INDEPENDENT_RECORD_CHECK.json']:
  proof=json.loads((S/n).read_text());assert proof['passed']
  for p,h in proof['source_sha256'].items():assert sha(p)==h,p
  bound[str(S/n)]=sha(S/n)
 bound[str(S/'COLLECTOR_PREPARATION.json')]=sha(S/'COLLECTOR_PREPARATION.json')
 return expected,bound'''),('verify_settings','''def verify_settings(args):
 from front_box_recenter_stage_source_binding import verify_settings as verify_parent
 assert args['inactive_transport_clearance'] is True
 args=dict(args);args.pop('inactive_transport_clearance')
 return verify_parent(args)''')]:
 node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name==fname);replace(ast.get_source_segment(text,node),body)
replace("spec=json.loads((S/'COLLECTOR_PREPARATION.json').read_text())['box_recenter']","spec=json.loads((W/'staged_front_box_recenter_v3/COLLECTOR_PREPARATION.json').read_text())['box_recenter']")
replace('def verify_observation_binding(ep):','def _verify_parent_observation_binding(ep):')
text+='''

def verify_observation_binding(ep):
 ep=Path(ep).resolve();result=_verify_parent_observation_binding(ep)
 with np.load(ep/'raw.npz',allow_pickle=False) as z:
  meta=json.loads(str(z['collect_meta']));q=z['q'][:,12:23];u=z['action'][:,12:23]
 data=json.loads((ep/'inactive_transport_clearance.json').read_text());spec=json.loads((S/'COLLECTOR_PREPARATION.json').read_text())['spec']
 assert meta['inactive_transport_clearance']==data['spec']==spec and data['training_ready'] is False
 rows=data['rows'];assert [r['step'] for r in rows]==list(range(len(q)))
 assert all(type(r['step']) is int and type(r['applied']) is bool and r['training_ready'] is False and r['version']==spec['version'] for r in rows)
 assert meta['inactive_transport_applied_frames']==sum(r['applied'] for r in rows)
 for t,r in enumerate(rows):
  assert np.array_equal(r['output_command'],u[t])
  assert np.array_equal(r['collector_context']['current'],q[t])
  if t==0:assert r['collector_context']['previous_q'] is None and np.array_equal(q[t],np.zeros(11)) and np.array_equal(u[t],np.zeros(11))
  else:
   assert np.array_equal(r['collector_context']['previous_q'],q[t-1])
   assert np.array_equal(r['collector_context']['previous_command'],u[t-1])
 result['source_sha256'][str(ep/'inactive_transport_clearance.json')]=sha(ep/'inactive_transport_clearance.json')
 result['source_sha256'][str(Path(__file__))]=sha(Path(__file__))
 result['transport_full_command_stream_audit_required']=True
 return result
'''
ast.parse(text)
with O.open('x') as f:f.write(text)
restored=text[:text.index('\n\ndef verify_observation_binding(ep):')]
for e in reversed(edits):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
assert restored==P.read_text()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,edits=edits,parent_sha256=sha(P),output_sha256=sha(O),source_sha256={str(p):sha(p) for p in [Path(__file__),P,O,S/'COLLECTOR_PREPARATION.json']},parent_observation_checks_preserved=True,source_binding_checked=False,physics_started=False,training_ready=False)
with (S/'SOURCE_BINDING_PREPARATION.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(generated=str(O),parent_observation_checks_preserved=True)))
