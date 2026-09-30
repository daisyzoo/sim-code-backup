"""Measured expert mode exposure; diagnostic only, no sampler/trajectory changes."""
from pathlib import Path
from collections import Counter
import json,sys
run=Path(sys.argv[1]).resolve();rows=[]
for ep in sorted(run.glob('case_*/layout_*')):
    if not (ep/'quality.json').exists():continue
    q=json.loads((ep/'quality.json').read_text());f=json.loads((ep/'expert_control.json').read_text());n=q['frames']
    modes=Counter(r['mode'] for r in f)
    hold=sum(v for k,v in modes.items() if k in ('goal_release','top_release','done','hold'))
    release=next((r['step'] for r in f if r['mode'] in ('goal_release','top_release')),None)
    # This is the previously used generic initial-prefix weighting formula,
    # not a claim about a yet-unbuilt training set or sampler configuration.
    prefix=3;old_weight=16.;denominator=n+prefix*(old_weight-1)
    rows.append(dict(episode=ep.name,frames=n,task_numeric_passed=q['passed'],mode_counts=dict(modes),first_release_frame=release,release_or_hold_frames=hold,release_or_hold_fraction=hold/n,uniform_first3_fraction=prefix/n,historical_weight16_first3_fraction=prefix*old_weight/denominator,current_weight32_cap_first3_fraction=prefix*32/(n+prefix*31),weight_for_same_prefix_exposure_as_320frame_weight16=(48/365)*(n-prefix)/(prefix*(1-48/365))))
result=dict(rows=rows,total_recorded_frames=sum(r['frames'] for r in rows),total_release_or_hold_frames=sum(r['release_or_hold_frames'] for r in rows),scope='Counts the full expert_control log including initial frame; frontal-only observer logs are empty when that route is unnecessary and must not be used as overall phase counts. Release includes actual retreat then hold, not all frames physically stationary. Initial3/weight16 formula is an exposure comparison, not an approved sampling schedule. Current production prefix_weights permits weight1..32: calculated48.30 for960 frames is NOT accepted by the current API, not a ready training configuration. Future sampler and stats must use qualified train split, with waits and actual motion phase separately preserved.',training_ready=False)
(run/'PHASE_EXPOSURE_AUDIT.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
