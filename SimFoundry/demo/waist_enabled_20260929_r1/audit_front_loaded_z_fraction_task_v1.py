"""Independent binding of a declared reduced Z task, without runtime imports.
Caller must separately prove original parent, lifecycle, physical observations,
nominal certificate, fallback decisions and final downstream command. This only
proves that the declared fraction changes exactly the selected linear Z target.
"""
import copy
import numpy as np

def verified_task(original_task,metadata,expected_fraction):
 assert type(expected_fraction) in (float,int) and np.isfinite(expected_fraction) and 0<expected_fraction<=1
 block=metadata.get('reduced_z_task')
 if block is None:
  assert expected_fraction==1 or 'solver' not in metadata,'reduced solve missing bound task'
  return original_task
 assert expected_fraction<1 and metadata['selected'] is True and metadata['context']['selected'] is True
 assert block['fraction']==expected_fraction and type(block['fraction']) is float
 assert block['original_task']==original_task,'original task mismatch'
 c=metadata['context'];assert c['mode']=='top_push' and c['side'] in ['left','right'];assert c['observed_vertical_load_n']>=.3
 q=np.asarray(original_task['current'],float);p=np.asarray(c['parent_command'],float);J=np.asarray(original_task['jacobian'],float);error=np.asarray(original_task['error'],float);zr=2 if c['side']=='left' else 5
 assert q.shape==p.shape==(11,) and J.shape==(9,11) and error.shape==(9,)
 assert np.isfinite(q).all() and np.isfinite(p).all() and np.isfinite(J).all() and np.isfinite(error).all()
 np.testing.assert_allclose(c['current'],q,atol=1e-7,rtol=0);np.testing.assert_allclose(c['previous'],original_task['previous'],atol=1e-7,rtol=0)
 requested=float(error[zr]);achieved=float(J[zr]@(p-q));assert requested<0 and achieved>requested
 assert block['parent_linear_z_m']==achieved and block['original_requested_z_m']==requested==c['requested_z_m']
 expected=achieved+float(expected_fraction)*(requested-achieved);assert requested<expected<achieved
 assert block['modified_requested_z_m']==expected
 task=copy.deepcopy(original_task);task['error'][zr]=expected
 assert block['modified_task']==task,'non-Z changes or inconsistent reduced target'
 return task
