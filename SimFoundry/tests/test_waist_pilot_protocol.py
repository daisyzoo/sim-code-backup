import unittest
from copy import deepcopy
from simfoundry.data.waist_pilot_protocol import validate_manifest, semantic_settings, GATES, REQUIRED_SOURCES


class WaistManifestTests(unittest.TestCase):
    def setUp(self):
        layouts=[dict(layout_id=81000,geometry_group='g',assignment='normal',planned_split='train',seed=1,box_xyz=[.43,.15,.7725],mailer_xyz=[.46,-.15,.77],box_yaw=.12,mailer_yaw=-.08),dict(layout_id=81001,geometry_group='g',assignment='swapped',planned_split='train',seed=1,box_xyz=[.46,-.15,.7725],mailer_xyz=[.43,.15,.77],box_yaw=-.08,mailer_yaw=.12)]
        self.c=dict(version=1,motion_protocol='waist_yaw_enabled_v1',approved_for_pilot=True,gates=dict(GATES),layouts=layouts,wait_layouts=[dict(layouts[0],layout_id=82000,geometry_group='wait_g')],feasibility=[{'fixture':'schema only; physical evidence checked separately'}],pilot_collector_sha256='a'*64,controller_source_sha256={x:'b'*64 for x in REQUIRED_SOURCES},collector_settings=dict(motion_protocol='waist_yaw_enabled_v1',policy_port=0,idle=False,waist_probe=False,newton_contacts=True,wait_force_n=0.,push_force_n=0.,waist_coordinated_expert=True,bounded_coupled_ik=True,steps=960,wait_steps=70,waist_limit_rad=1.,waist_wait_tolerance_rad=.01,environment_seed=0))

    def test_valid_schema_does_not_claim_physics_or_collection_admission(self):
        self.assertEqual(validate_manifest(self.c),{'g':[81000,81001]})

    def test_original_gates_and_missing_sources_cannot_be_relaxed(self):
        for key,value in [('non_target_max_xy_m',.02),('zero_first_action',False),('policy_horizon',50),('assist_frames',1)]:
            c=deepcopy(self.c);c['gates'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):validate_manifest(c)
        c=deepcopy(self.c);c['controller_source_sha256'].pop(next(iter(REQUIRED_SOURCES)))
        with self.assertRaises(ValueError):validate_manifest(c)

    def test_missing_swap_wait_or_test_split_rejected(self):
        for key,value in [('layouts',self.c['layouts'][:1]),('wait_layouts',[])]:
            c=deepcopy(self.c);c[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):validate_manifest(c)
        c=deepcopy(self.c);c['layouts'][0]['planned_split']='test'
        with self.assertRaises(ValueError):validate_manifest(c)

    def test_protocol_seed_force_and_waist_bounds_are_exact(self):
        for key,value in [('environment_seed',None),('environment_seed',True),('push_force_n',1.),('idle',True),('waist_limit_rad',1.01),('waist_limit_rad',float('nan')),('wait_steps',49),('steps',False)]:
            c=deepcopy(self.c);c['collector_settings'][key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):validate_manifest(c)

    def test_scheduling_removal_does_not_remove_physics_or_seed(self):
        a=dict(role='diagnostic',out_dir='old',layout_start=1,extended_waist_diagnostic=True,environment_seed=0,waist_limit_rad=1.,steps=960,newton_contacts=True)
        b=dict(a,role='pilot',out_dir='new',layout_start=8,extended_waist_diagnostic=False)
        self.assertEqual(semantic_settings(a),semantic_settings(b))
        for key,value in [('environment_seed',1),('steps',320),('newton_contacts',False),('waist_limit_rad',.8)]:
            self.assertNotEqual(semantic_settings(a),semantic_settings(dict(b,**{key:value})))

    def test_wait_requires_reproducible_full_layout_not_id_only(self):
        c=deepcopy(self.c);c['wait_layouts']=[dict(layout_id=82000,planned_split='train')]
        with self.assertRaisesRegex(ValueError,'id/seed'):validate_manifest(c)
        c=deepcopy(self.c);del c['wait_layouts'][0]['box_xyz']
        with self.assertRaisesRegex(ValueError,'coordinates'):validate_manifest(c)

    def test_new_contact_and_route_dependencies_cannot_be_omitted(self):
        for source in ('simfoundry/data/front_top_route.py','simfoundry/data/front_clearance_progress.py','simfoundry/data/tabletop_route_candidates.py','simfoundry/data/projected_support_reference.py','assets/robots/g1_hand_support_vertices.json','simfoundry/data/object_relative_push.py'):
            c=deepcopy(self.c);del c['controller_source_sha256'][source]
            with self.subTest(source=source),self.assertRaisesRegex(ValueError,'source bindings'):validate_manifest(c)
