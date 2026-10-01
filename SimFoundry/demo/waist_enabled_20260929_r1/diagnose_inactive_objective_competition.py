"""Read-only task-objective decomposition on all8 complete precise5N pushes.
Opposing active/inactive waist gradients indicate local objective competition,
not a demonstrated controller defect or evidence that relaxing a term is safe.
Uses actual recorded commands, clipped original task errors and logged Jacobian.
Non-rear Jacobians are sampled only; missing rows are explicitly counted, never
claimed as complete-frame objective evidence. No Jacobian is invented.
"""
from pathlib import Path
import json,hashlib,datetime
import numpy as np
w=Path(__file__).resolve().parent;r=w/'precise_interior_groups_r1';protocol=json.loads((r/'PROTOCOL.json').read_text());out=[];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for command in protocol['commands']:
 if command['wait']:continue
 for task in command['tasks']:
  ep=r/f"case_{command['layout_id']}"/f"layout_{command['layout_id']}_{task}";side='right' if 'push_box' in task else 'left';inactive='left' if side=='right' else 'right';active=slice(3,6) if side=='right' else slice(0,3);other=slice(0,3) if side=='right' else slice(3,6)
  with np.load(ep/'raw.npz') as z:q=z['q'][:,12:23].copy();u=z['action'][:,12:23].copy()
  cs={c['step']:c for c in json.loads((ep/'coordination.json').read_text())};fr=json.loads((ep/'frontal_bypass.json').read_text());records=[];untraced=[];total_push=0
  for f in fr['rows']:
   if f['mode']!='top_push':continue
   total_push+=1;t=f['step'];c=cs[t]
   if 'control_jacobian_world' not in c:untraced.append(t);continue
   J=np.array(c['control_jacobian_world'],dtype=np.float32).astype(float);assert J.shape==(6,11)
   edge=c.get('joint_edge_refinement');parent=np.array(edge['parent_final_upper_command'],np.float32) if edge else u[t]
   if edge:assert np.array_equal(np.array(edge['final_upper_command'],np.float32),u[t])
   error=[];raw_error={}
   for name in ['left','right']:
    target=np.array(f['target_xyz'] if name==side else c['inactive_anchor'],np.float32);observed=np.array(c['control_point_positions'][name],np.float32);raw_error[name]=target-observed;error.extend(np.clip(np.float32(.72)*(target-observed),np.float32(-.035),np.float32(.035)).tolist())
   dq=parent.astype(float)-q[t].astype(float);residual=J@dq-np.array(error);ga=float(J[active,0]@residual[active]);gi=float(J[other,0]@residual[other]);records.append(dict(step=t,active_reference_error_mm=float(np.linalg.norm(raw_error[side])*1000),inactive_anchor_error_mm=float(np.linalg.norm(raw_error[inactive])*1000),active_linear_residual_mm=float(np.linalg.norm(residual[active])*1000),inactive_linear_residual_mm=float(np.linalg.norm(residual[other])*1000),active_waist_gradient=ga,inactive_waist_gradient=gi,opposed=ga*gi<0,waist_state_rad=float(q[t,0]),waist_command_rad=float(parent[0]),task_override=c['self_clearance_task']['override']))
  assert records
  a=lambda k:np.array([v[k] for v in records])
  summary=dict(total_push_frames=total_push,jacobian_traced_push_frames=len(records),untraced_push_frames=len(untraced),inactive_error_quantiles_mm=np.quantile(a('inactive_anchor_error_mm'),[.1,.5,.9]).tolist(),active_error_quantiles_mm=np.quantile(a('active_reference_error_mm'),[.1,.5,.9]).tolist(),inactive_linear_residual_quantiles_mm=np.quantile(a('inactive_linear_residual_mm'),[.1,.5,.9]).tolist(),active_linear_residual_quantiles_mm=np.quantile(a('active_linear_residual_mm'),[.1,.5,.9]).tolist(),opposed_waist_gradients=sum(x['opposed'] for x in records),waist_command_at_bound=sum(abs(x['waist_command_rad'])>=.9799 for x in records),task_overrides=sum(x['task_override'] for x in records))
  out.append(dict(episode=ep.name,summary=summary,records=records,untraced_steps=untraced,source_sha256={n:sha(ep/n) for n in ['raw.npz','coordination.json','frontal_bypass.json']}));print(ep.name,summary,flush=True)
assert len(out)==8
(w/'INACTIVE_OBJECTIVE_COMPETITION.json').write_text(json.dumps(dict(scope=__doc__,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),episodes=out,source_sha256={str(p):sha(p) for p in [Path(__file__),r/'PROTOCOL.json',r/'RESULT.json']},controller_changed=False,training_ready=False),indent=2))
