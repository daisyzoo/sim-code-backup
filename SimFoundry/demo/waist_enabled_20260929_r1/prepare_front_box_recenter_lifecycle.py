"""Prepare isolated right-box recovery lifecycle; leave every frozen source unchanged."""
from pathlib import Path
import json,hashlib,datetime
W=Path(__file__).resolve().parent;S=W/'staged_front_recontact_headroom';D=W/'front_box_recenter_draft_r1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
renames={f'front_recontact_center_{s}':f'front_box_recenter_{s}' for s in ['lifecycle_static','selection','lifecycle','runtime']}
rows=[]
for old,new in renames.items():
 p=S/(old+'.py');original=p.read_text();text=original;edits=[]
 for a,b in renames.items():
  if a in text:edits.append((a,b));text=text.replace(a,b)
 for a,b in [('front-bag','front-box'),("scene.side == 'left'","scene.side == 'right'"),("scene.side != 'left'","scene.side != 'right'"),("self.side!='left'","self.side!='right'")]:
  if a in text:edits.append((a,b));text=text.replace(a,b)
 reverse=text
 for a,b in reversed(edits):reverse=reverse.replace(b,a)
 assert reverse==original
 out=D/(new+'.py')
 with out.open('x') as f:f.write(text)
 compile(text,str(out),'exec');rows.append(dict(parent=str(p),parent_sha256=sha(p),path=str(out),sha256=sha(out),replacements=edits))
p=W/'audit_front_recontact_center_events.py';text=p.read_text();assert text.count("scene['side']=='left'")==1
text=text.replace("scene['side']=='left'","scene['side']=='right'")
# Preserve independently reconstructed original geometry, adding the existing
# headroom restrictions that the candidate already enforces.
text=text.replace("assert created is not None and created['accepted'] is True", "assert actual['inactive_lowest_z_m'] >= .841\n            assert created is not None and created['accepted'] is True")
text=text.replace("assert verified['accepted'];self.compare_geometry(p[key],verified)","assert verified['accepted'];assert verified['inactive_lowest_z_m'] >= .8405;self.compare_geometry(p[key],verified)")
out=D/'audit_front_box_recenter_events.py'
with out.open('x') as f:f.write(text)
compile(text,str(out),'exec')
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,adaptations=rows,independent_auditor=dict(parent=str(p),parent_sha256=sha(p),path=str(out),sha256=sha(out),changes=['right side eligibility','existing measured841mm entry and nominal/predicted840.5mm reserve assertions']),defaults_off=True,unwired=True,physics_started=False,training_ready=False,source_sha256={str(Path(__file__)):sha(__file__),str(S/'front_recontact_center_tracking.py'):sha(S/'front_recontact_center_tracking.py'),str(S/'front_recontact_center_adapter.py'):sha(S/'front_recontact_center_adapter.py')})
with (D/'LIFECYCLE_PREPARATION.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(modules=len(rows),independent_auditor=True,unwired=True)))
