"""All original10conditions, independently reconstructed24tick contact loads.
Default-off pressure result must equal original auditor exactly. No physics.
"""
from pathlib import Path
import datetime,hashlib,json,sys
import numpy as np
W=Path(__file__).resolve().parent;D=W/'front_normal_pressure_parent_stream_r1';D.mkdir(exist_ok=False);sys.path.insert(0,str(W))
from audit_front_normal_pressure_stream_v1 import verify_stream,independent_loads
from audit_front_effective_height_r1_v1_stage_pressure import verify_stream as original
read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();rows=[];sources={}
for item in read(W/'front_cross_track_full_stream_probe_r1/CENSUS.json')['episodes']:
 ep=Path(item['episode']);wait=item['wait'];p=read(ep/'peak_load_updates.json');n=p['executed_action_count'];fr=None if wait else read(ep/'frontal_bypass.json');loads={}
 if not wait:
  meta=read(ep/'SUBSTEP_CONTACT_RECORDING.json')['metadata']
  with np.load(ep/'substep_contacts.npz') as z:arrays={k:z[k] for k in z.files}
  loads=independent_loads(arrays,meta,'push_box_to_bin' if 'push_box' in ep.name else 'nudge_mailer_to_bin',n)
 a=verify_stream(p,fr,loads,frames=n,wait=wait);b=original(p,fr,loads,frames=n,wait=wait);assert a==b and a['passed']
 if not wait:(D/(ep.name+'_loads.json')).write_text(json.dumps(loads))
 row=dict(episode=str(ep),frames=n,wait=wait,pressure_updates=a['pressure_updates'],control_frames=a['control_frames'],off_equal_original=True)
 rows.append(row)
 for name in ['peak_load_updates.json','SUBSTEP_CONTACT_RECORDING.json','substep_contacts.npz']+([] if wait else ['frontal_bypass.json']):sources[str(ep/name)]=sha(ep/name)
 print(json.dumps(row),flush=True)
report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,passed=True,episodes=rows,frames=sum(r['frames'] for r in rows),pressure_updates=sum(r['pressure_updates'] for r in rows),source_sha256={**sources,**{str(p):sha(p) for p in [Path(__file__),W/'audit_front_normal_pressure_stream_v1.py',W/'audit_front_normal_pressure_finalization_v1.py',W/'audit_front_effective_height_r1_v1_stage_pressure.py',W/'audit_peak_load_update_math.py']}},physics_started=False,training_ready=False)
assert len(rows)==10 and report['frames']==9740
(D/'RESULT.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(passed=True,frames=report['frames'],pressure_updates=report['pressure_updates'])),flush=True)
