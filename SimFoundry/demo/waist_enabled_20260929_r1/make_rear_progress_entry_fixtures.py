"""Reuse already checked synthetic history generation for isolated CLI fixtures."""
from pathlib import Path
import hashlib
w=Path(__file__).resolve().parent;source=w/'check_rear_coupled_progress_auditor.py';text=source.read_text();prefix=text[:text.index('for run in [')];body=text[text.index('for run in ['):text.index('  bads=[]')];body=body.replace("['rear_core_slice_groups_r1','front_drive_increment_groups_r1','front_edge_speed_groups_r1']", "['front_drive_increment_groups_r1']")
body+="  fixtures.append(dict(source=str(ep),frontal=dict(plan=candidate_plan,rows=synth)))\n"
ns={'__file__':str(source)};exec(prefix+'\nfixtures=[]\n'+body,ns)
import json
p=w/'staged_rear_coupled_progress_probe/ENTRY_FIXTURES.json';assert not p.exists();p.write_text(json.dumps(dict(rows=ns['fixtures'],source_checker_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Copied candidate history generation only; fixed observed modes/poses/forces, not physical trajectories.',training_ready=False),indent=2));print(len(ns['fixtures']),p.stat().st_size)
