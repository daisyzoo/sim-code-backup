"""Independent replay of the new recorded front lead/anchor/slew contract."""
from pathlib import Path
import sys,json,hashlib,math

p=Path(sys.argv[1]);doc=json.loads((p/'frontal_bypass.json').read_text())
assert doc['plan']['front_route_live_guards']['object_relative_lead']
assert doc['plan']['front_route_live_guards']['object_relative_lead_limit_m']==.012
rows=doc['rows'];anchor=None;previous=None;errors=[];segments=[];maximum=0.;count=0
for r in rows:
    if r['mode']!='top_push':
        anchor=None;previous=None;continue
    target=r['observed_target'];tip=r['observed_support_xyz']
    if anchor is None:
        anchor=[tip[i]-target[i] for i in (0,1)]
        segments.append(dict(first_step=r['step'],anchor_xy_m=anchor))
    goal_y=r['clearance_progress']['front_hold_y'] if r['route_stage']=='front_x' else doc['plan']['front_route_candidates']['goal_y']
    goals=[r['route_goal_x'],goal_y]
    desired=[target[i]+anchor[i]+max(-.012,min(.012,goals[i]-target[i])) for i in (0,1)]
    base=previous if previous is not None else tip
    # Registered experiment uses3mm XY slew; no controller helper imported.
    command=[base[i]+max(-.003,min(.003,desired[i]-base[i])) for i in (0,1)]
    values=[*r['object_relative_contact_anchor_xy_m'],*r['object_relative_desired_xy_m'],*r['target_xyz']]
    assert all(math.isfinite(v) for v in values)
    error=max([abs(anchor[i]-r['object_relative_contact_anchor_xy_m'][i]) for i in (0,1)]+[abs(desired[i]-r['object_relative_desired_xy_m'][i]) for i in (0,1)]+[abs(command[i]-r['target_xyz'][i]) for i in (0,1)])
    maximum=max(maximum,error);count+=1
    if error>1e-7:errors.append(dict(step=r['step'],max_error_m=error))
    previous=r['target_xyz']
assert count,'No object-relative push rows'
out=dict(passed=not errors,push_frames=count,contact_segments=segments,max_recompute_error_m=maximum,errors=errors,raw_sha256=hashlib.sha256((p/'raw.npz').read_bytes()).hexdigest(),frontal_sha256=hashlib.sha256((p/'frontal_bypass.json').read_bytes()).hexdigest(),scope='Independent recorded object-relative anchor, lead and3mm slew calculation only; no dynamics, contact stability, task, all-frame safety or training admission proof.',training_ready=False)
(p/'OBJECT_RELATIVE_FRONT_AUDIT.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
