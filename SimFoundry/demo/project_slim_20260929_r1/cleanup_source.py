import os,json,stat,hashlib,shutil,sys,datetime
from pathlib import Path
W=Path('/home/user/Documents/zoo/sim'); R=W/'SimFoundry/demo/project_slim_20260929_r1'
RETIRED=['paired_zero_pilot32_a_20260924','paired_zero_pilot32_b_20260924','paired_zero_pilot32_c4_20260924','paired_recovery_pilot40_20260928','paired_waitonly_pilot40_20260928','paired_language_adapter_pilot40_20260928','paired_spatial_pilot40_20260928','paired_spatial_prefix40_20260928','paired_coverage80_20260928','paired_coverage_chunk10_20260928']
DEMOS=['paired_zero_ab_experiment_20260924_r1','paired_c4_experiment_20260924_r1','recovery_comparison_20260928_r1','wait_only_recovery_comparison_20260928_r1','task_language_adapter_20260928_r1','spatial_model_comparison_20260928_r1','spatial_prefix_experiment_20260928_r1','coverage_model80_20260928_r1','coverage_chunk10_20260928_r1']
def identity(p):
 s=p.lstat();return dict(path=str(p.relative_to(W)),size=s.st_size,inode=s.st_ino,mtime_ns=s.st_mtime_ns,mode=s.st_mode,nlink=s.st_nlink,allocated=s.st_blocks*512)
def used_paths():
 used=set()
 for proc in Path('/proc').glob('[0-9]*'):
  try:
   for fd in (proc/'fd').iterdir():
    try:used.add(os.readlink(fd).removesuffix(' (deleted)'))
    except OSError:pass
  except OSError:pass
  try:
   for line in (proc/'maps').read_text().splitlines():
    parts=line.split(maxsplit=5)
    if len(parts)==6 and parts[5].startswith('/'):used.add(parts[5])
  except OSError:pass
 return used
if sys.argv[1]=='plan':
 R.mkdir(exist_ok=False);used=used_paths();protected=set();provenances=[]
 for p in (W/'lerobot').glob('*/meta/paired_provenance.json'):
  d=json.loads(p.read_text());provenances.append(str(p.relative_to(W)))
  for row in d['records']:
   x=Path(row['path']);protected.add((x if x.is_absolute() else W/x).resolve())
 candidates=[];trees=[];checkpoints=[]
 for name in RETIRED:
  cps=list((W/'lerobot/outputs'/name).glob('*/checkpoints'));assert len(cps)==1
  root=cps[0];trees.append(str(root.relative_to(W)));checkpoints.append(str(root.relative_to(W)))
  for p in root.rglob('*'):
   if p.is_symlink() or p.is_file():candidates.append((p,'retired_checkpoint_entire_tree'))
 for name in DEMOS:
  for p in (W/'SimFoundry/demo'/name).rglob('raw.npz'):
   if p.resolve() not in protected and not p.is_symlink():candidates.append((p,'retired_rollout_RGB; retain_nonRGB_arrays_and_five_keyframes'))
 root=W/'dist/_build_venv310';assert (root/'pyvenv.cfg').exists();trees.append(str(root.relative_to(W)))
 for base,dirs,files in os.walk(root,followlinks=False):
  for n in files:candidates.append((Path(base)/n,'regenerable_packaging_venv'))
  for n in list(dirs):
   p=Path(base)/n
   if p.is_symlink():candidates.append((p,'regenerable_packaging_venv'));dirs.remove(n)
 rows=[]
 for p,reason in candidates:
  assert str(p) not in used,('open_or_mapped',p)
  x=identity(p);assert stat.S_ISREG(x['mode']) or stat.S_ISLNK(x['mode']);x['reason']=reason
  if p.is_symlink():x['link_target']=os.readlink(p)
  rows.append(x)
 assert len({x['path'] for x in rows})==len(rows)
 retained=[]
 for p in (W/'lerobot/outputs').glob('**/pretrained_model/model.safetensors'):
  if not any(str(p.relative_to(W)).startswith(t+'/') for t in checkpoints):retained.append(identity(p))
 m=dict(created=datetime.datetime.now().isoformat(),before_free=shutil.disk_usage(W).free,checkpoint_trees=checkpoints,trees=trees,files=rows,retained_weights=retained,protected_raw_paths=sorted(map(str,protected)),provenance_files=provenances)
 (R/'manifest.json').write_text(json.dumps(m,indent=2))
 from collections import Counter,defaultdict
 sizes=defaultdict(int);counts=Counter()
 for x in rows:sizes[x['reason']]+=x['allocated'] if x['nlink']==1 else 0;counts[x['reason']]+=1
 print(json.dumps(dict(report=str(R),files=len(rows),GiB_by_reason={k:v/2**30 for k,v in sizes.items()},counts=counts,protected_raw=len(protected),retained_models=len(retained)),indent=2))
