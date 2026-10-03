"""Standalone diagnostic for new projection stops; never replaces full audits."""
from pathlib import Path
import ast,json,hashlib,sys,datetime
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
from front_projection_stage_source_binding import verify_trial_provenance
from front_projection_stop_context import verify
from audit_unloaded_wrist_prior_live import HandModel,near

def inspect(ep):
 ep=Path(ep).resolve();prov,_,_=verify_trial_provenance(ep.parent);sources={};sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
 def read(p):sources[str(p)]=sha(p);return json.loads(p.read_text())
 clear=read(ep/'self_clearance.json');failure=clear['failure'];quality=read(ep/'quality.json');result={}
 with np.load(ep/'raw.npz') as z:frames=len(z['q']);meta=json.loads(str(z['collect_meta']));last=z['action'][-1,12:23].astype(float)
 assert meta['front_loaded_material_projection'] is True and meta['self_clearance_failure']==failure
 assert frames==clear['recorded_frames']==quality['frames'];assert frames<=clear['requested_frames']
 if failure is None or failure.get('phase')!='front_loaded_reference_cap':
  result=dict(applicable=False,reason='no_projection_stop',training_ready=False)
 else:
  assert frames<clear['requested_frames'] and not quality['passed'];assert failure['step']==frames
  current=[r for r in clear['rows'] if r['step']==frames];assert len(current)==1 and current[0]['phase']=='pre'
  post=next(r for r in clear['rows'] if r['step']==frames-1 and r['phase']=='post');final=next(r for r in clear['rows'] if r['step']==frames-1 and r['phase']=='final_command')
  packets=read(ep/'solved_contact_forces.json')['rows'];assert len(packets)==frames
  fr=read(ep/'frontal_bypass.json');assert fr['rows'][-1]['step']==frames-1;near(failure['record']['previous_command_xy'],fr['rows'][-1]['target_xyz'][:2],0.)
  source=ROOT/'simfoundry/data/sorting_quality.py';assert sha(source)==prov['source_sha256']['simfoundry/data/sorting_quality.py']==sha(ep.parent/'source_snapshot/simfoundry/data/sorting_quality.py')
  tree=ast.parse(source.read_text());offset=np.array(ast.literal_eval(next(n.value for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PALM_OFFSET' for t in n.targets))),float)
  urdf=ROOT/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf';vertices=ROOT/'assets/robots/g1_hand_support_vertices.json';hand=HandModel(urdf,vertices)
  result=verify(failure,frames=frames,pre=current[0],previous_post=post,previous_final=final,previous_action=last,packet=packets[-1],hand=hand,palm_offset=offset);result['applicable']=True
  for p in [source,urdf,vertices]:sources[str(p)]=sha(p)
 for p in [Path(__file__),W/'front_projection_stop_context.py',W/'front_loaded_projection_independent_math.py',W/'audit_unloaded_wrist_prior_live.py',ep/'raw.npz',ep.parent/'provenance.json']:sources[str(p)]=sha(p)
 return dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),episode=ep.name,diagnostic_completed=True,result=result,source_sha256=sources,training_ready=False)
if __name__=='__main__':
 ep=Path(sys.argv[1]).resolve();out=ep/'FRONT_PROJECTION_STOP_CONTEXT_DIAGNOSTIC.json';assert not out.exists();result=inspect(ep);out.write_text(json.dumps(result,indent=2));print(json.dumps(result['result'],indent=2))
