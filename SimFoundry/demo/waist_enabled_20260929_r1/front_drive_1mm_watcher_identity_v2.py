"""Exact live driver and explicit supplemental observer-source binding."""
from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;R=W/'front_drive_1mm_physical_r1'
def verify():
 b=json.loads((R/'WATCHER_V2_PREPARATION.json').read_text())
 for p,h in {**b['original_failure_archive_sha256'],**b['new_sources_sha256']}.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
 p=Path('/proc')/str(b['producer_pid']);assert p.exists()
 stat=(p/'stat').read_text().rsplit(')',1)[1].split();assert stat[0]!='Z' and stat[19]==b['producer_start_ticks']
 assert (p/'cmdline').read_bytes().decode().split('\0')[:-1]==b['producer_cmd']
 return b['new_sources_sha256']
