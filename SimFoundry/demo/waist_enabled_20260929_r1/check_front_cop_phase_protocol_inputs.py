"""Parse all six real parent commands and verify the only new behavior flag."""
from pathlib import Path
import sys,types,json,hashlib,tempfile,contextlib,io
w=Path(__file__).resolve().parent;stage=w/'staged_front_cop_phase_anchor';parent=w/'front_cop_transverse_groups_r1';protocol=json.loads((parent/'PROTOCOL.json').read_text());prefix=(stage/'collect_paired_sorting.py').read_text().split('app = AppLauncher(args, enable_cameras=True).app')[0];rows=[]
with tempfile.TemporaryDirectory(prefix='phase_protocol_parse_') as td:
 out=Path(td)/'NOT_LAUNCHED'
 def parse(args):
  module=types.ModuleType('phase_protocol_input_check');module.__file__=str(stage/'collect_paired_sorting.py');sys.modules[module.__name__]=module;old=sys.argv;sys.argv=['collector',*args,'--out-dir',str(out)]
  try:
   with contextlib.redirect_stderr(io.StringIO()):exec(compile(prefix,module.__file__,'exec'),module.__dict__)
   return vars(module.args)
  finally:sys.argv=old;sys.modules.pop(module.__name__,None)
 for command in protocol['commands']:
  a=parse(command['args']);b=parse(command['args']+['--front-cop-phase-anchor']);delta={k:[a.get(k),b.get(k)] for k in set(a)|set(b) if a.get(k)!=b.get(k)};assert delta=={'front_cop_phase_anchor':[False,True]},delta;assert not out.exists();rows.append(dict(layout_id=command['layout_id'],wait=command['wait'],tasks=command['tasks'],only_argument_difference=delta))
assert len(rows)==6 and sum(len(r['tasks']) for r in rows)==10 and sum(r['wait'] for r in rows)==2
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();report=dict(passed=True,rows=rows,source_sha256={'collector':sha(stage/'collect_paired_sorting.py'),'parent_protocol':sha(parent/'PROTOCOL.json'),'checker':sha(Path(__file__))},scope='Actual six frozen commands pre-AppLauncher parsing; only phase flag differs. No output directory, AppLauncher construction or physics.',training_ready=False);(stage/'ACTUAL_PROTOCOL_INPUT_CHECK.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
