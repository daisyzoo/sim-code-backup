"""Actual admitted RGB through production Pi0.5 resize; no policy inference.
Camera exclusion is geometry-only; human image review remains separate.
"""
from pathlib import Path
import argparse,ast,datetime,hashlib,json
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image,ImageDraw
W=Path(__file__).resolve().parent;SIM=W.parents[2]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main(run,out):
 run=Path(run).resolve();out=Path(out).resolve();assert not out.exists()
 admission=run/'GROUP_ADMISSIONS/fresh_diagonal_02.json';a=json.loads(admission.read_text());assert a['full_group_source_admitted']
 phasepath=run/'ADMITTED_DIAGONAL_EXPOSURE.json';phase=json.loads(phasepath.read_text());phase_by={x['episode_index']:x for x in phase['phase_metadata']['records']}
 policy=SIM/'lerobot/unitree_lerobot_yth_repro_20260908/unitree_lerobot_yth/unitree_lerobot/lerobot/src/lerobot/policies/pi05/modeling_pi05.py'
 cfg=SIM/'lerobot/models/pi05_base/config.json';assert json.loads(cfg.read_text())['image_resolution']==[224,224]
 node=next(n for n in ast.parse(policy.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='resize_with_pad_torch')
 namespace={'torch':torch,'F':F};exec(compile(ast.Module(body=[node],type_ignores=[]),str(policy),'exec'),namespace);resize=namespace['resize_with_pad_torch'];torch.set_num_threads(1)
 out.mkdir();sheet=Image.new('RGB',(896,1024));draw=ImageDraw.Draw(sheet);rows=[];sources={str(p):sha(p) for p in [admission,phasepath,policy,cfg,Path(__file__)]}
 for index,rec in enumerate(a['records']):
  if rec['task_id']=='wait_no_package':continue
  raw=Path(rec['path']);assert sha(raw)==rec['hash'];ep=raw.parent;fp=ep/'CAMERA_FRUSTUM_DIAGNOSIS.json';frustum=json.loads(fp.read_text());assert frustum['source_sha256']['raw.npz']==rec['hash']
  key='box' if rec['task_id']=='push_box_to_bin' else 'mailer';push=[r['step'] for r in frustum['rows'] if r['mode']=='top_push'];frames=[0,push[0],push[len(push)//2],push[-1]]
  with np.load(raw) as z:rgb=z['rgb'][frames].transpose(0,2,3,1).copy()
  assert rgb.shape==(4,480,640,3) and rgb.dtype==np.uint8
  processed=resize(torch.from_numpy(rgb).float()/127.5-1.,224,224);assert tuple(processed.shape)==(4,224,224,3)
  pixels=np.clip(np.round((processed.numpy()+1.)*127.5),0,255).astype(np.uint8);image_hashes={};row_index=len(rows)
  for col,t in enumerate(frames):
   name=f'{ep.name}_{t:04d}_model224.png';im=Image.fromarray(pixels[col]);im.save(out/name);image_hashes[name]=sha(out/name);sheet.paste(im,(col*224,row_index*256));draw.text((col*224,row_index*256+224),f'{rec["layout_id"]} {key} t={t}',fill='white')
  phase_summary={}
  for span in phase_by[index]['runs']:
   selected=frustum['rows'][span['start']:span['end']];phase_summary[span['phase']]=dict(frames=len(selected),target_obb_excluded=sum(x['objects'][key]['obb_frustum_excluded'] for x in selected))
  rows.append(dict(episode=ep.name,task=rec['task_id'],frames=frames,phase_geometry=phase_summary,top_push_geometry=frustum['top_push'],runtime_camera_samples_checked=frustum['runtime_camera_pose_samples_checked'],image_sha256=image_hashes,raw_sha256=rec['hash']))
  sources[str(fp)]=sha(fp)
 assert len(rows)==4;sheet.save(out/'CONTACT_MODEL224.jpg',quality=92)
 report=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,source_sha256=sources,contact_sheet_sha256=sha(out/'CONTACT_MODEL224.jpg'),image_hw=[224,224],actual_visual_review='pending',actual_inference=False,training_ready=False)
 (out/'REPORT.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(episodes=len(rows),actual_model_scaled_frames=16,output=str(out),actual_inference=False)))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('run');p.add_argument('--out',required=True);a=p.parse_args();main(a.run,a.out)
