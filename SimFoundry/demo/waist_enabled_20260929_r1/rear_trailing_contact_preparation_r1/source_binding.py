"""Exact candidate source/settings archive contract only; no raw/physics admission.
Full native stream and per-episode control audits remain separate requirements.
"""
from pathlib import Path
import sys,json,hashlib
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];S=W/'staged_rear_trailing_contact_v1';T=W/'rear_trailing_contact_candidate_r1';B=W/'staged_joint_transport_bounded_v1';sys.path[:0]=[str(W),str(ROOT)]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify_preparation():
 from joint_transport_stage_source_binding_v1 import verify_preparation as verify_original
 _,bound=verify_original()
 prep=json.loads((S/'COLLECTOR_PREPARATION.json').read_text());parent=json.loads((B/'COLLECTOR_PREPARATION.json').read_text())
 assert prep['parent']==str(B) and prep['parent_manifest_sha256']==sha(B/'COLLECTOR_PREPARATION.json')
 assert parent['parent']==str(W/'staged_joint_transport_v1') and parent['parent_manifest_sha256']==sha(W/'staged_joint_transport_v1/COLLECTOR_PREPARATION.json')
 for p,a in [(B,parent),(S,prep)]:
  for n,h in a['stage_sha256'].items():assert sha(p/n)==h,n;bound[str(p/n)]=h
  for f,h in a['source_sha256'].items():assert sha(f)==h,f;bound[f]=h
  bound[str(p/'COLLECTOR_PREPARATION.json')]=sha(p/'COLLECTOR_PREPARATION.json')
 original=parent['stage_sha256'];current=prep['stage_sha256'];assert len(original)==96 and len(current)==101
 added={'trailing_contact_plan.py','trailing_offset_solver.py','trailing_recontact_plan.py','trailing_minimum_motion_lifecycle.py','trailing_entry_lift_lifecycle.py'}
 assert set(current)-set(original)==added and {n for n in original if original[n]!=current[n]}=={'collect_paired_sorting.py'}
 for n in added:assert current[n]==sha(T/n)
 text=(S/'collect_paired_sorting.py').read_text()
 for e in reversed(prep['collector_edits']):assert text.count(e['new'])==1;text=text.replace(e['new'],e['old'])
 assert text==(B/'collect_paired_sorting.py').read_text()
 for name,flag in [('PARSER_SOURCE_CHECK.json','passed'),('NATIVE_PREFIX_CHECK.json','complete'),('EVENT_AUDIT_CHECK.json','passed')]:
  p=D/name;a=json.loads(p.read_text());assert a[flag]
  for f,h in a['source_sha256'].items():assert sha(f)==h,f
  bound[str(p)]=sha(p)
 unused={'inactive_transport_clearance.py','transport_constraint_certificate.py','transport_path_certificate.py','inactive_transport_runtime.py'}
 expected={n:h for n,h in current.items() if n not in unused};assert len(expected)==97
 return expected,bound

def verify_settings(args):
 from joint_transport_stage_source_binding_v1 import verify_settings as original
 assert args['rear_box_trailing_preference'] is True
 a=dict(args);a.pop('rear_box_trailing_preference');return original(a)

def verify_trial_provenance(case):
 case=Path(case).resolve();expected,bound=verify_preparation();p=case/'provenance.json';prov=json.loads(p.read_text());verify_settings(prov['args'])
 prefix=str(S.relative_to(ROOT))+'/'
 assert {Path(n).name:h for n,h in prov['source_sha256'].items() if n.startswith(prefix)}==expected
 assert [n for n in prov['source_sha256'] if Path(n).name=='collect_paired_sorting.py']==[prefix+'collect_paired_sorting.py']
 for n,h in prov['source_sha256'].items():
  rel=Path(n);assert not rel.is_absolute() and '..' not in rel.parts
  assert sha(case/'source_snapshot'/rel)==h==sha(ROOT/rel),n
 bound[str(p)]=sha(p)
 return prov,bound
