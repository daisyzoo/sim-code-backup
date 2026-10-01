"""Prepare an unwired release monitor that preserves the existing expert margin.

Only the early position-confirmation path changes when explicitly enabled.
The quality evaluator, running collectors and original top_push release stay put.
"""
from pathlib import Path
import hashlib
import json

w = Path(__file__).resolve().parent
repo = w.parents[1]
source = repo / 'simfoundry/data/confirmed_position_release.py'
stage = w / 'staged_confirmed_release_margin_probe'
stage.mkdir(exist_ok=False)
text = source.read_text()
text = text.replace(text[:text.index('from collections')], '''"""Isolated, unwired early-release monitor with optional existing expert margin.

A true result only proposes release; original controller guards must still run.
This is not a task-quality or training-admission decision.
"""
''', 1)
old = 'def __init__(self, initial_y, direction):'
assert text.count(old) == 1
text = text.replace(old, 'def __init__(self, initial_y, direction, *, require_expert_margin=False):')
old = '        self.initial_y=float(initial_y);self.direction=direction;self.window=deque(maxlen=10)'
assert text.count(old) == 1
text = text.replace(old, '''        if not isinstance(require_expert_margin, bool):
            raise ValueError('Expert margin flag must be boolean')
        self.require_expert_margin = require_expert_margin
''' + old)
old = '        return (len(self.window)==10'
assert text.count(old) == 1
text = text.replace(old, '''        margin_ready = True
        if self.require_expert_margin:
            from simfoundry.data.reach_sweep import ready_to_release
            margin_ready = ready_to_release(self.initial_y, point[1], self.direction)
        return (margin_ready and len(self.window)==10''')
candidate = stage / source.name
candidate.write_text(text)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
(stage / 'PREPARATION.json').write_text(json.dumps(dict(
    source_sha256=sha(source), candidate_sha256=sha(candidate),
    existing_expert_margin_source_sha256=sha(repo/'simfoundry/data/reach_sweep.py'),
    collector_wired=False, physical_started=False, training_ready=False,
    scope='Optional early-release predicate adds the already-existing expert margin; '
          'original 10-observation confirmation remains. Default preserves old behavior. '
          'Not wired into any collector. No change to original scoring or emergency guards.'
), indent=2))
print(stage)
