"""Unwired candidate: exact fresh waist pilot admission before simulator launch.

Authorizes only collection against verified complete-group evidence; never
promotes diagnostic files or approves resulting data for training.
"""
from dataclasses import dataclass
from pathlib import Path
from copy import deepcopy
import hashlib
from simfoundry.data.waist_pilot_protocol import validate_waist_contract, semantic_settings

@dataclass(frozen=True)
class WaistPilotAdmission:
    contract_sha256: str
    contract_path: Path
    push_layouts: dict
    wait_layouts: dict

    def layout(self,identifier,*,wait=False):
        entries=self.wait_layouts if wait else self.push_layouts
        if identifier not in entries:raise ValueError('Layout outside exact admitted collection schedule')
        return deepcopy(entries[identifier])


def prepare_waist_pilot(settings,collector_path):
    path=settings.get('waist_pilot_contract')
    if not path:return None
    if settings.get('role')!='pilot' or settings.get('motion_protocol')!='waist_yaw_enabled_v1':
        raise ValueError('Waist contract only permits explicit fresh waist pilot')
    if any(settings.get(k) for k in ('spatial_pilot_contract','recovery_pilot_contract','diagnostic_layout_json')):
        raise ValueError('Cannot combine waist contract with another layout/admission source')
    if settings.get('policy_port') or settings.get('idle') or settings.get('waist_probe'):
        raise ValueError('Cannot admit policy/idle/probe as expert pilot')
    # Full validator recomputes exact geometry, original gates, visual evidence,
    # frozen physics/controller snapshots and semantic settings.
    contract,digest=validate_waist_contract(path)
    if semantic_settings(settings) != contract.get('prelaunch_collector_settings'):
        raise ValueError('Fresh prelaunch settings differ from exact waist contract')
    actual=hashlib.sha256(Path(collector_path).read_bytes()).hexdigest()
    if actual!=contract['pilot_collector_sha256']:
        raise ValueError('Fresh collector differs from exact contract source')
    def schedule(start_key,count_key,registered):
        count=settings.get(count_key);start=settings.get(start_key)
        if type(count) is not int or count<0 or type(start) is not int or start<0:
            raise ValueError('Invalid explicit collection schedule')
        registered={d['layout_id']:d for d in registered}
        requested=range(start,start+count)
        if not set(requested)<=set(registered):raise ValueError('Scheduled layout not registered in contract')
        return {identifier:deepcopy(registered[identifier]) for identifier in requested}
    pushes=schedule('layout_start','layouts',contract['layouts'])
    waits=schedule('wait_layout_start','wait_episodes',contract['wait_layouts'])
    if not pushes and not waits:raise ValueError('Empty fresh collection schedule')
    if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=digest:
        raise ValueError('Waist contract changed during validation')
    return WaistPilotAdmission(digest,Path(path).resolve(),pushes,waits)


def finalize_waist_pilot(admission, settings, collector_path):
    """After AppLauncher mutates args, verify resolved settings before env/data."""
    if admission is None:
        return
    contract, digest = validate_waist_contract(admission.contract_path, settings=settings)
    if digest != admission.contract_sha256:
        raise ValueError('Waist contract changed during launcher initialization')
    if hashlib.sha256(Path(collector_path).read_bytes()).hexdigest() != contract['pilot_collector_sha256']:
        raise ValueError('Fresh collector changed during launcher initialization')
