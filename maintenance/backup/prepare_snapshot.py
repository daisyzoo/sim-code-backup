"""Create a code-only working-tree backup; never read credential-file contents."""
from pathlib import Path
import os,re,json,hashlib,shutil,subprocess,collections,datetime
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'.code-backup/repository';META=ROOT/'.code-backup';OUT.mkdir(exist_ok=True)
CODE={'.py','.pyi','.sh','.bash','.zsh','.fish','.bat','.ps1','.js','.mjs','.cjs','.ts','.tsx','.jsx','.css','.scss','.html','.htm','.c','.cc','.cpp','.cxx','.h','.hpp','.cu','.cuh','.cmake','.rs','.go','.java','.r','.lua','.sql','.patch','.diff'}
TEXT={'.md','.mdx','.rst','.txt','.toml','.yaml','.yml','.ini','.cfg','.json','.xml','.lock','.in','.j2','.jinja','.jinja2','.bddl','.msg','.srv','.action'}
NAMED={'Dockerfile','Makefile','CMakeLists.txt','LICENSE','LICENCE','NOTICE','COPYING','VERSION','.gitignore','.gitattributes','.gitmodules','.dockerignore','.editorconfig','.clang-format','.flake8','.coveragerc','pre-commit'}
SKIP={'.tools','.wheelhouse','.git','.code-backup','.cache','.pytest_cache','.mypy_cache','.ruff_cache','__pycache__','node_modules','.venv','venv','env','dist','build','source_snapshot','runtime_source','substep_runtime_sources','outputs','output','logs','smoke_logs','wandb','checkpoints','checkpoint','hf_home','videos','images','textures','meshes','renders','recordings','generated_data','offline_cu118_bundle','third_party_build','lingbot_bundle_staging','reports','coverage','htmlcov'}
PREFIX_SKIP={'SimFoundry/datasets','lerobot/data','lerobot/models','lerobot/lerobot_v3.0','nvidia/SimFoundry/Data','pic','example_scene'}
SENSITIVE=re.compile(r'(^\.env($|\.)|\.env$|(^|[_\-.])(api[_-]?keys?|credentials?|secrets?|tokens?)([_\-.]|$)|^id_(rsa|ed25519)|\.(pem|key|p12|pfx)$)',re.I)
SECRET=[re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),re.compile(rb'gh[pousr]_[A-Za-z0-9]{30,}'),re.compile(rb'github_pat_[A-Za-z0-9_]{35,}'),re.compile(rb'hf_[A-Za-z0-9]{25,}'),re.compile(rb'sk-(?:proj-)?[A-Za-z0-9_-]{35,}'),re.compile(rb'AKIA[A-Z0-9]{16}'),re.compile(rb'https?://[^\s/:]{1,100}:[^\s/@]{3,100}@')]
prior=json.loads((META/'snapshot_manifest.json').read_text()).get('files',[]) if (META/'snapshot_manifest.json').exists() else []
rows=[];excluded=collections.Counter();sensitive=[];reviews=[];symlinks=[];repos=[]
for dp,ds,fs in os.walk(ROOT,followlinks=False):
 p=Path(dp);rel=p.relative_to(ROOT)
 if (p/'.git').exists():
  def git(*a):return subprocess.run(['git','-C',str(p),*a],capture_output=True,text=True).stdout.strip()
  url=git('config','--get','remote.origin.url');url=re.sub(r'(https?://)[^/]*@',r'\1[redacted]@',url)
  repos.append({'path':str(rel),'origin':url,'commit':git('rev-parse','HEAD'),'branch':git('branch','--show-current')})
 kept=[]
 for d in ds:
  child=p/d;r=child.relative_to(ROOT).as_posix()
  if child.is_symlink():symlinks.append(r);continue
  if d in SKIP or d in {'.agents','.aws','.codex','generated','World'} or d.endswith('.egg-info') or d.startswith(('before_','staged_','.venv')) or r in PREFIX_SKIP or (r.startswith('lerobot/lerobot_sim_')):
   excluded['excluded_directory']+=1;continue
  kept.append(d)
 ds[:]=kept
 for name in sorted(fs):
  src=p/name;r=src.relative_to(ROOT).as_posix();parts=src.relative_to(ROOT).parts
  if src.is_symlink():symlinks.append(r);continue
  ext=src.suffix.lower()
  if SENSITIVE.search(name) and ext not in CODE:sensitive.append({'path':r,'reason':'credential_or_environment_filename'});continue
  if name not in NAMED and ext not in CODE|TEXT and not name.startswith(('Dockerfile.','LICENSE','COPYING','NOTICE')):
   excluded['non_source_extension']+=1;continue
  # Runtime JSON and documentation are not code. Retain experiment scripts only.
  if 'demo' in parts and ext not in CODE:excluded['experiment_output_or_note']+=1;continue
  if 'assets' in parts and ext not in CODE and not name.startswith(('LICENSE','NOTICE')):excluded['model_asset_or_metadata']+=1;continue
  if ext=='.json' and not (any(v in {'config','configs','cfg','cfgs','.vscode','.devcontainer'} for v in parts) or name in {'package.json','package-lock.json','tsconfig.json','jsconfig.json','g1_23_tasks.json'} or r.startswith('SimFoundry/simfoundry/')):
   excluded['non_configuration_json']+=1;continue
  if ext=='.bddl':excluded['benchmark_task_dataset']+=1;continue
  if any(v in {'tokenizer','text_encoder','scheduler','sampled_task','artifacts','metadata','bddl'} for v in parts) and ext not in CODE and name not in NAMED:
   excluded['runtime_or_model_metadata']+=1;continue
  if name.startswith(('events.out','metrics','results','summary')) and ext in {'.json','.txt'}:excluded['runtime_results']+=1;continue
  if src.stat().st_size>5*1024**2:reviews.append({'path':r,'reason':'text_file_over_5MiB'});continue
  data=src.read_bytes()
  if b'\0' in data:excluded['binary_content']+=1;continue
  try:data.decode('utf-8')
  except UnicodeDecodeError:reviews.append({'path':r,'reason':'not_utf8'});continue
  if any(pattern.search(data) for pattern in SECRET):sensitive.append({'path':r,'reason':'potential_secret_pattern'});continue
  # Flag concrete credential assignments for human review; print no values.
  assign=re.search(rb'(?im)^\s*(?:export\s+)?[A-Za-z_]*(?:API_KEY|ACCESS_TOKEN|AUTH_TOKEN|PASSWORD|SECRET_KEY)\s*=\s*[\x22\x27]?([A-Za-z0-9_./+=-]{12,})',data)
  if ext not in CODE and assign and not any(x in assign.group(1).lower() for x in [b'example',b'placeholder',b'your_',b'none',b'getenv',b'os.environ']):
   sensitive.append({'path':r,'reason':'potential_literal_credential_assignment'});continue
  dest=OUT/r;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);dest.chmod(0o755 if src.stat().st_mode&0o111 else 0o644)
  rows.append({'path':r,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
manifest={'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_root':str(ROOT),'snapshot_root':str(OUT),'file_count':len(rows),'bytes':sum(x['bytes'] for x in rows),'files':rows,'excluded_counts':dict(excluded),'sensitive_files_excluded':sensitive,'manual_review':reviews,'symlinks_not_followed':symlinks,'repositories':repos,'scope':'Source working-tree snapshot, no historical git objects. Images/video/datasets/checkpoints/weights/robot assets/cache/generated snapshots/credentials excluded. Dependency source retained where present outside build and staging folders.'}
new_paths={x['path'] for x in rows}
for x in prior:
 if x['path'] not in new_paths:
  stale=OUT/x['path']
  if stale.is_file():stale.unlink()
(META/'snapshot_manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({k:manifest[k] for k in ['file_count','bytes','excluded_counts','sensitive_files_excluded','manual_review']},indent=2))
