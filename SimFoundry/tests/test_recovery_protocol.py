import unittest,json,tempfile
from pathlib import Path
import numpy as np
from simfoundry.data.recovery_protocol import validate_contract,audit_force_trace

class RecoveryProtocolTests(unittest.TestCase):
    def test_registration_requires_explicit_review_and_exact_scope(self):
        request=dict(layouts=[],waits=[31000],push_force=0,wait_force=40,wait_side='both',wait_start=20)
        item=dict(layouts=[],wait_layouts=[31000],push_force_n=0,wait_force_n=40,wait_force_side='both',wait_force_start=20)
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'contract.json'
            p.write_text(json.dumps(dict(approved_for_pilot=False,collections=[item])))
            with self.assertRaises(ValueError):validate_contract(p,**request)
            p.write_text(json.dumps(dict(approved_for_pilot=True,collections=[item])))
            self.assertEqual(len(validate_contract(p,**request)),64)
            with self.assertRaises(ValueError):validate_contract(p,**{**request,'wait_force':80})
    def test_trace_rejects_missing_frames_wrong_body_and_off_window_force(self):
        meta=dict(wait_force_n=80,wait_force_side='both',wait_force_start=20)
        rows=[dict(step=t,bodies=['left_hand','right_hand'],force_per_body_world_N=[80*np.sin(np.pi*(t-19)/7) if 20<=t<=25 else 0,0,0]) for t in range(70)]
        self.assertTrue(audit_force_trace(meta,'wait_no_package',70,rows))
        with self.assertRaises(ValueError):audit_force_trace(meta,'wait_no_package',70,rows[:-1])
        rows[0]['force_per_body_world_N'][0]=1
        with self.assertRaises(ValueError):audit_force_trace(meta,'wait_no_package',70,rows)
        rows[0]['force_per_body_world_N'][0]=0;rows[21]['bodies']=['parcel_box']
        with self.assertRaises(ValueError):audit_force_trace(meta,'wait_no_package',70,rows)
