"""Continue a reviewed complete group across preregistered development layouts."""
import argparse,os,json,hashlib,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root.parents[1]))
from simfoundry.data.waist_group_audit import validate_complete_swap_layouts
p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--layout-ids',type=int,nargs='+',required=True);args=p.parse_args()
parent=args.parent.resolve();out=args.out.resolve()
ready=json.loads((parent/'COMPLETE_GROUP_READINESS.json').read_text())
if ready.get('complete_group_feasibility_passed') is not True:raise ValueError('Parent complete group has not passed actual task/pose/pair/visual review')
if out.exists():raise ValueError('New batch requires a fresh output directory')
layout_paths={str(i):root/f'development_layouts/{i}.json' for i in args.layout_ids}
layouts=[json.loads(path.read_text()) for path in layout_paths.values()]
if any(d.get('planned_split')!='development' for d in layouts):raise ValueError('Only registered development layouts allowed')
groups=validate_complete_swap_layouts(layouts)
old=json.loads((parent/'PROTOCOL.json').read_text());settings=old['settings']
if settings[settings.index('--role')+1]!='diagnostic':raise ValueError('This runner cannot collect training data')
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
for path,digest in old['source_sha256'].items():
    if sha(path)!=digest:raise ValueError('Expert/scene source differs from reviewed parent: '+path)
layout_hashes={i:sha(path) for i,path in layout_paths.items()}
out.mkdir(parents=True,exist_ok=False)
protocol=dict(old,parent_run=str(parent),parent_readiness_sha256=sha(parent/'COMPLETE_GROUP_READINESS.json'),layout_ids=args.layout_ids,layout_sha256=layout_hashes,groups=groups,runner_sha256=sha(__file__),training_ready=False,hypothesis='Fixed successful configuration across complete preregistered development groups; keep every attempted failure, no held-out/test geometry, no training admission.')
protocol.pop('layout_id',None);(out/'PROTOCOL.json').write_text(json.dumps(protocol,indent=2))
env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',CONDA_PREFIX='/home/user/miniconda3/envs/env_isaaclab',OMNI_KIT_ACCEPT_EULA='yes');env['PATH']=env['CONDA_PREFIX']+'/bin:'+env['PATH'];env.setdefault('DISPLAY',':1')
def status(stage,**kw):(out/'STATUS.json').write_text(json.dumps(dict(stage=stage,pid=os.getpid(),training_ready=False,**kw),indent=2))
try:
    for i in args.layout_ids:
        for path,digest in old['source_sha256'].items():
            if sha(path)!=digest:raise ValueError('Frozen source changed: '+path)
        if sha(layout_paths[str(i)])!=layout_hashes[str(i)]:raise ValueError('Frozen layout changed')
        status('running',layout_id=i)
        case=out/f'case_{i}'
        cmd=['./isaaclab.sh','-p',str(root.parents[1]/'scripts/collect_paired_sorting.py'),*settings,'--layout-start',str(i),'--diagnostic-layout-json',str(layout_paths[str(i)]),'--out-dir',str(case)]
        with (out/f'case_{i}.log').open('w') as log:r=subprocess.run(cmd,cwd=root.parents[2]/'IsaacLab',env=env,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
        if r.returncode:raise RuntimeError(f'Collector {i} exit {r.returncode}')
        for script in ('audit_contacts.py','review_diagnostics.py'):
            with (out/f'{i}_{script}.log').open('w') as log:subprocess.run([env['CONDA_PREFIX']+'/bin/python',str(root/script),str(case)],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    for path,digest in old['source_sha256'].items():
        if sha(path)!=digest:raise ValueError('Frozen source changed: '+path)
    (out/'TERMINAL_SOURCE_VERIFICATION.json').write_text(json.dumps(dict(all_frozen_sources_match=True,training_ready=False)))
    status('numeric_complete_actual_visual_review_pending')
except BaseException as exc:
    status('runtime_failed',error=str(exc));raise
