"""Preserve original measured geometry/force/history/COP audit; replace cap math only."""
from pathlib import Path
import json,hashlib,ast,datetime
W=Path(__file__).resolve().parent;src=W/'audit_front_loaded_material_cap.py';dst=W/'audit_front_loaded_material_projection.py';assert not dst.exists();s=src.read_text();edits=[]
def replace(old,new):
 global s
 assert s.count(old)==1;s=s.replace(old,new);edits.append(dict(old=old,new=new))
old='from front_initial_center_reference_ledger import verified_reference_lifetimes';replace(old,old+'\nfrom front_loaded_projection_independent_math import verify as verify_projection')
start=s.index('            # Each axis is a one-dimensional strictly convex projection.')
end=s.index('            self.active[t]=',start)
old=s[start:end]
new='''            # Scalar projection verifier is separate from production code.
            checked=verify_projection(a,parent=parent[:2].tolist(),previous=previous.tolist(),reference=obs_ref.tolist(),material=obs_surface.tolist(),normal=normal)
            assert checked['feasible'],'A genuinely empty set must stop before action'
            expected=np.asarray(checked['command_xy'])
            close(row['target_xyz'][:2],expected)
'''
replace(old,new)
restored=s
for e in reversed(edits):assert restored.count(e['new'])==1;restored=restored.replace(e['new'],e['old'])
assert restored==src.read_text();ast.parse(s);dst.write_text(s)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,source_sha256={str(p):sha(p) for p in [src,dst,W/'front_loaded_projection_independent_math.py',Path(__file__)]},edits=edits,integrated_into_run_contract=False,physical_audit_executed=False,training_ready=False)
with (W/'FRONT_LOADED_PROJECTION_AUDIT_PREPARATION.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(auditor=str(dst),edits=len(edits),physical_audit_executed=False)))
