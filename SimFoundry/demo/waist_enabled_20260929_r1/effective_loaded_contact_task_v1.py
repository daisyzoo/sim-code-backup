"""Uninstalled binding for a quarter-loaded parent contact target.
Only the downstream contact-height check uses the returned task. The caller must
retain the original full objective and every original tolerance/guard. This is
metadata/geometry binding, not a contact, stationarity, path or task certificate.
"""
import copy
import numpy as np

def resolve(coordinate,*,side,current,parent_command,quarter_enabled=False):
 if type(quarter_enabled) is not bool or side not in ('left','right'):raise ValueError('Explicit side and quarter flag required')
 task=coordinate['task_inputs'];loaded=coordinate['front_loaded_z_priority'];step=coordinate['step']
 if type(step) is not int or step<1 or type(loaded.get('applied')) is not bool:raise ValueError('Invalid current loaded record')
 q=np.asarray(current,dtype=float);p=np.asarray(parent_command,dtype=float)
 if any(z.shape!=(11,) or not np.isfinite(z).all() for z in [q,p]):raise ValueError('Finite11 context required')
 if not np.array_equal(p,p.astype(np.float32)) or not np.array_equal(p,loaded['output_command']):raise ValueError('Parent output binding mismatch')
 if not np.array_equal(q,task['current']):raise ValueError('Stale original task')
 base=dict(step=step,version='effective_loaded_contact_task_v1',quarter_enabled=quarter_enabled,loaded_applied=loaded['applied'],full_task_objective_unchanged=True,height_tolerance_m=2e-7,training_ready=False)
 if not loaded['applied'] or 'reduced_z_task' not in loaded:
  return copy.deepcopy(task),dict(base,target='original_task')
 if not quarter_enabled:raise ValueError('Reduced loaded parent requires explicit quarter configuration')
 r=loaded['reduced_z_task'];ctx=loaded['context'];zr=2 if side=='left' else 5
 if loaded['step']!=step or ctx['step']!=step or ctx['side']!=side or not np.array_equal(ctx['current'],q):raise ValueError('Stale reduced context')
 if r['fraction']!=.25 or isinstance(r['fraction'],bool):raise ValueError('Only frozen quarter fraction allowed')
 if r['original_task']!=task:raise ValueError('Changed original objective or constraints')
 J=np.asarray(task['jacobian'],float);e=np.asarray(task['error'],float);prior=np.asarray(ctx['parent_command'],float)
 if J.shape!=(9,11) or e.shape!=(9,) or prior.shape!=(11,) or not all(np.isfinite(z).all() for z in [J,e,prior]):raise ValueError('Invalid reduced task inputs')
 achieved=float(J[zr]@(prior-q));effective=achieved+.25*(float(e[zr])-achieved)
 if achieved<=e[zr]:raise ValueError('Reduced context did not require downward refinement')
 for name,value in [('parent_linear_z_m',achieved),('original_requested_z_m',float(e[zr])),('modified_requested_z_m',effective)]:
  if not np.isfinite(r[name]) or abs(r[name]-value)>1e-15:raise ValueError('Incorrect reduction '+name)
 expected=copy.deepcopy(task);expected['error'][zr]=effective
 if r['modified_task']!=expected:raise ValueError('Modification outside exact quarter height task')
 residual=float(J[zr]@(p-q)-effective)
 if not np.isfinite(residual) or abs(residual)>2e-7:raise ValueError('Parent does not satisfy original effective-height tolerance')
 return expected,dict(base,target='verified_effective_quarter_task',original_request_m=float(e[zr]),effective_request_m=effective,parent_effective_height_residual_m=residual,scope=__doc__)
