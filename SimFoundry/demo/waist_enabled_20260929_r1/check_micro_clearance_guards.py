"""Meaningful rejection checks for history, current contact and guard precedence."""
from pathlib import Path
import sys,copy,json,hashlib
w=Path(__file__).resolve().parent;stage=w/'staged_micro_clearance_probe';sys.path.insert(0,str(stage))
from micro_clearance_return import MicroClearanceReturn
base=dict(previous_stage='front_x',current_stage='lateral_y',target_xy=[.401,.1],contact=dict(valid=True,normal_load_n=4.,weighted_contact_local=[0.,0.,.02]),core_size=[.13,.12,.04],restart_expected=True,terminal=False,tilted=False)
def prepared():
 s=MicroClearanceReturn();s.update(**dict(base,previous_stage='lateral_y',current_stage='front_x',target_xy=[.4,.1]));return s
checks=[]
for name in ['valid','initial_turn','large_excursion','returned_after_excursion','no_contact','low_normal','near_edge','not_original_restart','terminal','tilt','invalid_xy','invalid_load','invalid_core']:
 s=prepared();args=copy.deepcopy(base)
 if name=='initial_turn':s=MicroClearanceReturn()
 elif name=='large_excursion':args['target_xy']=[.406,.1]
 elif name=='returned_after_excursion':s.update(**dict(args,previous_stage='front_x',current_stage='front_x',target_xy=[.406,.1]))
 elif name=='no_contact':args['contact']=None
 elif name=='low_normal':args['contact']['normal_load_n']=.299
 elif name=='near_edge':args['contact']['weighted_contact_local'][0]=.06
 elif name=='not_original_restart':args['restart_expected']=False
 elif name=='terminal':args['terminal']=True
 elif name=='tilt':args['tilted']=True
 elif name=='invalid_xy':args['target_xy']=[float('nan'),0.]
 elif name=='invalid_load':args['contact']['normal_load_n']=float('nan')
 elif name=='invalid_core':args['core_size']=[.13,-.12,.04]
 try:r=s.update(**args)
 except ValueError:assert name.startswith('invalid_');checks.append(dict(case=name,invalid_rejected=True));continue
 assert not name.startswith('invalid_') and r['retained']==(name=='valid'),(name,r)
 checks.append(dict(case=name,retained=r['retained']))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();out=dict(passed=True,checks=checks,scope=__doc__,source_sha256={str(p):sha(p) for p in [Path(__file__),stage/'micro_clearance_return.py']},training_ready=False)
(stage/'GUARD_CHECK.json').write_text(json.dumps(out,indent=2));print('passed',len(checks),'direct history/contact/guard checks')
