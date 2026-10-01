"""Uninstalled collection-only v2 contract. This never approves training data."""
from pathlib import Path
import hashlib,json

CATALOG_SHA256='e6435d54d18a9b5a95f374e1b62a46fe98045952f9df5da5aaf1f9c83eb01c42'
EXTRA_SOURCES={'simfoundry/data/contact_bout_yaw.py','simfoundry/data/waist_pilot_protocol.py','simfoundry/data/waist_trial_collection.py'}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def validate_trial_schedule(contract):
    if (contract.get('version')!=2 or contract.get('admission_kind')!='frozen_trial_collection'
            or contract.get('collection_admission_only') is not True
            or contract.get('training_ready') is not False or contract.get('feasibility')!=[]):
        raise ValueError('Trial contract grants collection only, not feasibility or training approval')
    # The first trial uses the better verified controller settings, with the
    # newly experimental heading feature explicitly disabled. Future changes
    # need an explicit revised trial protocol instead of silent option uptake.
    if contract['collector_settings'].get('expert_top_contact_bout_yaw_hold') is not False:
        raise ValueError('Unregistered experimental heading profile in trial collection')
    binding=contract.get('trial_plan',{})
    if set(binding)!={'catalog_path','catalog_sha256','group_plan_path','group_plan_sha256'}:
        raise ValueError('Incomplete frozen trial plan binding')
    catalog=Path(binding['catalog_path']);group=Path(binding['group_plan_path'])
    if binding['catalog_sha256']!=CATALOG_SHA256 or sha(catalog)!=CATALOG_SHA256:
        raise ValueError('Trial catalog is not the registered pre-outcome proposal')
    if group.resolve().parent!=catalog.resolve().parent:
        raise ValueError('Trial group must belong to the bound catalog directory')
    proposal=json.loads(catalog.read_text());expected=proposal['plan_sha256'].get(group.name)
    if not expected or expected!=binding['group_plan_sha256'] or sha(group)!=expected:
        raise ValueError('Trial group is not frozen before outcomes')
    schedule=json.loads(group.read_text())
    if (contract['layouts']!=schedule['layouts'] or contract['wait_layouts']!=schedule['wait_layouts']):
        raise ValueError('Trial changed original geometry, category swaps, wait, IDs or split')
    if not EXTRA_SOURCES<=set(contract['controller_source_sha256']):
        raise ValueError('Trial source bindings omit admission/control dependencies')
    for relative,digest in contract['controller_source_sha256'].items():
        if len(digest)!=64 or any(x not in '0123456789abcdef' for x in digest):
            raise ValueError('Invalid trial source digest')
    return {d['layout_id'] for d in schedule['layouts']+schedule['wait_layouts']}

def validate_trial_sources(contract,repo,*,require_live_sources):
    if type(require_live_sources) is not bool:
        raise ValueError('Explicit source validation mode required')
    if require_live_sources:
        for relative,digest in contract['controller_source_sha256'].items():
            path=Path(relative)
            if path.is_absolute() or '..' in path.parts or sha(Path(repo)/path)!=digest:
                raise ValueError('Trial controller/admission source changed')
    # Historical data is checked against each complete recorded source archive
    # by the unchanged audit_waist_pilot_episode, never against replacement code.
