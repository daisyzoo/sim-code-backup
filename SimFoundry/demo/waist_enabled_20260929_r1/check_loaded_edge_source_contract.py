"""Exercise new source/provenance contract using clearly synthetic archives.
All parent snapshots are read-only links; changed stage files copied into a new
fixture only. This proves source selection/rejection, NOT physical provenance.
"""
from pathlib import Path
import sys,json,hashlib,tempfile,copy,datetime
w=Path(__file__).resolve().parent;repo=w.parents[1];sys.path[:0]=[str(w),str(repo)]
from audit_loaded_edge_pose_live import source_contract
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();stage=w/'staged_loaded_edge_coverage';oldstage=w/'staged_recontact_pose';root=Path(tempfile.mkdtemp(prefix='loaded_edge_source_fixture_',dir='/tmp'));rows=[];negative=[];sources={}
for cid,task in [(840001,'push_box_to_bin'),(840004,'nudge_mailer_to_bin'),(840000,'push_box_to_bin'),(841000,'wait_no_package')]:
    original=w/'recontact_pose_groups_r1'/f'case_{cid}';case=root/f'case_{cid}';ep=case/f'layout_{cid}_{task}';ep.mkdir(parents=True);snap=case/'source_snapshot';snap.mkdir();prov=json.loads((original/'provenance.json').read_text());prov['args']['loaded_edge_coverage']=True;prov['fixture_only']=True;source={}
    for name,h in prov['source_sha256'].items():
        src=original/'source_snapshot'/name;assert sha(src)==h;sources[str(src)]=h
        if str(oldstage.relative_to(repo))+'/' in name:
            name=name.replace(str(oldstage.relative_to(repo)),str(stage.relative_to(repo)));src=repo/name
        dst=snap/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.symlink_to(src);source[name]=sha(src)
    for name in ['loaded_edge_coverage_current_contact.py','loaded_edge_coverage_adapter.py']:
        src=stage/name;rel=str(src.relative_to(repo));dst=snap/rel;dst.parent.mkdir(parents=True,exist_ok=True);dst.symlink_to(src);source[rel]=sha(src)
    prov['source_sha256']=source;(case/'provenance.json').write_text(json.dumps(prov))
    original_ep=original/ep.name
    for name in ['raw.npz','frontal_bypass.json']:
        if (original_ep/name).exists():(ep/name).symlink_to(original_ep/name);sources[str(original_ep/name)]=sha(original_ep/name)
    assert source_contract(ep)==stage;rows.append({'layout_id':cid,'task':task,'archive_sources':len(source),'passed':True})
    if not negative:
        original_bytes=(case/'provenance.json').read_bytes()
        for label,mutate in [('no_new_flag',lambda p:p['args'].__setitem__('loaded_edge_coverage',False)),('wrong_role',lambda p:p['args'].__setitem__('role','train')),('assist',lambda p:p['args'].__setitem__('push_assist',True)),('wrong_motion',lambda p:p['args'].__setitem__('motion_protocol','waist_locked_v1')),('wrong_waist',lambda p:p['args'].__setitem__('waist_limit_rad',1.3)),('wrong_hash',lambda p:p['source_sha256'].__setitem__(str((stage/'collect_paired_sorting.py').relative_to(repo)),'0'*64)),('missing_helper',lambda p:p['source_sha256'].pop(str((stage/'loaded_edge_coverage_adapter.py').relative_to(repo))))]:
            bad=copy.deepcopy(prov);mutate(bad);(case/'provenance.json').write_text(json.dumps(bad))
            try:source_contract(ep)
            except AssertionError:negative.append(label)
            else:raise AssertionError('accepted '+label)
            finally:(case/'provenance.json').write_bytes(original_bytes)
        # A self-consistent but old collector archive must still fail stage binding.
        rel=str((stage/'collect_paired_sorting.py').relative_to(repo));dst=snap/rel;dst.unlink();dst.symlink_to(oldstage/'collect_paired_sorting.py');bad=copy.deepcopy(prov);bad['source_sha256'][rel]=sha(dst);(case/'provenance.json').write_text(json.dumps(bad))
        try:source_contract(ep)
        except AssertionError:negative.append('self_consistent_wrong_collector')
        else:raise AssertionError('accepted wrong collector')
        finally:dst.unlink();dst.symlink_to(stage/'collect_paired_sorting.py');(case/'provenance.json').write_bytes(original_bytes)
    for name in source:sources[str(repo/name)]=sha(repo/name)
for p in [Path(__file__),w/'audit_loaded_edge_pose_live.py',w/'audit_recontact_pose_live.py']:sources[str(p)]=sha(p)
out=dict(passed=True,created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,fixture_root=str(root),rows=rows,negative_checks=negative,source_sha256=sources,physical_validation=False,training_ready=False);assert len(rows)==4 and len(negative)==8
(stage/'SOURCE_CONTRACT_CHECK.json').write_text(json.dumps(out,indent=2));print('PASS',len(rows),len(negative))
