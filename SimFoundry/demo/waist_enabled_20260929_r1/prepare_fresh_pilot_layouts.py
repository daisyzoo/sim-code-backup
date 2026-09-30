"""Deterministic, continuous multi-family pilot proposal; no physics admission.
Category swaps hold the geometric slots/seed fixed. Validation geometry is
separated from train under permutation-invariant slot distance, before outcomes.
"""
from pathlib import Path
import hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;REPO=W.parents[1];sys.path.insert(0,str(REPO))
from simfoundry.data.diverse_layouts import validate_diagnostic_layout
from simfoundry.data.waist_group_audit import validate_complete_swap_layouts
from simfoundry.calibration.sorting_station import TABLE_TOP_BOX_Z,TABLE_TOP_MAILER_Z
SEED=2026093001;OUT=W/'fresh_pilot_layout_proposal_r1';rng=np.random.default_rng(SEED)
FAMILIES=('lateral','depth','diagonal','reverse_diagonal')
def family(a,b):
    dx,dy=b-a
    if abs(dx)<.08 and abs(dy)>.25:return 'lateral'
    if abs(dx)>.18 and abs(dy)<.075:return 'depth'
    if .09<abs(dx)<.22 and .17<abs(dy)<.32:return 'diagonal' if dx*dy<0 else 'reverse_diagonal'
    return None

def distance(a,b):
    return min(float(np.linalg.norm(a-b,axis=1).max()),float(np.linalg.norm(a-b[::-1],axis=1).max()))

def make_group(index,split,kind,slots,yaws):
    identifier=840000+index*2;name=f'fresh_{kind}_{index:02d}';seed=SEED+index
    common=dict(seed=seed,geometry_group=name,planned_split=split,geometry_family=kind)
    a=dict(common,layout_id=identifier,assignment='normal',box_xyz=[*slots[0].tolist(),TABLE_TOP_BOX_Z],mailer_xyz=[*slots[1].tolist(),TABLE_TOP_MAILER_Z],box_yaw=float(yaws[0]),mailer_yaw=float(yaws[1]))
    b=dict(common,layout_id=identifier+1,assignment='swapped',box_xyz=[*slots[1].tolist(),TABLE_TOP_BOX_Z],mailer_xyz=[*slots[0].tolist(),TABLE_TOP_MAILER_Z],box_yaw=float(yaws[1]),mailer_yaw=float(yaws[0]))
    for d in (a,b):validate_diagnostic_layout(d,d['layout_id'])
    validate_complete_swap_layouts([a,b])
    wait=dict(a,layout_id=841000+index,geometry_group=name+'_wait',geometry_family='empty_wait')
    validate_diagnostic_layout(wait,wait['layout_id'])
    return dict(layouts=[a,b],wait_layouts=[wait],training_ready=False,approved_for_pilot=False)

if __name__=='__main__':
    if OUT.exists():raise ValueError('Proposal already exists; never regenerate after outcomes')
    accepted=[];plans=[];tries=0
    # Two independent train groups and one validation group in each family.
    schedule=[(split,f) for split in ('train','train','validation') for f in FAMILIES]
    for index,(split,kind) in enumerate(schedule):
        for _ in range(100000):
            tries+=1;slots=rng.uniform([.39,-.16],[.60,.16],size=(2,2));slots=slots[np.argsort(slots[:,0])];yaws=rng.uniform(-.18,.18,size=2)
            if family(*slots)!=kind:continue
            # Predeclared separation; no simulation outcomes or independent-test
            # layouts used to choose geometry.
            if any(distance(slots,x['slots'])<(.04 if split!=x['split'] else .02) for x in accepted):continue
            try:plan=make_group(index,split,kind,slots,yaws)
            except ValueError:continue
            accepted.append(dict(slots=slots,split=split,family=kind));plans.append(plan);break
        else:raise RuntimeError('Unable to sample declared geometry strata')
    layouts=[d for p in plans for d in p['layouts']];validate_complete_swap_layouts(layouts)
    train=[x['slots'] for x in accepted if x['split']=='train'];val=[x['slots'] for x in accepted if x['split']=='validation']
    separation=min(distance(a,b) for a in train for b in val);assert separation>=.04
    OUT.mkdir();files={}
    for p in plans:
        name=p['layouts'][0]['geometry_group'];path=OUT/(name+'.json');path.write_text(json.dumps(p,indent=2));files[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
    report=dict(seed=SEED,groups=12,push_layouts=24,push_episodes=48,wait_episodes=12,train_groups=8,validation_groups=4,
        families={f:dict(train=2,validation=1) for f in FAMILIES},min_train_validation_slot_distance_m=separation,
        distance_definition='minimum over slot exchange of maximum of two XY Euclidean distances; yaw ignored conservatively',
        initial_x_range_m=[.39,.60],initial_y_range_m=[-.16,.16],yaw_range_rad=[-.18,.18],attempted_slot_pairs=tries,
        exact_category_counterfactual=True,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),plan_sha256=files,
        scope='Pre-outcome proposal only. Continuous positions/yaws, original footprint clearance, complete category swaps and group split. No independent-test layouts read. No physical success, contract or training admission claimed.',approved_for_pilot=False,training_ready=False)
    (OUT/'PROPOSAL.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
