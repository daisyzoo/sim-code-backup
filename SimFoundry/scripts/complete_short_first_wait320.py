#!/usr/bin/env python3
"""Run supplemental waits only after the original batch exits and wait patch is applied."""
import argparse, hashlib, json, os, subprocess, sys
from pathlib import Path

W = Path(__file__).resolve().parents[2]
R = W / 'SimFoundry/demo/short_first_model40_20260929_r1'
S = W / 'SimFoundry/scripts'
PY = '/home/user/miniconda3/envs/env_isaaclab/bin/python'
PROTOCOL = W / 'SimFoundry/demo/short_first_test_protocol_20260929_r1/heldout_protocol.json'

def preflight():
    stage = json.loads((R/'STATUS.json').read_text())['stage']
    if stage != 'numeric_complete_actual_visual_review_required':
        raise RuntimeError(f'Original batch not completed: {stage}')
    forbidden = {'run_short_first_training_evaluation.sh', 'collect_paired_sorting.py', 'pi05_policy_server.py'}
    for proc in Path('/proc').glob('[0-9]*'):
        try:
            args = (proc/'cmdline').read_bytes().split(b'\0')
        except OSError:
            continue
        if any(Path(os.fsdecode(a)).name in forbidden for a in args if a):
            raise RuntimeError(f'Original evaluation or another collector/server is still live: {proc.name}')
    source = (S/'collect_paired_sorting.py').read_text()
    if "parser.add_argument('--wait-steps'" not in source or "args.wait_steps if task_id == 'wait_no_package'" not in source:
        raise RuntimeError('Explicit wait-duration patch is not applied')
    return hashlib.sha256(source.encode()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    source_hash = preflight()  # No directory/process mutation before this guard.
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out/'PREFLIGHT.json').write_text(json.dumps({'collector_sha256':source_hash,'protocol_sha256':hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()},indent=2))
    checkpoints = {
        'baseline': W/'lerobot/outputs/paired_relative_chunk10_20260929/package_sorting_pi05_1gpu_20260929_015655/checkpoints/014480/pretrained_model',
        'new': Path((R/'checkpoint.txt').read_text().strip()),
    }
    configs = {'baseline':S/'pi05_paired_relative_chunk10_20260929.env','new':S/'pi05_short_first_relative_chunk10_20260929.env'}
    def run(command, log=None, env=None):
        if log:
            with log.open('x') as stream:
                subprocess.run(command,cwd=W,env=env,stdout=stream,stderr=subprocess.STDOUT,check=True)
        else:
            subprocess.run(command,cwd=W,env=env,check=True)
    for model in ['baseline','new']:
        roots=[]
        for seed in [0,1,2]:
            directory=args.out/f'{model}_seed{seed}'
            env=dict(os.environ,PI05_LOCAL_CONFIG=str(configs[model]),PI05_POLICY_PATH=str(checkpoints[model]),PI05_RECORD_DIR=str(directory.resolve()),PI05_EVAL_SEED=str(seed),PI05_SPATIAL_PROTOCOL=str(PROTOCOL))
            run(['bash',str(S/'run_pi05_wait320_sim.sh')],args.out/f'{model}_seed{seed}.log',env)
            roots.extend([R/f'evaluation/{model}_local320_seed{seed}/layout_70014',R/f'evaluation/{model}_local320_seed{seed}/layout_70015',directory.resolve()/'wait'])
            run([PY,str(S/'make_rollout_review.py'),'--root',str(directory.resolve()),'--out',str((args.out/f'review_{model}_seed{seed}').resolve())])
        summary=args.out/f'{model}_LOCAL320_COMPLETE.json'
        run([sys.executable,str(S/'summarize_paired_evaluation.py'),'--roots',*[str(p) for p in roots],'--output',str(summary.resolve())])
        run([PY,str(S/'audit_local_evaluation_budget.py'),'--summary',str(summary.resolve()),'--protocol',str(PROTOCOL),'--out',str((args.out/f'{model}_BUDGET.json').resolve())])
        run([PY,str(S/'audit_policy_parcel_poses.py'),'--summary',str(summary.resolve()),'--out',str((args.out/f'{model}_POSES.json').resolve())])
    (args.out/'STATUS.json').write_text(json.dumps({'stage':'numeric_complete_actual_visual_review_required','goal_complete':False},indent=2))

if __name__ == '__main__':
    main()
