"""Independent logged-bound diagnosis of material-cap stop; no control change.
Uses scalar box intersections, no production controller/helper imports. The
stop observation lacks q/quaternion in raw; logged stop material/hand geometry
is not falsely labelled independently pose-verified. Candidate relaxed point
is an unissued geometric alternative, not a physical counterfactual outcome.
"""
from pathlib import Path
import json,hashlib,datetime,sys
W=Path(__file__).resolve().parent;E=Path(sys.argv[1]).resolve();OUT=E/'LOADED_CAP_EMPTY_INTERSECTION_V2_DIAGNOSTIC.json';assert not OUT.exists();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda n:json.loads((E/n).read_text());failure=read('self_clearance.json')['failure'];assert failure['phase']=='front_loaded_reference_cap' and failure['reason']=='empty_original_slew_lead_material_intersection';r=failure['record'];assert r['command_xy'] is None and r['requires_recontact'] is True
previous=r['previous_command_xy'];parent=r['parent_xy'];hand=r['reference_xy'];material=r['material_surface_xy'];assert r['original_step_m']==.003 and r['original_hand_lead_m']==.030 and r['cap_xy_m']==.010
fr=read('frontal_bypass.json');last=fr['rows'][-1];assert last['step']==failure['step']-1;assert last['loaded_reference_cap']['command_xy']==previous==last['target_xyz'][:2]
sets={'original_command_slew':[[x-.003,x+.003] for x in previous],'original_hand_reference_lead':[[x-.030,x+.030] for x in hand],'new_material_cap':[[x-.010,x+.010] for x in material],'new_parent_direction_segment':[[min(x,y),max(x,y)] for x,y in zip(previous,parent)]}
def intersection(names):
 lower=[max(sets[name][axis][0] for name in names) for axis in range(2)];upper=[min(sets[name][axis][1] for name in names) for axis in range(2)]
 return dict(lower=lower,upper=upper,feasible=all(x<=y for x,y in zip(lower,upper)),positive_gap_m=[max(0,x-y) for x,y in zip(lower,upper)])
all_bounds=intersection(list(sets));assert all_bounds['lower']==r['lower'] and all_bounds['upper']==r['upper'] and not all_bounds['feasible']
base=intersection(['original_command_slew','original_hand_reference_lead']);without_segment=intersection(['original_command_slew','original_hand_reference_lead','new_material_cap']);assert base['feasible'] and without_segment['feasible']
alternative=[min(max(parent[i],without_segment['lower'][i]),without_segment['upper'][i]) for i in range(2)]
for i in range(2):assert abs(alternative[i]-previous[i])<=.003+1e-15 and abs(alternative[i]-hand[i])<=.030+1e-15 and abs(alternative[i]-material[i])<=.010+1e-15
packets=read('solved_contact_forces.json')['rows'];assert packets[-1]['after_action_step']==failure['step']-1;key='box' if fr['plan']['direction']==-1 else 'mailer';object_delta=[packets[-1]['post_action_pose'][key][i]-packets[-2]['post_action_pose'][key][i] for i in range(2)]
changes=[]
for row in fr['rows']:
 cap=row.get('loaded_reference_cap')
 if cap and cap.get('changed'):changes.append(row['step'])
quality=read('quality.json');assert not quality['passed'] and quality['frames']==failure['step']
sources={str(p):sha(p) for p in [Path(__file__),E/'self_clearance.json',E/'frontal_bypass.json',E/'solved_contact_forces.json',E/'quality.json',E/'raw.npz',E/'trace.npz',E/'parcel_orientation.npz',E/'peak_load_updates.json']}
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,episode=E.name,stop_step=failure['step'],recorded_frames=quality['frames'],constraint_sets=sets,original_bounds=base,all_candidate_bounds=all_bounds,without_added_direction_segment=without_segment,conflict_gap_micrometers=[x*1e6 for x in all_bounds['positive_gap_m']],last_applied_step=last['step'],first_changed_cap_step=min(changes),changed_cap_steps=changes,material_surface_delta_from_last_applied_m=[material[i]-last['loaded_reference_cap']['material_surface_xy'][i] for i in range(2)],independently_recorded_post_action_target_translation_delta_m=object_delta,unissued_geometric_alternative_xy=alternative,unissued_geometric_alternative_delta_from_previous_m=[alternative[i]-previous[i] for i in range(2)],stop_hand_material_pose_independently_verified=False,missing_evidence='No raw q or parcel quaternion at attempted stop step; report proves arithmetic conflict in logged bounds and binds previous emitted command/post-action translations, not independent full stop geometry.',interpretation='New material boundary lowerX exceeds prior emittedX, while added per-axis parent segment upperX equals priorX. Original slew/hand lead plus material box remain geometrically feasible. No arbitrary tolerance increase, original gate change, physical success, or training admission.',training_ready=False)
OUT.write_text(json.dumps(report,indent=2));print(json.dumps({k:report[k] for k in ['episode','stop_step','first_changed_cap_step','conflict_gap_micrometers','unissued_geometric_alternative_delta_from_previous_m','material_surface_delta_from_last_applied_m','independently_recorded_post_action_target_translation_delta_m']},indent=2))
