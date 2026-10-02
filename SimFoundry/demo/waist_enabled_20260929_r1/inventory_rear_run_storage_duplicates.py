"""Read-only exact-byte duplicate inventory in three completed diagnostic archives.
No current source, model, unique data, changing status/audit files or temp fixtures.
"""
from pathlib import Path
import json,hashlib,os,datetime,collections,shutil
W=Path(__file__).resolve().parent
ROOTS=[W/n for n in ['fresh_closed_peak_trials_r1','joint_edge_intersection_physical_r1','front_interval_physical_r2']]
NAMES={'raw.npz','trace.npz','parcel_orientation.npz','substep_contacts.npz','solved_contact_forces.json','self_clearance.json','coordination.json','frontal_bypass.json','region_approach.json','recontact_pose.json','runtime_collision_arrays.npz'}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(8*1024**2):h.update(b)
 return h.hexdigest()
sizes=collections.defaultdict(list)
for root in ROOTS:
 assert (root/('RESULT_WITH_SUPPLEMENT.json' if 'joint_edge' in root.name else 'RESULT.json')).exists()
 for base,ds,fs in os.walk(root):
  ds[:]=[d for d in ds if d not in ['source_snapshot','runtime_source','substep_runtime_sources']]
  for name in fs:
   p=Path(base)/name
   if name not in NAMES or p.is_symlink():continue
   s=p.stat()
   if s.st_size>=1024**2:sizes[s.st_size].append(p)
groups=[];hashed=0
for size,ps in sizes.items():
 if len({p.stat().st_ino for p in ps})<2:continue
 byhash=collections.defaultdict(list);cache={}
 for p in ps:
  s=p.stat();identity=(s.st_dev,s.st_ino)
  if identity not in cache:cache[identity]=sha(p);hashed+=s.st_size
  byhash[cache[identity]].append(p)
 for digest,paths in byhash.items():
  if len({p.stat().st_ino for p in paths})<2:continue
  # Preserve the most externally-linked inode as canonical.
  paths.sort(key=lambda p:(-p.stat().st_nlink,str(p)));canonical=paths[0]
  groups.append(dict(size=size,sha256=digest,canonical=str(canonical),files=[dict(path=str(p),inode=p.stat().st_ino,device=p.stat().st_dev,nlink=p.stat().st_nlink,mode=p.stat().st_mode,uid=p.stat().st_uid,gid=p.stat().st_gid,blocks=p.stat().st_blocks) for p in paths]))
reclaim=0
for g in groups:
 nodes=collections.defaultdict(list)
 for f in g['files']:nodes[f['inode']].append(f)
 for inode,fs in nodes.items():
  if inode!=Path(g['canonical']).stat().st_ino and fs[0]['nlink']==len(fs):reclaim+=fs[0]['blocks']*512
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,roots=[str(p) for p in ROOTS],hashed_bytes=hashed,groups=groups,estimated_reclaimable_bytes=reclaim,free_bytes=shutil.disk_usage(W).free,changes_made=False)
p=W/'REAR_RUN_STORAGE_DUPLICATE_INVENTORY.json';assert not p.exists();p.write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='groups'}),flush=True);print('groups',len(groups))
