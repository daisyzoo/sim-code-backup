"""Compare exact new commands and real parser prelaunch settings to parent profile.
Post-AppLauncher resolved settings are checked later by actual source provenance.
"""
from pathlib import Path
import sys,json,datetime,hashlib
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W.parents[1])]
from prepare_closed_peak_trial import parser_namespace
from simfoundry.data.waist_pilot_protocol import semantic_settings
P=W/'inactive_transport_physical_preparation_r1';plan=json.loads((P/'PLAN.json').read_text());parent=json.loads((W/'front_box_recenter_preparation_r2/PLAN.json').read_text());assert len(plan['commands'])==len(parent['commands'])==6;rows=[]
for a,b in zip(plan['commands'],parent['commands']):
 args=list(a['args']);assert args.pop()=='--inactive-transport-clearance';args[args.index('--out-dir')+1]=b['args'][b['args'].index('--out-dir')+1];assert args==b['args'];assert a['tasks']==b['tasks'] and a['layout_id']==b['layout_id'] and a['wait']==b['wait']
 ns,_=parser_namespace(Path(plan['collector']),a['args'],full=True);settings=semantic_settings(ns)
 for key in ['inactive_transport_clearance','front_box_recenter','front_recontact_center_landing','front_corridor_midpoint_replan','front_loaded_z_priority','front_initial_center_landing','terminal_release_margin','edge_clearance_intersection']:assert settings.pop(key) is True
 assert settings==json.loads((W/'staged_closed_peak_trial/TRIAL_PROFILE.json').read_text())['prelaunch_settings']
 rows.append(dict(layout_id=a['layout_id'],tasks=a['tasks'],only_new_flag_and_output_directory_changed=True))
assert sum(len(r['tasks']) for r in rows)==10
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,commands=rows,source_sha256={str(x):sha(x) for x in [Path(__file__),P/'PLAN.json',W/'front_box_recenter_preparation_r2/PLAN.json',Path(plan['collector']),W/'staged_closed_peak_trial/TRIAL_PROFILE.json']},driver_ready=False,full_preflight_passed=False,physics_started=False,training_ready=False)
with (P/'PLAN_CONFIGURATION_CHECK.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(dict(passed=True,configurations=6,conditions=10,physics=False)))
