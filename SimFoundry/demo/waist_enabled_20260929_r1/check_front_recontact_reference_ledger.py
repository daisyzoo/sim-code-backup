"""Source-bound parent parity plus explicit repeated-capture bookkeeping fixtures.
Fixture captures are not independently physics-certified and must never be
used as episode admission. Native event certification remains an upstream gate.
"""
from pathlib import Path
import copy,datetime,hashlib,json,sys
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W));sys.path.insert(0,str(W.parents[1]))
from front_initial_center_reference_ledger import verified_reference_lifetimes as old
from front_recontact_reference_ledger import verified_reference_lifetimes as new
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};parents=[]
for run in ['front_corridor_midpoint_physical_r1','front_drive_1mm_physical_r1']:
 ep=W/run/'case_840023/layout_840023_nudge_mailer_to_bin';fr=json.loads((ep/'frontal_bypass.json').read_text());stream=json.loads((ep/'front_initial_center.json').read_text());events={e['step']:e for e in stream['rows'] if e['kind'] in ('command','handover')}
 a=old(fr['rows'],events);b=new(fr['rows'],events,{},side='left')
 for key in ['centers','surface_local_by_step','handover_step','resets']:assert a[key]==b[key],key
 assert not b['recovery_centers'] and not b['recovery_handovers']
 parents.append(dict(run=run,frames=len(fr['rows']),first_capture_and_surface_exact=True))
 for p in [ep/'frontal_bypass.json',ep/'front_initial_center.json']:sources[str(p)]=sha(p)
# Explicit algebraic ledger fixture: initial capture -> inner reset -> recapture
# -> outer reset -> second recapture. Distinct centers expose stale references.
ci=[.1,.2,.3];c1=[.2,.3,.4];c2=[.3,.4,.5];s0=[0.,0.];s1=[.001,0.];s2=[0.,-.001]
rows=[]
for t in range(1,12):
 count=0 if t<4 else 1 if t<8 else 2
 row=dict(step=t,recontacts=count,mode='top_press' if t in [2,6,10] else 'top_cross',parcel_top_xyz=[0.,0.,1.])
 if t>=2:row['front_initial_captured_center_local']=ci
 if t>=6:row['front_recontact_captured_center_local']=c1 if t<10 else c2
 if t==4:row['last_recontact_reason']='lost_contact'
 if t==8:row.update(last_recontact_reason='front_route_direction_change',direction_change_recontact=dict(restarted=True))
 rows.append(row)
initial={2:dict(kind='handover',context=dict(recontacts=0),captured_center_local=ci,selected_surface_local_xy=s0)}
recovery={5:dict(kind='command',context=dict(recontacts=1),real_recontact_index=1),6:dict(kind='handover',context=dict(recontacts=1),real_recontact_index=1,captured_center_local=c1,selected_surface_local_xy=s1),9:dict(kind='command',context=dict(recontacts=2),real_recontact_index=2),10:dict(kind='handover',context=dict(recontacts=2),real_recontact_index=2,captured_center_local=c2,selected_surface_local_xy=s2)}
r=new(rows,initial,recovery,side='left');assert r['surface_local_by_step']=={2:s0,3:s0,4:s0,6:s1,7:s1,10:s2,11:s2};assert r['centers']=={t:ci if t<6 else c1 if t<10 else c2 for t in range(2,12)}
negative=[]
for label in ['missing_handover','stale_recovery','changed_initial','wrong_counter','wrong_binding','right_side','duplicate_capture','counter_jump','early_capture_field','overlapping_events','guard_on_event','missing_step','missing_reset_reason','outer_reset_wrong_reason']:
 rr=copy.deepcopy(rows);aa=copy.deepcopy(initial);bb=copy.deepcopy(recovery);side='left'
 if label=='missing_handover':bb.pop(6)
 elif label=='stale_recovery':rr[9]['front_recontact_captured_center_local']=c1
 elif label=='changed_initial':rr[6]['front_initial_captured_center_local']=c1
 elif label=='wrong_counter':bb[6]['context']['recontacts']=2
 elif label=='wrong_binding':bb[6]['real_recontact_index']=2
 elif label=='right_side':side='right'
 elif label=='duplicate_capture':bb[7]=copy.deepcopy(bb[6]);rr[6]['mode']='top_press'
 elif label=='counter_jump':rr[3]['recontacts']=2
 elif label=='early_capture_field':rr[4]['front_recontact_captured_center_local']=c1
 elif label=='overlapping_events':aa[5]=copy.deepcopy(aa[2])
 elif label=='guard_on_event':rr[4]['route_stop_reason']='parent_guard'
 elif label=='missing_step':rr.pop(3)
 elif label=='missing_reset_reason':rr[3].pop('last_recontact_reason')
 elif label=='outer_reset_wrong_reason':rr[7]['last_recontact_reason']='lost_contact'
 try:new(rr,aa,bb,side=side)
 except (AssertionError,ValueError,KeyError):negative.append(label)
 else:raise AssertionError('accepted bad ledger '+label)
# Recovery after first-landing fallback is supported explicitly.
rr=copy.deepcopy(rows);aa={}
for row in rr:row.pop('front_initial_captured_center_local',None)
b=new(rr,aa,recovery,side='left');assert min(b['centers'])==6 and b['handover_step'] is None and not b['initial_centers']
for p in [Path(__file__),W/'front_recontact_reference_ledger.py',W/'front_initial_center_reference_ledger.py']:sources[str(p)]=sha(p)
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,parent_parity=parents,repeated_capture_fixture=r,negative_cases=negative,initial_fallback_then_recovery_checked=True,source_sha256=sources,episode_audit_integrated=False,simulation_started=False,training_ready=False)
with (W/'staged_front_recontact_center/REFERENCE_LEDGER_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,parent_frames=sum(x['frames'] for x in parents),negative_cases=len(negative))))
