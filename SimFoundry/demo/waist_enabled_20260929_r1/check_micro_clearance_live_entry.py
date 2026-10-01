"""Exercise actual auditor entry on a labeled fixed-input counterfactual fixture.
No physics or training data; immutable physical inputs are linked read-only in /tmp.
"""
from pathlib import Path
import runpy,tempfile,copy,json,sys,os,subprocess,hashlib
import numpy as np
w=Path(__file__).resolve().parent;repo=w.parents[1];stage=w/'staged_micro_clearance_return';ns=runpy.run_path(str(w/'check_micro_clearance_integrated_replay.py'));source_ep=Path(ns['reports'][-1]['episode']);case=Path(tempfile.mkdtemp(prefix='micro_auditor_fixture_'));ep=case/source_ep.name;ep.mkdir();plan=copy.deepcopy(ns['plan']);plan['front_micro_repair_retention']=dict(enabled=True,maximum_excursion_m=.005,minimum_core_margin_m=.01,minimum_normal_load_n=.3,initial_turn_keeps_recontact=True,whole_repair_excursion=True,original_guard_priority=True,scope='Counterfactual auditor fixture, not physical data.')
fr=dict(plan=plan,rows=ns['fullrows']);base_prov=json.loads((source_ep.parent/'provenance.json').read_text());prov=copy.deepcopy(base_prov);prov['args']['front_micro_repair_retention']=True;prov['args']['out_dir']=str(case);prov['fixture_kind']='fixed_recorded_inputs_counterfactual_only';prov['source_sha256']={};sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();parentrel=str((w/'staged_front_diagonal_entry').relative_to(repo));newrel=str(stage.relative_to(repo))
for name in base_prov['source_sha256']:
 newname=name.replace(parentrel,newrel);src=repo/newname if newname!=name else source_ep.parent/'source_snapshot'/name;dst=case/'source_snapshot'/newname;dst.parent.mkdir(parents=True,exist_ok=True);dst.symlink_to(src);prov['source_sha256'][newname]=sha(src)
for name in ['front_top_route_micro.py','front_cop_route_micro.py','micro_clearance_return.py']:
 relative=newrel+'/'+name;dst=case/'source_snapshot'/relative;dst.symlink_to(stage/name);prov['source_sha256'][relative]=sha(stage/name)
for name in ['raw.npz','trace.npz','parcel_orientation.npz','solved_contact_forces.json']:(ep/name).symlink_to(source_ep/name)
encode=lambda x:json.dumps(x,indent=2,default=lambda a:a.tolist() if isinstance(a,np.ndarray) else float(a));(ep/'frontal_bypass.json').write_text(encode(fr));(case/'provenance.json').write_text(encode(prov));report=ep/'MICRO_CLEARANCE_RETURN_LIVE_AUDIT.json';checks=[]
def call(label,success):
 p=subprocess.run([sys.executable,str(w/'audit_micro_clearance_live.py'),str(ep)],capture_output=True,text=True);(case/(label+'.log')).write_text(p.stdout+p.stderr);assert (p.returncode==0)==success,(label,p.stdout,p.stderr)
 if success:assert report.exists() and json.loads(report.read_text())['passed']
 else:assert not report.exists()
 checks.append(dict(case=label,returncode=p.returncode,expected_pass=success,log_sha256=sha(case/(label+'.log'))))
call('positive',True);positive=report.read_bytes();(case/'POSITIVE_REPORT.json').write_bytes(positive);report.unlink();ix=next(i for i,r in enumerate(fr['rows']) if r.get('direction_change_recontact',{}).get('micro_repair_retention',{}).get('retained'))
for label in ['disabled','weakened_margin','source_hash','fake_retained','fake_load','fake_excursion','fake_counter','nonfront_claim']:
 f=copy.deepcopy(fr);p=copy.deepcopy(prov)
 if label=='disabled':p['args']['front_micro_repair_retention']=False
 elif label=='weakened_margin':f['plan']['front_micro_repair_retention']['minimum_core_margin_m']=.005
 elif label=='source_hash':p['source_sha256'][next(iter(p['source_sha256']))]='0'*64
 elif label=='fake_retained':f['rows'][ix]['direction_change_recontact']['micro_repair_retention']['retained']=False
 elif label=='fake_load':f['rows'][ix]['direction_change_recontact']['micro_repair_retention']['normal_load_n']+=1.
 elif label=='fake_excursion':f['rows'][ix]['direction_change_recontact']['micro_repair_retention']['maximum_excursion_m']+=.01
 elif label=='fake_counter':f['rows'][ix]['recontacts']+=1
 else:f['plan']['front_route_selected']=False
 (ep/'frontal_bypass.json').write_text(encode(f));(case/'provenance.json').write_text(encode(p));call(label,False)
(ep/'frontal_bypass.json').write_text(encode(fr));(case/'provenance.json').write_text(encode(prov))
out=dict(passed=True,checks=checks,fixture=str(case),positive_report_sha256=sha(case/'POSITIVE_REPORT.json'),source_episode=str(source_ep),source_sha256={str(p):sha(p) for p in [Path(__file__),w/'audit_micro_clearance_live.py',w/'audit_micro_clearance_return.py',w/'check_micro_clearance_integrated_replay.py',stage/'collect_paired_sorting.py']},scope=__doc__,training_ready=False);(stage/'CLI_CHECK.json').write_text(json.dumps(out,indent=2));print('passed actual CLI positive +8 negative checks',case)
