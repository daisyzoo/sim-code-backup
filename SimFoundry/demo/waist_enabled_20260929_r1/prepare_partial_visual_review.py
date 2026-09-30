"""Same evidence renderer, completed cases only; final RESULT remains untouched."""
from pathlib import Path
import sys,hashlib,json
root=Path(__file__).resolve().parent;source=(root/'review_frontal_run.py').read_text();sha=hashlib.sha256(source.encode()).hexdigest()
assert source.count('all_rows=[]')==1
if len(sys.argv)>2:
 requested={f'case_{int(v)}' for v in sys.argv[2:]}
 source=source.replace('all_rows=[]',f'cases=[p for p in cases if p.name in {requested!r}]\nall_rows=[]')
source=source.replace('all_rows=[]',"cases=[p for p in cases if (p/'POSE_AND_MOTION_REVIEW.json').exists()]\nall_rows=[]").replace("root/'RESULT.json'","root/'PARTIAL_RESULT.json'")
exec(compile(source,'same_partial_evidence_renderer','exec'))
run=Path(sys.argv[1]);(run/'PARTIAL_RENDERER_BINDING.json').write_text(json.dumps(dict(original_renderer_sha256=sha,requested_cases=sys.argv[2:],scope='Only completed case directories, identical sheet rendering; writesPARTIAL_RESULT, not finalRESULT. No visual approval.',training_ready=False),indent=2))
