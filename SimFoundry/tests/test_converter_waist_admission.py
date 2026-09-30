"""Converter dispatch/coverage integration. Fixtures are not physical evidence."""
import hashlib, importlib.util, json, tempfile, unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('converter_waist_test',Path(__file__).resolve().parents[1]/'scripts/prepare_paired_sorting_lerobot.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)

class WaistConverterAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.episodes={};review={}
        for identifier in (81000,81001):
            name=f'layout_{identifier}_wait_no_package';p=self.root/name;p.mkdir()
            (p/'raw.npz').write_bytes(name.encode());(p/'quality.json').write_text('{"passed":true}')
            review[name+'/raw.npz']=hashlib.sha256((p/'raw.npz').read_bytes()).hexdigest()
            meta=dict(collection_role='pilot',idle_diagnostic=False,assist_frames=0,
                motion_protocol=c.WAIST_PROTOCOL,layout_id=identifier,
                layout=dict(planned_split='train' if identifier==81000 else 'validation',geometry_group='wait_'+str(identifier),assignment='normal'))
            self.episodes[name]=SimpleNamespace(collect_meta=meta,task_id='wait_no_package',instruction=c.PAIRED_SORTING_PROMPTS['wait_no_package'])
        (self.root/'STATUS.json').write_text('{"status":"numeric_pass_visual_review_pending"}')
        (self.root/'review.json').write_text(json.dumps(dict(approved=True,method='test fixture only',episodes=review)))
        (self.root/'provenance.json').write_text(json.dumps(dict(args=dict(layouts=0,wait_episodes=2))))
        self.contract=dict(layouts=[],wait_layouts=[dict(layout_id=i) for i in (81000,81001)])
        self.write_contract()
    def write_contract(self):
        (self.root/'waist_pilot_contract.json').write_text(json.dumps(self.contract))
    def auditor(self,path,ep,provenance):
        return dict(planned_split=ep.collect_meta['layout']['planned_split'],contract_sha256='a'*64,original_audit=dict(passed=True))
    def check(self,side_effect=None):
        with patch.object(c,'load_episode',side_effect=lambda p:self.episodes[p.parent.name]), \
             patch.object(c,'audit_waist_pilot_episode',side_effect=side_effect or self.auditor) as audit, \
             patch.object(c,'audit_rollout',side_effect=AssertionError('must not rerun locked-waist gate')), \
             patch.object(c,'validate_spatial_contract',side_effect=AssertionError('must not use legacy spatial contract')):
            result=c.checked_sources([self.root]);self.assertEqual(audit.call_count,2);return result
    def test_explicit_waist_uses_new_audit_and_preserves_wait_metadata(self):
        rows=self.check()
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[0]['motion_protocol'],c.WAIST_PROTOCOL)
        self.assertEqual(rows[0]['waist_pilot_contract_sha256'],'a'*64)
        self.assertIn('wait_geometry_group',rows[0]);self.assertNotIn('geometry_group',rows[0])
    def test_contract_audit_failure_is_fatal(self):
        with self.assertRaisesRegex(ValueError,'bad source'):
            self.check(lambda *args:(_ for _ in ()).throw(ValueError('bad source')))
    def test_failed_new_numeric_report_is_fatal(self):
        def failed(*args):
            d=self.auditor(*args);d['original_audit']['passed']=False;return d
        with self.assertRaisesRegex(ValueError,'numeric gate failed'):self.check(failed)
    def test_saved_failed_quality_is_fatal(self):
        p=next(self.root.glob('layout_*/quality.json'));p.write_text('{"passed":false}')
        with self.assertRaisesRegex(ValueError,'numeric gate failed'):self.check()
    def test_missing_contract_episode_is_fatal(self):
        self.contract['wait_layouts'].append(dict(layout_id=81002));self.write_contract()
        with self.assertRaisesRegex(ValueError,'contract episode coverage'):self.check()
    def test_extra_episode_outside_contract_is_fatal(self):
        self.contract['wait_layouts'].pop();self.write_contract()
        with self.assertRaisesRegex(ValueError,'contract episode coverage'):self.check()
    def test_diagnostic_rejected_before_new_auditor(self):
        for ep in self.episodes.values():ep.collect_meta['collection_role']='diagnostic'
        with self.assertRaisesRegex(ValueError,'diagnostic or assisted'):
            self.check(lambda *args:(_ for _ in ()).throw(AssertionError('must reject first')))
    def test_unknown_protocol_rejected(self):
        for ep in self.episodes.values():ep.collect_meta['motion_protocol']='unsupported_v2'
        with self.assertRaisesRegex(ValueError,'unknown motion protocol'):self.check()
    def test_conflicting_old_expert_rejected(self):
        for ep in self.episodes.values():ep.collect_meta['twopass_expert']={}
        with self.assertRaisesRegex(ValueError,'conflicting waist/twopass'):self.check()
    def test_test_split_rejected(self):
        for ep in self.episodes.values():ep.collect_meta['layout']['planned_split']='test'
        with self.assertRaisesRegex(ValueError,'preassigned test geometry'):self.check()
    def test_legacy_locked_path_still_uses_original_audit(self):
        import numpy as np
        for name,ep in self.episodes.items():
            ep.collect_meta.pop('motion_protocol');ep.collect_meta['layout'].pop('geometry_group')
            ep.q=np.zeros((2,23));ep.action=ep.q.copy()
            np.savez(self.root/name/'trace.npz',fixture=np.zeros(2))
        with patch.object(c,'load_episode',side_effect=lambda p:self.episodes[p.parent.name]), \
             patch.object(c,'audit_waist_pilot_episode',side_effect=AssertionError('legacy path')), \
             patch.object(c,'audit_rollout',return_value={'passed':True}) as audit:
            rows=c.checked_sources([self.root])
        self.assertEqual(audit.call_count,2)
        self.assertTrue(all(r['motion_protocol']=='waist_locked_v1' for r in rows))

    def test_missing_contract_file_rejected(self):
        (self.root/'waist_pilot_contract.json').unlink()
        with self.assertRaises(FileNotFoundError):self.check()

if __name__=='__main__':unittest.main()
