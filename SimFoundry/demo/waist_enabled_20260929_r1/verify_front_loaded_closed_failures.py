"""Classify every retained short audit error, including subprocess propagation.
No original audit error is removed or made passing. Reject unexpected root or
wrapper failures before launching any subsequent physical comparison.
"""
from pathlib import Path
import ast,hashlib,json,re,datetime,sys
W=Path(__file__).resolve().parent;R=W/'front_loaded_physical_r1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify_log(text,ep):
 assert 'front_loaded_stage_source_binding.py' in text and "assert frames==args['wait_steps' if task=='wait_no_package' else 'steps']" in text
 exceptions=[s for s in text.splitlines() if s.startswith(('AssertionError','subprocess.CalledProcessError:'))];assert exceptions
 allowed={'audit_front_loaded_stage_region_causal.py','audit_front_loaded_stage_region_continuity.py','audit_front_loaded_stage_region_bounds.py'}
 wrappers=[]
 for line in exceptions:
  if line in ['AssertionError','AssertionError: Traceback (most recent call last):']:continue
  match=re.fullmatch(r"subprocess\.CalledProcessError: Command '(.+)' returned non-zero exit status 1\.",line);assert match,line
  args=ast.literal_eval(match.group(1));assert len(args)==3 and Path(args[0]).resolve()==Path(sys.executable).resolve() and Path(args[1]).parent==W and Path(args[1]).name in allowed and Path(args[2])==ep
  wrappers.append(Path(args[1]).name)
 assert text.rstrip().splitlines()[-1] in exceptions
 assert not re.search(r'^(?:FileNotFoundError|ValueError|KeyError|TypeError|ImportError|RuntimeError|ModuleNotFoundError)[:\n]',text,re.M)
 return dict(root='original_full_frame_requirement',propagated_by=wrappers)
if __name__=='__main__':
 result=json.loads((R/'RESULT.json').read_text());assert result['conditions']==10 and result['audit_invocations']==194
 short={'layout_840023_nudge_mailer_to_bin':191,'layout_840020_push_box_to_bin':212};assert len(result['failed_audit_invocations'])==36
 rows=[];sources={str(R/'RESULT.json'):sha(R/'RESULT.json'),str(Path(__file__)):sha(__file__)}
 for f in result['failed_audit_invocations']:
  assert f['episode'] in short and f['incomplete_episode'];ep=next(R.glob('case_*/'+f['episode']));p=ep/(f['script']+'.log');assert sha(p)==f['log_sha256'];sources[str(p)]=sha(p);classified=verify_log(p.read_text(),ep);rows.append(dict(episode=ep.name,script=f['script'],**classified))
 for r in result['rows']:
  if r['episode'] in short:assert r['frames']==short[r['episode']] and not r['original_task_and_pose_passed']
  else:assert r['control_audits_passed'] and not r['failed_audits']
 # Genuine unrelated wrapper or root failures must not be admitted.
 example=next(R.glob('case_*/layout_840023_nudge_mailer_to_bin'));text=(example/'audit_front_loaded_stage_region_bounds.py.log').read_text()
 for bad in [text+'\nValueError: unrelated\n',text.replace('audit_front_loaded_stage_region_causal.py','unrelated_audit.py'),text.replace("assert frames==args['wait_steps' if task=='wait_no_package' else 'steps']",'unknown assertion')]:
  try:verify_log(bad,example)
  except (AssertionError,ValueError,SyntaxError):pass
  else:raise AssertionError('unrelated failure accepted')
 out=W/'FRONT_LOADED_CLOSED_FAILURE_CLASSIFICATION.json';assert not out.exists();out.write_text(json.dumps(dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,retained_failures=36,rows=rows,negative_rejections=3,source_sha256=sources,training_ready=False),indent=2));print('36 original failures retained, root/wrapper causes verified; all8 other conditions original control audits passed')
