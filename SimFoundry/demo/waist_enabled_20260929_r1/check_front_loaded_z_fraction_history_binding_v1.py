"""Bind unchanged downstream runtime and history for the ongoing static stream probe.
No candidate runtime imports; no new physics. Confirms saved transport context
uses the actual preceding q/action and source files match the archived collector.
"""
from pathlib import Path
import json,hashlib,datetime
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'staged_front_corridor_lateral_v1';read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={};rows=[]
for case,task in [(840023,'nudge_mailer_to_bin'),(840020,'push_box_to_bin')]:
 ep=W/f'front_corridor_lateral_physical_r1/case_{case}/layout_{case}_{task}';provenance=read(ep.parent/'provenance.json');stage=[]
 for name,h in provenance['source_sha256'].items():
  archive=ep.parent/'source_snapshot'/name
  if Path(name).parent.name==S.name:
   p=S/Path(name).name;assert sha(p)==sha(archive)==h,name;sources[str(p)]=h;sources[str(archive)]=h;stage.append(p.name)
 assert 'joint_transport_runtime.py' in stage and 'loaded_z_priority_solver.py' in stage and 'front_loaded_z_priority.py' in stage
 with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23];u=z['action'][:,12:23]
 coords=read(ep/'coordination.json');assert len(coords)==1199
 for r in coords:
  t=r['step'];c=r['joint_transport_clearance']['collector_context'];np.testing.assert_array_equal(c['current'],q[t]);np.testing.assert_array_equal(c['previous_q'],q[t-1]);np.testing.assert_array_equal(c['previous_command'],u[t-1])
 rows.append(dict(episode=ep.name,actual_history_rows=len(coords),stage_sources=len(stage),passed=True))
 for p in [ep/'raw.npz',ep/'coordination.json',ep.parent/'provenance.json']:sources[str(p)]=sha(p)
sources[str(Path(__file__))]=sha(__file__);report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,source_sha256=sources,passed=True,physics_started=False,training_ready=False)
with (W/'front_loaded_z_fraction_candidate_v1/HISTORY_SOURCE_CHECK.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(passed=True,rows=rows)))
