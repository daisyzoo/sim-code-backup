"""Collect an exact fresh contract after admission is installed; never train here.

Each assignment has its own process so a complete, recorded task failure does
not prevent recording its category-swapped counterpart. Runtime errors stop.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys

W = Path(__file__).resolve().parent
REPO = W.parents[1]
sys.path.insert(0, str(REPO))
import numpy as np
from simfoundry.data.waist_pilot_protocol import validate_waist_contract


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare(contract_path, collector):
    contract, digest = validate_waist_contract(contract_path)
    if sha(collector) != contract['pilot_collector_sha256']:
        raise ValueError('Collector must match the admitted candidate exactly')
    reference = Path(contract['feasibility'][0]['root'])
    settings = list(json.loads((reference/'PROTOCOL.json').read_text())['settings'])
    settings[settings.index('--role')+1] = 'pilot'
    settings = [x for x in settings if x != '--extended-waist-diagnostic']
    settings += ['--waist-pilot-contract', str(contract_path.resolve())]
    commands = []
    for layout in contract['layouts']:
        commands.append(dict(layout_id=layout['layout_id'], wait=False,
            args=settings+['--layouts', '1', '--layout-start', str(layout['layout_id']),
                           '--wait-episodes', '0'],
            tasks=['push_box_to_bin', 'nudge_mailer_to_bin']))
    for layout in contract['wait_layouts']:
        commands.append(dict(layout_id=layout['layout_id'], wait=True,
            args=settings+['--layouts', '0', '--wait-episodes', '1',
                           '--wait-layout-start', str(layout['layout_id'])],
            tasks=['wait_no_package']))
    return contract, digest, commands


def complete_case(case, item, settings, returncode, contract_digest):
    state = json.loads((case/'STATUS.json').read_text())
    declared_failure = state.get('status') == 'blocked_quality_or_runtime' and state.get('error') in (
        'Quality gate failed. Stop; no retries or training export. See manifest.json.',
        'Wait quality gate failed.')
    if state.get('status') != 'numeric_pass_visual_review_pending' and not declared_failure:
        raise RuntimeError('Unexpected runtime state: '+str(state))
    if returncode not in (0, 1) or (returncode != 0 and not declared_failure):
        raise RuntimeError('Collector did not end with a complete declared quality outcome')
    expected = settings['wait_steps' if item['wait'] else 'steps']
    records = []
    for task in item['tasks']:
        ep = case/f"layout_{item['layout_id']}_{task}"
        quality = json.loads((ep/'quality.json').read_text())
        with np.load(ep/'raw.npz') as raw:
            meta = json.loads(str(raw['collect_meta']))
            if raw['q'].shape != (expected,23) or raw['action'].shape != (expected,23):
                raise RuntimeError('Incomplete episode')
            if str(raw['task_id']) != task or meta.get('waist_pilot_contract_sha256') != contract_digest:
                raise RuntimeError('Task or fresh contract metadata differs')
        if quality['frames'] != expected:
            raise RuntimeError('Quality frame count differs')
        records.append(dict(episode=ep.name, original_task_passed=quality['passed'],
                            raw_sha256=sha(ep/'raw.npz')))
    return dict(layout_id=item['layout_id'], collector_returncode=returncode,
                collector_status=state, conditions=records, training_ready=False)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--contract',type=Path,required=True)
    p.add_argument('--out',type=Path)
    p.add_argument('--validate-only',action='store_true')
    a=p.parse_args()
    collector = (W/'staged_waist_collector/collect_paired_sorting.py' if a.validate_only
                 else REPO/'scripts/collect_paired_sorting.py')
    contract, digest, commands = prepare(a.contract, collector)
    summary=dict(contract_path=str(a.contract.resolve()), contract_sha256=digest,
        collector_sha256=sha(collector), runner_sha256=sha(__file__),
        layout_ids=[d['layout_id'] for d in contract['layouts']],
        wait_layout_ids=[d['layout_id'] for d in contract['wait_layouts']],
        settings=contract['collector_settings'], commands=commands, training_ready=False)
    if a.validate_only:
        print(json.dumps(dict(**summary, scope='Preparation only; no source installation or simulation.'),indent=2))
        return
    if a.out is None or a.out.exists():
        raise ValueError('New output directory required')
    # Refuse simultaneous simulator processes; the user has authorized running.
    for proc in Path('/proc').glob('[0-9]*/cmdline'):
        try: parts=proc.read_bytes().split(b'\0')
        except (FileNotFoundError,PermissionError): continue
        if any(Path(os.fsdecode(x)).name == 'collect_paired_sorting.py' for x in parts if x):
            raise RuntimeError('Another collector is still alive: '+str(proc.parent))
    out=a.out.resolve();out.mkdir()
    (out/'PROTOCOL.json').write_text(json.dumps(summary,indent=2))
    env=os.environ.copy()
    env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',
               CONDA_PREFIX='/home/user/miniconda3/envs/env_isaaclab',OMNI_KIT_ACCEPT_EULA='yes')
    env['PATH']=env['CONDA_PREFIX']+'/bin:'+env['PATH'];env.setdefault('DISPLAY',':1')
    def status(stage,**kw):
        (out/'STATUS.json').write_text(json.dumps(dict(stage=stage,pid=os.getpid(),
            updated_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            training_ready=False,**kw),indent=2))
    records=[]
    try:
        for item in commands:
            if sha(a.contract)!=digest or sha(collector)!=summary['collector_sha256']:
                raise RuntimeError('Frozen admission changed')
            validate_waist_contract(a.contract)
            if shutil.disk_usage(W).free < 30*2**30:
                raise RuntimeError('Insufficient space for fresh collection')
            case=out/f"case_{item['layout_id']}"
            status('running',layout_id=item['layout_id'])
            cmd=['./isaaclab.sh','-p',str(collector),*item['args'],'--out-dir',str(case)]
            with (out/f"case_{item['layout_id']}.log").open('w') as log:
                result=subprocess.run(cmd,cwd=REPO.parent/'IsaacLab',env=env,
                    stdout=log,stderr=subprocess.STDOUT,timeout=1800)
            records.append(complete_case(case,item,contract['collector_settings'],result.returncode,digest))
            (out/'COLLECTION_EXECUTION.json').write_text(json.dumps(records,indent=2))
            if not item['wait']:
                for script in ('audit_contacts.py','review_diagnostics.py'):
                    with (out/f"{item['layout_id']}_{script}.log").open('w') as log:
                        subprocess.run([sys.executable,str(W/script),str(case)],env=env,
                            stdout=log,stderr=subprocess.STDOUT,check=True)
            else:
                ep=case/f"layout_{item['layout_id']}_wait_no_package"
                with (out/'wait_audit.log').open('w') as log:
                    check=subprocess.run([sys.executable,str(W/'audit_normal_wait.py'),str(ep)],
                        env=env,stdout=log,stderr=subprocess.STDOUT)
                report=json.loads((ep/'WAIT_STABILITY_AUDIT.json').read_text())
                if check.returncode != (0 if report['passed'] else 1):
                    raise RuntimeError('Wait auditor execution/report mismatch')
                frames=[str(x) for x in report['sampled_rgb_frames']]
                subprocess.run([sys.executable,str(W/'render_episode_frames.py'),str(ep),*frames],env=env,check=True)
        status('numeric_complete_actual_visual_review_pending',
               original_tasks_passed=sum(x['original_task_passed'] for r in records for x in r['conditions']),
               total_conditions=sum(len(r['conditions']) for r in records))
    except BaseException as exc:
        status('runtime_failed',error=str(exc));raise


if __name__ == '__main__':
    main()
