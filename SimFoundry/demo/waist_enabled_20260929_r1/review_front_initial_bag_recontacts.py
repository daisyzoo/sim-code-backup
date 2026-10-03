"""Read-only actual RGB/external samples and observed recontact COP geometry.
Sheet creation does not mark visual review complete. COP uses previous action's
last solver tick, independently reconstructed by the bound prior diagnostic.
"""
from pathlib import Path
import json,hashlib,datetime
import numpy as np
from scipy.spatial.transform import Rotation
from PIL import Image,ImageDraw
W=Path(__file__).resolve().parent;E=W/'front_initial_physical_r1/case_840023/layout_840023_nudge_mailer_to_bin';OUT=E/'RECONTACT_DETAIL_PREPARATION.json';assert not OUT.exists();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda n:json.loads((E/n).read_text());track=read('FRONT_LOADED_TRACKING_RESIDUAL_V2_DIAGNOSTIC.json');mom=read('FRONT_INITIAL_CONTACT_MOMENT_DIAGNOSTIC.json');fr=read('frontal_bypass.json');by={r['step']:r for r in fr['rows']};cop={r['step']:r for r in mom['rows']};core=np.array(mom['core_size_xyz']);sources={str(Path(__file__)):sha(__file__)}
for report in [track,mom]:
 for p,h in report['source_sha256'].items():assert sha(p)==h
with np.load(E/'trace.npz') as z:xyz=z['mailer'].astype(float)
with np.load(E/'parcel_orientation.npz') as z:rotation=Rotation.from_quat(z['mailer']).as_matrix()
rows=[]
for b in track['bouts']:
 t=b['start'];r=by[t];c=cop[t];ref=rotation[t].T@(np.asarray(r['observed_support_xyz'])-xyz[t]);surface=rotation[t].T@(np.asarray(r['parcel_top_xyz'])-xyz[t]);actual=c['cop'];rows.append(dict(bout=b['bout'],step=t,core_size_xyz=core.tolist(),observed_support_in_object_frame_m=ref.tolist(),logged_surface_in_object_frame_m=surface.tolist(),actual_cop=actual,cop_support_distance_mm=None if actual is None else float(np.linalg.norm(ref[:2]-np.asarray(actual['local_m'])[:2])*1000),cop_core_margin_mm=None if actual is None else float(min(core[:2]/2-abs(np.asarray(actual['local_m'])[:2]))*1000),yaw_deg=c['target_yaw_deg'],tilt_rad=r['observed_parcel_tilt_rad'],full_bout_load24_mean_N=b['per_action24_load_mean_N']['mean'],reference_scope=r['support_reference_scope']))
selected=[]
for i in [1,3,5,8,10]:
 b=next(b for b in track['bouts'] if b['bout']==i)
 for t in [b['start']+8,b['end']-5]:selected.append(dict(bout=i,step=t))
with np.load(E/'raw.npz') as z:
 rgb=z['rgb'];assert rgb.shape[0]==1200;images={r['step']:Image.fromarray(rgb[r['step']].transpose(1,2,0)) for r in selected}
viewer=E.parent/('viewer_'+E.name);sheets={}
for kind,size in [('rgb',(320,240)),('external',(480,270))]:
 canvas=Image.new('RGB',(size[0]*2,(size[1]+24)*5));draw=ImageDraw.Draw(canvas)
 for i,r in enumerate(selected):
  t=r['step'];p=viewer/f'pre_{t//5*5:04d}.jpg';im=images[t] if kind=='rgb' else Image.open(p);canvas.paste(im.resize(size),((i%2)*size[0],(i//2)*(size[1]+24)));draw.text(((i%2)*size[0],(i//2)*(size[1]+24)+size[1]),f"bout {r['bout']} frame {t if kind=='rgb' else t//5*5} ({kind})")
  if kind=='external':sources[str(p)]=sha(p);r['external_frame']=t//5*5
 dest=E/f'RECONTACT_DETAIL_{kind.upper()}.jpg';assert not dest.exists();canvas.save(dest);sheets[str(dest)]=sha(dest)
for name in ['raw.npz','trace.npz','parcel_orientation.npz','frontal_bypass.json','FRONT_LOADED_TRACKING_RESIDUAL_V2_DIAGNOSTIC.json','FRONT_INITIAL_CONTACT_MOMENT_DIAGNOSTIC.json']:sources[str(E/name)]=sha(E/name)
OUT.write_text(json.dumps(dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,geometry=rows,selected=selected,sheets=sheets,source_sha256=sources,actual_visual_review='pending',training_ready=False),indent=2))
for r in rows:print(json.dumps({k:v for k,v in r.items() if k not in ['core_size_xyz','reference_scope','actual_cop']},ensure_ascii=False))