if sys.argv[1]=='apply':
 import numpy as np
 from PIL import Image,ImageDraw
 m=json.loads((R/'manifest.json').read_text());used=used_paths()
 for row in m['files']:
  p=W/row['path'];assert identity(p)=={k:row[k] for k in identity(p)},('changed',p);assert str(p) not in used
 # Archive metadata and sufficient non-RGB trace evidence before deleting anything.
 for tree in m['checkpoint_trees']:
  root=W/tree;dest=R/'retired_checkpoint_metadata'/root.parent.parent.name/root.parent.name
  dest.mkdir(parents=True,exist_ok=False)
  for p in root.rglob('*'):
   if p.is_symlink():continue
   if p.is_file() and p.stat().st_size<10*2**20:
    target=dest/p.relative_to(root);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
  (dest/'RETIRED.json').write_text(json.dumps(dict(original_checkpoint_tree=tree,weights_removed=True,reason='User-requested project slimming; superseded experiment, not current baseline/new model'),indent=2))
 with (R/'rollout_archives.jsonl').open('x') as log:
  raws=[x for x in m['files'] if x['reason'].startswith('retired_rollout')]
  for i,row in enumerate(raws):
   p=W/row['path'];sha=hashlib.sha256(p.read_bytes()).hexdigest()
   with np.load(p,allow_pickle=False) as src:
    arrays={k:src[k] for k in src.files if k!='rgb'};rgb=src['rgb'];frames=np.linspace(0,len(rgb)-1,5,dtype=int).tolist()
    target=p.parent/'archived_state_actions.npz';assert not target.exists();np.savez_compressed(target,**arrays)
    with np.load(target,allow_pickle=False) as check:
     assert set(check.files)==set(arrays)
     for key,value in arrays.items():assert check[key].dtype==value.dtype and check[key].shape==value.shape and check[key].tobytes()==value.tobytes()
    image=Image.new('RGB',(1200,200),'white');draw=ImageDraw.Draw(image)
    for k,f in enumerate(frames):
     draw.text((k*240,0),f'frame {f}',fill='black');image.paste(Image.fromarray(rgb[f].transpose(1,2,0)).resize((240,180)),(k*240,20))
    image.save(p.parent/'archived_keyframes.jpg',quality=70)
   rec=dict(raw_path=row['path'],raw_sha256=sha,retained_arrays=list(arrays),frames=frames,archive_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),note='Historical raw RGB removed for user-requested slimming; not a complete replayable training episode. Keyframe extraction alone is not actual visual review.')
   (p.parent/'RAW_ARCHIVED.json').write_text(json.dumps(rec,indent=2));log.write(json.dumps(rec)+'\n');log.flush()
   if (i+1)%100==0:print('Archived',i+1,'/',len(raws),flush=True)
 # Revalidate identities immediately before each deletion. Unlink retired last links first.
 rows=sorted(m['files'],key=lambda x:0 if stat.S_ISLNK(x['mode']) else 1)
 with (R/'deleted.jsonl').open('x') as log:
  for row in rows:
   p=W/row['path'];current=identity(p);assert all(current[k]==row[k] for k in current),('changed_before_delete',p)
   p.unlink();log.write(json.dumps(row)+'\n')
 for rel in m['trees']:
  root=W/rel
  for base,dirs,files in os.walk(root,topdown=False):
   assert not files,(base,files)
   for name in dirs:(Path(base)/name).rmdir()
  root.rmdir()
  if 'checkpoints' in rel:(root.parent/'CHECKPOINT_RETIRED.md').write_text('This superseded checkpoint was retired by user-requested cleanup on2026-09-29. Weights and last link removed together. Configuration and training metadata archived in SimFoundry/demo/project_slim_20260929_r1/retired_checkpoint_metadata. Historical evaluation reports remain; this run is no longer loadable.\n')
 for name in DEMOS:
  (W/'SimFoundry/demo'/name/'RAW_RGB_PRUNED.md').write_text('User-authorized project slimming: old evaluation raw.npz payloads not referenced by dataset provenance have been archived without RGB. All original non-RGB arrays retained in archived_state_actions.npz with byte-for-byte checks, five RGB keyframes retained per rollout; JSON reports and prior review material retained. See project_slim_20260929_r1/manifest.json. Do not treat archived rollouts as complete trainable episodes.\n')
 for row in m['retained_weights']:
  current=identity(W/row['path']);assert current==row
 for raw in m['protected_raw_paths']:assert Path(raw).is_file(),raw
 links=[p for p in (W/'lerobot/outputs').glob('**/checkpoints/last')];assert all((p/'pretrained_model/model.safetensors').is_file() for p in links)
 after=shutil.disk_usage(W).free;result=dict(completed=datetime.datetime.now().isoformat(),deleted_files=len(rows),retired_checkpoints=len(m['checkpoint_trees']),archived_rollouts=len(raws),retained_models=len(m['retained_weights']),valid_last_links=len(links),protected_raw_files=len(m['protected_raw_paths']),free_before_GiB=m['before_free']/2**30,free_after_GiB=after/2**30,net_free_increase_GiB=(after-m['before_free'])/2**30)
 (R/'RESULT.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2),flush=True)
