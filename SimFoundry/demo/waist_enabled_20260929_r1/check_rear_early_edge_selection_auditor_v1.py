"""Historical-input probe of earlier 20mm rear-box edge intervention.

Only changes near-edge eligibility from10mm to20mm in an isolated function.
Original equations, X slew, forward-Y scaling, Z and mode/load guards retained.
No simulator/controller edits, new physical outcomes, or data admission.
"""
from pathlib import Path
import ast
import copy
import datetime
import hashlib
import itertools
import importlib.util
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from audit_rear_early_edge_selection_v1 import verify_selection
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import linprog

W=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
sources={}
def bound(p):sources[str(p)]=sha(p);return p
def read(p):return json.loads(bound(p).read_text())
src=W/'staged_front_box_trailing_v2/rear_joint_xy_progress.py'
text=bound(src).read_text();old='size[:2]/2-abs(cop[:2])<.010';assert text.count(old)==1
def make(source):
    env={'np':np,'itertools':itertools}
    node=next(x for x in ast.parse(source).body if isinstance(x,ast.FunctionDef) and x.name=='govern_rear_joint_xy')
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(src),'exec'),env)
    return env['govern_rear_joint_xy']
original=make(text);candidate=make(text.replace(old,'size[:2]/2-abs(cop[:2])<.020'))
independent_source=W/'audit_substep_rear_xy.py'
independent_text=bound(independent_source).read_text()
node=next(n for n in ast.parse(independent_text).body if isinstance(n,ast.FunctionDef) and n.name=='independent_joint_xy')
independent_function_text=ast.unparse(node)
assert independent_function_text.count('< 0.01')==1
independent_function_text=independent_function_text.replace('< 0.01','< 0.02')
env={'np':np,'linprog':linprog}
exec(compile(independent_function_text,str(independent_source),'exec'),env)
independent=env['independent_joint_xy']
candidate_path=W/'staged_rear_early_edge_v1/rear_early_edge_governor.py'
spec=importlib.util.spec_from_file_location('rear_early_edge_candidate',bound(candidate_path));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
helper=module.govern_rear_joint_xy_early
prefix=candidate_path.read_text().split('\n\ndef govern_rear_joint_xy_early',1)[0].rstrip()+'\n'
restored=prefix.replace('def _govern(*, edge_margin_m, enabled, mode, previous_xyz, parent_xyz,','def govern_rear_joint_xy(*, enabled, mode, previous_xyz, parent_xyz,').replace('size[:2]/2-abs(cop[:2])<edge_margin_m','size[:2]/2-abs(cop[:2])<.010')
assert restored==text
records=[];protected=0;disabled_identity=0;left_identity=0;sample=None
for version in ['r1','r2']:
    ep=W/('front_box_trailing_physical_'+version)/'case_840023/layout_840023_push_box_to_bin'
    fr=read(ep/'frontal_bypass.json');rows=fr['rows'];size=fr['plan']['rear_cop_centering']['actual_core_size_xyz'];direction=fr['plan']['direction']
    packets={r['after_action_step']:r for r in read(ep/'solved_contact_forces.json')['rows']}
    with np.load(bound(ep/'trace.npz')) as z:xyz=z['box'].copy()
    with np.load(bound(ep/'parcel_orientation.npz')) as z:quat=z['box'].copy()
    previous=None
    for row in rows:
        t=row['step'];feedback=row.get('rear_cop_centering',{})
        if feedback.get('override'):
            assert previous is not None and row['mode']=='top_push'
            rot=Rotation.from_quat(quat[t]).as_matrix();points=[];weights=[]
            for c in packets[t-1]['parcel_contacts']:
                slots=[i for i,s in enumerate(c['shapes']) if '/parcel_box/' in s]
                if len(slots)!=1 or not any('right_wrist' in s for s in c['shapes']):continue
                f=np.asarray(c['force_world_N'])*(1 if slots[0]==1 else -1);load=-float(f@rot[:,2])
                if load>.05:points.append(c['position_world']);weights.append(load)
            assert sum(weights)>=.3
            cop_world=np.average(points,axis=0,weights=weights)
            np.testing.assert_allclose(cop_world,feedback['cop_world'],atol=2e-6,rtol=0)
            args=dict(enabled=True,mode=row['mode'],previous_xyz=previous,parent_xyz=feedback['command_xyz'],reference_xyz=row['observed_support_xyz'],object_rotation=rot,core_size=size,cop_local=rot.T@(cop_world-xyz[t]),normal_load_n=sum(weights),direction=direction)
            before=copy.deepcopy(args);got=original(**args);saved=row['rear_joint_xy_progress']
            assert got['override']==saved['override'] and got['reason']==saved['reason'],(version,t,got,saved)
            for k in ['command_xyz','scale','projected_local_xy_delta_m','constraints_mm','rhs_mm']:
                if k in got:np.testing.assert_allclose(got[k],saved[k],atol=2e-7,rtol=0,err_msg=f'{version}:{t}:{k}')
            proposed=candidate(**args)
            checked=independent(np.array(previous),np.array(args['parent_xyz']),np.array(args['reference_xyz']),rot,np.array(size),args['cop_local'],direction)
            assert proposed['override']==checked['override'] and proposed['reason']==checked['reason'],(version,t,proposed,checked)
            for k in ['command_xyz','scale','projected_local_xy_delta_m','constraints_mm','rhs_mm']:
                if k in proposed:np.testing.assert_allclose(proposed[k],checked[k],atol=2e-7,rtol=0)

            for k in args:
                if isinstance(args[k],(list,np.ndarray)):np.testing.assert_array_equal(args[k],before[k])
                else:assert args[k]==before[k]
            assert helper(early_enabled=False,side='right',**args)==got
            assert helper(early_enabled=True,side='left',**args)==got
            disabled_identity+=1;left_identity+=1
            combined=helper(early_enabled=True,side='right',**args)
            assert verify_selection(observed=combined,early_enabled=True,side='right',**args)['passed']
            assert verify_selection(observed=helper(early_enabled=False,side='right',**args),early_enabled=False,side='right',**args)['passed']
            assert verify_selection(observed=helper(early_enabled=True,side='left',**args),early_enabled=True,side='left',**args)['passed']
            selected={k:v for k,v in combined.items() if k!='early_edge'}
            expected=proposed if proposed['override'] else got
            assert selected==expected
            sample=copy.deepcopy(args)
            parent=np.asarray(args['parent_xyz']);fallback=np.asarray(row['rear_coupled_progress'].get('command_xyz',parent))
            oldcmd=np.asarray(got.get('command_xyz',fallback));newcmd=np.asarray(selected.get('command_xyz',fallback))
            np.testing.assert_allclose(oldcmd,row['target_xyz'],atol=2e-7,rtol=0,err_msg=f'{version}:{t}:composed original command')
            changed=bool(np.max(abs(newcmd-oldcmd))>1e-10)
            records.append(dict(version=version,step=t,original_reason=got['reason'],candidate_reason=proposed['reason'],original_override=got['override'],candidate_override=proposed['override'],changed=changed,old_command_xyz=oldcmd.tolist(),new_command_xyz=newcmd.tolist(),new_minus_old_mm=((newcmd-oldcmd)*1000).tolist(),margin_mm=((np.asarray(size[:2])/2-abs(args['cop_local'][:2]))*1000).tolist(),candidate_scale=proposed.get('scale'),independent_LP_checked=True,complete_original_governor_preserved=not proposed['override'],effective_selected_reason=selected['reason'],effective_selected_override=selected['override']))
        previous=row['target_xyz']
