"""Read-only observed COP versus virtual reference decomposition on four rear runs.
Coordinates are object-local millimetres at the same observation step. Exact
geometric identities do not establish causal dynamics, friction or IK validity.
COP is previous solved final-substep and the support reference is virtual.
The command is issued for the NEXT action at this observation, so measured minus
command is a same-step command lead/gap, NOT measured tracking error. Component
medians need not sum to the median total. Reference selection uses hand geometry
and captured center; proximity to COP is not independent contact validation.
"""
from pathlib import Path
import json,hashlib,datetime
import numpy as np
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent;source=w/'recontact_interior_load3_groups_r1/CONTACT_EXIT_COMPARISON.json';parent=json.loads(source.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();reports=[]
for e in parent['episodes']:
 ep=next((w/e['run']).glob('case_*/'+e['episode']));target='box' if 'push_box' in ep.name else 'mailer'
 for name,h in e['source_sha256'].items():assert sha(ep/name)==h
 with np.load(ep/'trace.npz') as z:xyz=z[target].copy()
 with np.load(ep/'parcel_orientation.npz') as z:R=Rotation.from_quat(z[target]).as_matrix()
 rows={x['step']:x for x in json.loads((ep/'frontal_bypass.json').read_text())['rows']};bouts=[]
 for b in e['bouts']:
  if not b['first_loaded'] or not b['last_loaded']:continue
  samples=[]
  for label in ['first_loaded','last_loaded']:
   raw=b[label];t=raw['step'];row=rows[t];cop=np.array(raw['cop_local_mm']);local=lambda key:R[t].T@(np.array(row[key])-xyz[t])*1000
   measured=local('observed_support_xyz');command=local('target_xyz');selected=local('parcel_top_xyz')
   parts={'cop_minus_measured_reference_mm':cop-measured,'measured_minus_command_mm':measured-command,'command_minus_selected_mm':command-selected}
   assert np.max(abs(sum(parts.values())-(cop-selected)))<1e-9
   samples.append(dict(label=label,step=t,cop_local_mm=cop.tolist(),measured_reference_local_mm=measured.tolist(),command_reference_local_mm=command.tolist(),selected_local_mm=selected.tolist(),cop_minus_selected_mm=(cop-selected).tolist(),decomposition={k:v.tolist() for k,v in parts.items()}))
  first,last=samples;changes={k:(np.array(last['decomposition'][k])-first['decomposition'][k]).tolist() for k in first['decomposition']}
  bouts.append(dict(start=b['start'],end=b['end'],exit_reason=b['exit_reason'],object_signed_y_progress_mm=b['object_signed_y_progress_mm'],samples=samples,component_change_mm=changes,cop_local_change_mm=(np.array(last['cop_local_mm'])-first['cop_local_mm']).tolist()))
 lost=[b for b in bouts if b['exit_reason']=='lost_contact'];keys=list(bouts[0]['samples'][0]['decomposition'])
 summary=dict(lost_bouts=len(lost),lost_median_local_cop_delta_mm=np.median([b['cop_local_change_mm'] for b in lost],axis=0).tolist(),lost_median_component_delta_mm={k:np.median([b['component_change_mm'][k] for b in lost],axis=0).tolist() for k in keys})
 reports.append(dict(run=e['run'],episode=e['episode'],summary=summary,bouts=bouts,source_sha256=e['source_sha256']));print(e['run'],e['episode'],summary,flush=True)
(w/'REAR_COP_REFERENCE_DECOMPOSITION.json').write_text(json.dumps(dict(scope=__doc__,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),episodes=reports,source_sha256={str(source):sha(source),str(Path(__file__)):sha(Path(__file__))},training_ready=False),indent=2))
