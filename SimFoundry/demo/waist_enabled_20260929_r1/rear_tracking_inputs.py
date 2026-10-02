"""Verify native recovery records before exposing parent control inputs.
Parent targets are for same-step control reconstruction only. Raw measured q and
actual previous actions are never rewritten. Required transport steps include the
measured handover frame and exclude the frame that first emits the unload.
This boundary is not the complete pose/path/contact audit or training admission.
"""
from pathlib import Path
from dataclasses import dataclass
import copy,json,hashlib
from audit_rear_recovery_tracking_native_bound import verify_files

FILES=('raw.npz','rear_corridor_recovery.json','frontal_bypass.json','coordination.json',
       'expert_control.json','recontact_pose.json','peak_load_updates.json',
       'trace.npz','parcel_orientation.npz')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def unique(rows):
    out={r['step']:r for r in rows};assert len(out)==len(rows)
    return out

@dataclass(frozen=True)
class VerifiedInputs:
    episode: Path
    proof: dict
    overrides: dict
    required_transport_steps: frozenset
    file_sha256: dict

    def assert_unchanged(self):
        for name,h in self.file_sha256.items():assert sha(self.episode/name)==h,('episode changed during audit',name)

    def parent_row(self,step,final_row):
        assert final_row['step']==step
        return copy.deepcopy(self.overrides[step]['parent_row'] if step in self.overrides else final_row)

    def parent_expert(self,step,final_expert):
        assert final_expert['step']==step
        out=copy.deepcopy(final_expert)
        if step in self.overrides:
            row=self.overrides[step]['parent_row'];out['mode']=row['mode'];out['target_xyz']=copy.deepcopy(row['target_xyz'])
        return out

    def parent_command(self,step,actual_command):
        return copy.deepcopy(self.overrides[step]['parent_command'] if step in self.overrides else actual_command)


def verify_inputs(ep,root,stage):
    ep=Path(ep).resolve();hashes={n:sha(ep/n) for n in FILES if (ep/n).exists()}
    proof=verify_files(ep,root,stage);assert proof['passed']
    log=json.loads((ep/'rear_corridor_recovery.json').read_text())
    rows=unique(log['rows']);hands=unique(log['handovers']);overrides={t:r for t,r in rows.items() if r['kind'] in ('loaded_recovery','unload')}
    assert len(overrides)==proof['overrides']
    required=set();pending=False;completed=[]
    for t in range(1,proof['frames']):
        if pending:required.add(t)
        if t in hands:
            assert pending;pending=False;completed.append(t)
        if t in overrides and overrides[t]['kind']=='unload':
            assert not pending;pending=True
    assert not pending
    assert completed==proof.get('measured_directional_handovers',[])
    out=VerifiedInputs(ep,proof,overrides,frozenset(required),hashes);out.assert_unchanged()
    return out
