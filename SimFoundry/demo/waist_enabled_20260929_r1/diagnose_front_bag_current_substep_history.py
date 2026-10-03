"""Reuse original load-history mathematics with a completed source-bound audit.
Only the already-passed contact audit lookup differs between the two closed runs.
This avoids rerunning identical array/force checks after their hashes are verified.
"""
from pathlib import Path
import ast,datetime,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def audit(ep):
 ep=Path(ep).resolve();run=ep.parent.parent.name
 versions={'front_corridor_midpoint_physical_r1':('FRONT_CORRIDOR_MIDPOINT_STAGE_CONTACT_AUDIT.json','audit_front_corridor_midpoint_stage_contacts.py'),'front_drive_1mm_physical_r1':('FRONT_DRIVE_1MM_V2_STAGE_CONTACT_AUDIT.json','audit_front_drive_1mm_v2_stage_contacts.py')}
 report,source=versions[run];d=json.loads((ep/report).read_text());assert d['passed'] is True and d['action_intervals']==1200 and d['auditor_sha256']==sha(W/source)
 for name,h in d['source_sha256'].items():assert sha(ep/name)==h,name
 for name,h in d['source_binding']['source_sha256'].items():assert sha(name)==h,name
 return d

def inspect(ep):
 source=W/'diagnose_substep_load_history.py';tree=ast.parse(source.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='inspect');namespace=dict(Path=Path,np=np,json=json,datetime=datetime,sha=sha,audit=audit,__file__=str(source),__doc__=__doc__)
 exec(compile(ast.Module(body=[fn],type_ignores=[]),str(source),'exec'),namespace);result=namespace['inspect'](ep)
 result['adaptation']='Original inspect function AST unchanged; reuse completed contact audit with all original inputs/source hashes verified.'
 result['adapter_sha256']=sha(__file__);result['original_inspector_sha256']=sha(source)
 report='FRONT_CORRIDOR_MIDPOINT_STAGE_CONTACT_AUDIT.json' if Path(ep).parent.parent.name=='front_corridor_midpoint_physical_r1' else 'FRONT_DRIVE_1MM_V2_STAGE_CONTACT_AUDIT.json';result['source_sha256'][report]=sha(Path(ep)/report)
 return result

if __name__=='__main__':
 ep=Path(sys.argv[1]);out=inspect(ep)
 with (ep/'SUBSTEP_LOAD_HISTORY.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps(out['summary'],indent=2))
