"""Preserve the full original diagnostic and audit flow for the final-load candidate."""
from pathlib import Path
import ast,json,hashlib,datetime
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rename(s):return s.replace('audit_peak_guard','audit_instant_guard').replace('peak_guard_run_contract','instant_guard_run_contract').replace('staged_peak_load_guard','staged_instant_load_guard').replace('PEAK_GUARD_','INSTANT_GUARD_')
rows=[]
for a,b in [('peak_guard_run_contract.py','instant_guard_run_contract.py'),('run_peak_guard_groups.py','run_instant_guard_groups.py'),('watch_peak_guard_audits.py','watch_instant_guard_audits.py'),('close_peak_guard_groups.py','close_instant_guard_groups.py')]:
    src=W/a;dst=W/b;assert not dst.exists();base=rename(src.read_text());s=base;changes=[]
    def replace(old,new):
        global s
        assert s.count(old)==1,(a,old);s=s.replace(old,new);changes.append((old,new))
    if a in ('run_peak_guard_groups.py','close_peak_guard_groups.py'):
        replace("assert prov['args']['peak_load_bias_guard'] is True","assert prov['args']['instant_load_bias_guard'] is True and prov['args']['peak_load_bias_guard'] is True")
    if a=='close_peak_guard_groups.py':
        replace("assert meta['peak_load_bias_guard'] is True", "assert meta['instant_load_bias_guard'] is True and meta['peak_load_bias_guard'] is True")
    restored=s
    for old,new in reversed(changes):assert restored.count(new)==1;restored=restored.replace(new,old)
    assert restored==base;ast.parse(s);dst.write_text(s)
    rows.append(dict(parent=str(src),parent_sha256=sha(src),new=str(dst),new_sha256=sha(dst),changes=changes,original_flow_preserved_except_explicit_candidate_source_binding=True))
import peak_guard_run_contract as old
import instant_guard_run_contract as new
r=W/'peak_guard_groups_r1';p=json.loads((r/'PROTOCOL.json').read_text());control=0;primary=0
for c in p['commands']:
    assert new.primary(c['wait'])==[rename(s) for s in old.primary(c['wait'])]
    primary+=len(c['tasks'])*len(new.primary(c['wait']))
    if not c['wait']:
        for task in c['tasks']:
            plan=json.loads((r/f"case_{c['layout_id']}"/f"layout_{c['layout_id']}_{task}"/'frontal_bypass.json').read_text())['plan']
            assert new.controls(plan)==[rename(s) for s in old.controls(plan)];control+=len(new.controls(plan))
assert primary==36 and control==80 and len(new.ADDITIONAL)*8==56
assert new.ADDITIONAL==[rename(s) for s in old.ADDITIONAL]
assert new.REPORTS=={rename(k):(rename(v[0]),v[1]) for k,v in old.REPORTS.items()}
for name in new.REPORTS:assert (W/name).exists(),name
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),rows=rows,original_primary=36,original_control=80,original_additional=56,original_observation=10,explicit_final_load_pressure=10,source_sha256={str(p):sha(p) for p in [Path(__file__),*[W/n for n in new.REPORTS],r/'PROTOCOL.json']},physical_validation=False,training_ready=False)
f=W/'INSTANT_GUARD_DRIVER_VERSION_CHECK.json';assert not f.exists();f.write_text(json.dumps(out,indent=2));print('PASS original36/80/56/10 preserved; explicit final-load pressure10; no launch')
