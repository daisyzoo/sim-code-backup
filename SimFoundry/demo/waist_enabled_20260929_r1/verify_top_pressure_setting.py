"""Bind a declared top-pressure setting to actual provenance and both recorded plans.
This verifies configuration identity only, not pressure tracking, task success,
audit completion or training eligibility. No controller imports or file rewrites.
"""
from pathlib import Path
import json,hashlib,sys,datetime
import numpy as np
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify(ep,expected):
 ep=Path(ep);assert .5<=expected<=5.;prov=json.loads((ep.parent/'provenance.json').read_text());args=prov['args'];assert args['expert_frontal_top_load_n']==expected,'actual CLI pressure differs'
 assert args['recontact_interior_preference'] and args['unloaded_recontact_pose'] and args['role']=='diagnostic'
 with np.load(ep/'raw.npz') as z:
  task=str(z['task_id']);meta=json.loads(str(z['collect_meta']));assert meta['assist_frames']==0 and not meta['push_assist'];assert np.max(abs(z['q'][0,12:23]))<1e-4 and np.max(abs(z['action'][0,12:23]))==0
 if task!='wait_no_package':
  fr=json.loads((ep/'frontal_bypass.json').read_text());assert fr['plan']['top_recontact']['desired_vertical_load_n']==expected,'episode plan pressure differs';assert meta['frontal_bypass_plan']['top_recontact']['desired_vertical_load_n']==expected,'raw plan pressure differs'
 return dict(episode=ep.name,expected_top_load_n=expected,actual_cli_top_load_n=args['expert_frontal_top_load_n'],wait=task=='wait_no_package',passed=True,source_sha256={str(p):sha(p) for p in [ep.parent/'provenance.json',ep/'raw.npz']+([] if task=='wait_no_package' else [ep/'frontal_bypass.json'])})
def main(run,expected):
 r=Path(run).resolve();p=json.loads((r/'PROTOCOL.json').read_text());rows=[]
 for c in p['commands']:
  i=c['args'].index('--expert-frontal-top-load-n')+1;assert float(c['args'][i])==expected
  for task in c['tasks']:rows.append(verify(r/f"case_{c['layout_id']}"/f"layout_{c['layout_id']}_{task}",expected))
 assert len(rows)==10 and sum(x['wait'] for x in rows)==2
 out=dict(scope=__doc__,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,rows=rows,script_sha256=sha(__file__),protocol_sha256=sha(r/'PROTOCOL.json'),training_ready=False)
 dest=r/'PRESSURE_SETTING_BINDING.json';assert not dest.exists();dest.write_text(json.dumps(out,indent=2));print('BOUND10',expected)
if __name__=='__main__':main(sys.argv[1],float(sys.argv[2]))