assert sample is not None
mutation_rejections=[]
for label in ['selected_flag','warning_margin','parent_reason','candidate_reason','top_reason']:
    observed=helper(early_enabled=True,side='right',**sample)
    if label=='selected_flag':observed['early_edge']['candidate_selected']=not observed['early_edge']['candidate_selected']
    elif label=='warning_margin':observed['early_edge']['warning_inset_m']=.03
    elif label=='parent_reason':observed['early_edge']['parent_result']['reason']='tampered'
    elif label=='candidate_reason':observed['early_edge']['candidate_result']['reason']='tampered'
    else:observed['reason']='tampered'
    try:verify_selection(observed=observed,early_enabled=True,side='right',**sample)
    except AssertionError:mutation_rejections.append(label)
    else:raise AssertionError(label)

for changes in [dict(mode='top_lift'),dict(mode='top_release'),dict(normal_load_n=.2),dict(cop_local=None)]:
    args=copy.deepcopy(sample);args.update(changes);expected=original(**args);observed=helper(early_enabled=True,side='right',**args)
    assert not observed['override'] and {k:v for k,v in observed.items() if k!='early_edge'}==expected
    protected+=1
negative=0
for key,value in [('enabled','true'),('direction',True),('direction',0),('normal_load_n',float('nan')),('normal_load_n',-.1),('parent_xyz',[0,0]),('reference_xyz',[0,float('inf'),0]),('object_rotation',np.zeros((3,3))),('core_size',[.01,.1,.1]),('cop_local',[float('nan'),0,0])]:
    args=copy.deepcopy(sample);args[key]=value
    try:helper(early_enabled=True,side='right',**args)
    except ValueError:negative+=1
    else:raise AssertionError(key)
for extra in [dict(early_enabled=1,side='right'),dict(early_enabled=True,side='center')]:
    try:helper(**extra,**sample)
    except ValueError:negative+=1
    else:raise AssertionError(extra)
for p,h in sources.items():assert sha(p)==h,p
sources[str(Path(__file__).resolve())]=sha(__file__)
sources[str(W/'audit_rear_early_edge_selection_v1.py')]=sha(W/'audit_rear_early_edge_selection_v1.py')
out=dict(selection_auditor_eligible_checks=3*len(records),selection_auditor_mutation_rejections=mutation_rejections,audit_family_ready=False,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,original_records_reproduced=len(records),disabled_identity=disabled_identity,left_identity=left_identity,protected_cases=protected,invalid_inputs_rejected=negative,independent_candidate_LPs_checked=len(records),original_composed_commands_reproduced=True,changed_records=sum(r['changed'] for r in records),records=records,source_sha256=sources,limitations=['Recorded parent inputs reused; changed candidate is not recursively replayed through its own prior commands.','Earlier activation may reduce progress or yield infeasible LPs; candidate preserves complete original jointXY result on fallback; future integration still requires all downstream guards.','20mm is an exploratory interior warning margin, not a revised quality threshold or demonstrated optimum.'],training_ready=False)
dest=W/'rear_early_edge_preparation_r1/INDEPENDENT_SELECTION_AUDITOR_CHECK_V1.json'
with dest.open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k not in ['records','source_sha256']},indent=2))
