"""Full byte comparison of sampled upload-cache candidates; does not delete."""
from pathlib import Path
import datetime,hashlib,json,subprocess
W=Path(__file__).resolve().parent;D=W/'storage_duplicate_staging_20261005_r1';D.mkdir(exist_ok=False)
source=Path('/tmp/sim_wandb_staging_candidates_20261005.json');c=json.loads(source.read_text());(D/'CANDIDATES.json').write_text(source.read_text());rows=[]
def stat(p):
 s=p.stat();return dict(device=s.st_dev,inode=s.st_ino,bytes=s.st_size,mtime_ns=s.st_mtime_ns,links=s.st_nlink,allocated_bytes=s.st_blocks*512)
for x in c['candidates']:
 a=Path(x['temporary_path']);b=Path(x['retained_model']);assert a.parent==Path('/home/user/.local/share/wandb/artifacts/staging') and a.name.startswith('tmp') and not a.is_symlink() and not b.is_symlink()
 before=[stat(a),stat(b)];assert before[0]['bytes']==before[1]['bytes']==x['bytes'];ha=hashlib.sha256();hb=hashlib.sha256();equal=True;count=0
 with a.open('rb') as f,b.open('rb') as g:
  while True:
   aa=f.read(8*1024**2);bb=g.read(8*1024**2)
   if not aa and not bb:break
   ha.update(aa);hb.update(bb);equal=equal and aa==bb;count+=len(aa)
 assert before==[stat(a),stat(b)]
 row=dict(**x,temporary_stat=before[0],retained_stat=before[1],compared_bytes=count,byte_identical=equal,temporary_sha256=ha.hexdigest(),retained_sha256=hb.hexdigest());rows.append(row)
 print(json.dumps(dict(temporary_path=str(a),byte_identical=equal,compared_bytes=count)),flush=True)
 (D/'STATUS.json').write_text(json.dumps(dict(status='verifying',completed=len(rows),rows=rows),indent=2))
paths=[r['temporary_path'] for r in rows if r['byte_identical']]
p=subprocess.run(['lsof','-n','-P','--',*paths],capture_output=True,text=True)
assert p.returncode in (0,1);(D/'OPEN_HANDLES.txt').write_text(p.stdout+'\n'+p.stderr)
out=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,rows=rows,all_identical=all(r['byte_identical'] for r in rows),lsof_returncode=p.returncode,no_open_temporary_handles=p.returncode==1 and not p.stdout.strip(),deleted=False)
(D/'VERIFIED.json').write_text(json.dumps(out,indent=2));(D/'STATUS.json').write_text(json.dumps(dict(status='verified',identical=sum(r['byte_identical'] for r in rows),deleted=False),indent=2));print(json.dumps({k:v for k,v in out.items() if k!='rows'}),flush=True)
