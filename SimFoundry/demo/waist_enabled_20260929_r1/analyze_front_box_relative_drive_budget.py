"""Read-only command-relative-to-object budget alongside actual loaded box bouts.
Command accumulation is not measured surface slip or a proved force cause. Use
separate material-motion reports for actual displacement; no policy change.
"""
from pathlib import Path
import json,hashlib,datetime
import numpy as np
W=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};runs=[]
for run in ['front_initial_physical_r1','front_z_priority_physical_r1']:
 ep=W/run/'case_840020/layout_840020_push_box_to_bin';fr=json.loads((ep/'frontal_bypass.json').read_text());aud=json.loads((ep/'FRONT_DIAGONAL_ENTRY_LIVE_AUDIT.json').read_text());assert aud['passed'] is True
 for name,h in aud['source_sha256'].items():assert sha(ep/name)==h
 with np.load(ep/'trace.npz') as z:xyz=z['box'].astype(float)
 records={r['step']:r for r in aud['records']};bouts=[];bout=None;near_zero_correction=[]
 for r in fr['rows']:
  f=r.get('cop_slip_following',{});selected=r['mode']=='top_push' and r['route_stage']=='lateral_y' and f.get('override') and f.get('route_axis_control',{}).get('active_axis')==1
  if not selected:
   if bout:
    bout['exit_mode']=r['mode'];bouts.append(bout);bout=None
   continue
  t=r['step'];assert t in records
  np.testing.assert_allclose(f['measured_cop_local'],records[t]['independent_cop_local_m'],atol=2e-6,rtol=0)
  emitted=np.array(r['target_xyz'][:2]);previous=np.array(f['previous_command_xy']);feed=np.array(f['object_anchor_translation_xy']);drive=np.array(f['drive_xy']);correction=np.array(f['slip_correction_xy'])
  np.testing.assert_array_equal(emitted,np.array(f['route_axis_control']['emitted_xy']));assert emitted[1]==f['command_xy'][1]
  desired=previous+feed+drive+correction;ref=np.array(f['reference_xy']);bounded=np.clip(desired,ref-.03,ref+.03);independent=previous+np.clip(bounded-previous,-.003,.003)
  np.testing.assert_allclose(independent,np.array(f['command_xy']),atol=2e-12,rtol=0)
  relative=-(emitted[1]-previous[1]-feed[1]);drive_mm=-drive[1]*1000;correction_mm=-correction[1]*1000
  clipped=abs(relative+drive[1]+correction[1])>1e-12
  if not clipped:assert abs(relative-(-drive[1]-correction[1]))<1e-12
  if bout is None:bout=dict(start=t,last=t,frames=0,relative_command_sum_mm=0.,drive_sum_mm=0.,transverse_correction_along_y_sum_mm=0.,clipped_frames=0,start_cop_local=f['measured_cop_local'],last_cop_local=f['measured_cop_local'])
  bout.update(last=t,last_cop_local=f['measured_cop_local']);bout['frames']+=1;bout['relative_command_sum_mm']+=1000*relative;bout['drive_sum_mm']+=drive_mm;bout['transverse_correction_along_y_sum_mm']+=correction_mm;bout['clipped_frames']+=int(clipped);near_zero_correction.append(abs(correction_mm))
 if bout:bout['exit_mode']='end_of_episode';bouts.append(bout)
 for b in bouts:
  b['actual_box_advance_mm']=float(1000*(xyz[b['start'],1]-xyz[min(b['last']+1,len(xyz)-1),1]));b['cop_local_y_shift_mm']=1000*(b['last_cop_local'][1]-b['start_cop_local'][1]);b['note']='COP endpoints are pressure centroids; not fixed material points. Command uses prior force packet and actual current observation.'
 complete=[b for b in bouts if b['frames']>=10]
 runs.append(dict(run=run,bouts=bouts,lateral_loaded_rows=sum(b['frames'] for b in bouts),long_bouts=len(complete),long_bout_median_relative_command_mm=float(np.median([b['relative_command_sum_mm'] for b in complete])),long_bout_median_actual_box_advance_mm=float(np.median([b['actual_box_advance_mm'] for b in complete])),long_bout_median_cop_y_shift_mm=float(np.median([b['cop_local_y_shift_mm'] for b in complete])),median_abs_transverse_correction_y_mm=float(np.median(near_zero_correction))))
 for name in ['frontal_bypass.json','FRONT_DIAGONAL_ENTRY_LIVE_AUDIT.json','CONTACT_SURFACE_MOTION_AUDIT.json','trace.npz']:sources[str(ep/name)]=sha(ep/name)
for p in [Path(__file__),W/'staged_front_loaded_z_priority/contact_slip_following.py',W/'staged_front_loaded_z_priority/front_initial_center_cop_route.py']:sources[str(p)]=sha(p)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,runs=runs,findings=['On non-clipped lateral rows, relative Y command increment equals nominal drive plus the retained transverse correction exactly. Object translation feed-forward does not cancel the added drive.','Cross-axis mixing replaces X; it leaves the Y drive untouched. Local Y COP drift toward the drive edge is not evidence that discarding X feedback alone is the cause.','Repeated positive relative command budget and actual material slip motivate evaluating sustained-contact control; this is not proof of a candidate fix. Do not restore the rejected fixed 10mm material cap or change current frozen physics.'],source_sha256=sources,physics_changed=False,training_ready=False)
with (W/'front_z_priority_physical_r1/BOX_RELATIVE_DRIVE_BUDGET_DIAGNOSTIC.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps([ {k:v for k,v in r.items() if k!='bouts'} for r in runs],indent=2))
