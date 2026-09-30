"""Release all reviewed ordinary push episodes unchanged for a task ablation."""
from pathlib import Path
import hashlib,json,shutil,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from prepare_paired_sorting_lerobot import checked_sources
source=ROOT/'demo/ordinary_pilot8_20260928_r1';out=ROOT/'demo/ordinary_push4_release_20260928_r1'
assert not out.exists()
records=checked_sources([source])
selected=[r for r in records if r['task_id']!='wait_no_package']
assert {(r['layout_id'],r['task_id']) for r in selected}=={(l,t) for l in (50,51) for t in ('push_box_to_bin','nudge_mailer_to_bin')}
out.mkdir();hashes={}
for r in selected:
 src=r['path'].parent;dst=out/src.name;shutil.copytree(src,dst)
 raw=dst/'raw.npz';assert hashlib.sha256(raw.read_bytes()).hexdigest()==r['hash']
 hashes[str(raw.relative_to(out))]=r['hash']
prov=json.loads((source/'provenance.json').read_text());prov['release_scope']={'layouts':2,'wait_episodes':0,'layout_start':50}
prov['release']={'source':str(source),'reason':'All four paired ordinary pushes selected by task, not success or trajectory features; ordinary waits replaced by reviewed recovery waits for registered exploratory task ablation. Original raw files unchanged.','source_review_sha256':hashlib.sha256((source/'review.json').read_bytes()).hexdigest()}
(out/'provenance.json').write_text(json.dumps(prov,indent=2))
shutil.copy2(source/'STATUS.json',out/'STATUS.json');shutil.copy2(source/'review.json',out/'source_review.json');shutil.copy2(__file__,out/'release_script.py')
(out/'review.json').write_text(json.dumps({'approved':True,'method':'Inherited actual visual review of the exact unchanged four ordinary push episodes; source review retained and hashed. Reaudited source and copied raw equality. No new visual approval inferred.','episodes':hashes},indent=2))
assert len(checked_sources([out]))==4
print(out,'4 unchanged reviewed push episodes')
