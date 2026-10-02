"""Independent recovery-command geometry and state-record verifier.
No import or replay of candidate solvers. This component does not replace the
original contact/pressure/phase/path audits, full-horizon task gates or physics.
"""
from pathlib import Path
import copy
import numpy as np
from audit_self_clearance_task_optimality import IndependentElbows
from audit_unloaded_wrist_prior_live import HandModel


class RecoveryVerifier:
    def __init__(self, root, stage):
        root,stage=Path(root),Path(stage)
        urdf=root/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf'
        vertices=root/'assets/robots/g1_hand_support_vertices.json'
        self.hand=HandModel(urdf,vertices)
        self.elbows=IndependentElbows(stage/'elbow_torso_hulls.json',urdf)
        import json
        self.vertices=json.loads(vertices.read_text())['vertices']
        from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI
        self.lower=np.asarray(U1_JOINT_LIMIT_LO[12:23],float).copy()
        self.upper=np.asarray(U1_JOINT_LIMIT_HI[12:23],float).copy()
        self.lower[0]=-.98;self.upper[0]=.98
        self.steps=np.array([.015]+[.04]*10)

    def verify(self, record, *, row, coordinate, current, previous, action, geometry):
        t=record['step'];kind=record['kind'];assert type(t) is int and t>=1
        assert kind in ['loaded_recovery','unload']
        parent=record['parent_row'];coord=record['parent_coordinate']
        assert t==row['step']==coordinate['step']==parent['step']==coord['step']
        assert parent['mode']=='top_push' and not parent.get('route_stop_reason') and not parent.get('release_reason')
        assert parent['rear_cop_centering']['override'] is True
        assert not coord.get('region_joint_override') and not coord.get('terminal_joint_hold')
        ccopy=copy.deepcopy(coordinate);annotation=ccopy.pop('rear_corridor_override')
        assert ccopy==coord and annotation==dict(kind=kind,step=t,record_file='rear_corridor_recovery.json')
        assert row['rear_corridor_override']==dict(kind=kind,step=t,parent_evidence='rear_corridor_recovery.json')
        q,prev,cmd=[np.asarray(x,float) for x in [current,previous,action]]
        assert all(x.shape==(11,) and np.isfinite(x).all() for x in [q,prev,cmd])
        assert np.array_equal(q,coord['upper_q']) and np.array_equal(q,coord['task_inputs']['current']) and np.array_equal(prev,coord['task_inputs']['previous'])
        assert np.array_equal(cmd,record['emitted_command']) and np.array_equal(cmd,record['proposed_command'])
        assert np.array_equal(cmd,cmd.astype(np.float32).astype(float))
        assert np.all(cmd>=self.lower-2e-7) and np.all(cmd<=self.upper+2e-7)
        assert np.all(abs(cmd-q)<=self.steps+2e-7) and np.max(abs(cmd-prev))<=.0550002
        gaps=self.elbows.gap(cmd);assert min(gaps)>=.005-2e-7
        for name,value in geometry.items():assert np.allclose(np.asarray(value),np.asarray(record['geometry'][name]),atol=2e-7,rtol=0),name
        target,other,size,osize,core=[np.asarray(geometry[k],float) for k in ['target_xyz','obstacle_xyz','target_size','obstacle_size','core_size']]
        R,OR=[np.asarray(geometry[k],float) for k in ['target_rotation','obstacle_rotation']]
        assert all(a.shape==(3,) and np.isfinite(a).all() for a in [target,other,size,osize,core])
        assert np.min(size)>0 and np.min(osize)>0 and np.min(core)>.02
        for rotation in [R,OR]:assert rotation.shape==(3,3) and np.allclose(rotation.T@rotation,np.eye(3),atol=1e-6) and np.linalg.det(rotation)>.99999
        rad=np.abs(R)@size/2;orad=np.abs(OR)@osize/2
        deficit=other[0]+orad[0]+rad[0]+.020-target[0]
        side=coord['active_side'];assert side in ['right','left'];direction=-1 if side=='right' else 1
        assert deficit>0 and direction*(target[1]-other[1])<=rad[1]+orad[1]+.020
        rr=record['recovery'];assert abs(rr['rear_deficit_m']-deficit)<1e-12
        requested=min(.002,max(.001,float(deficit)))
        assert abs(rr['requested_x_m']-requested)<1e-12
        assert min(target[0]-rad[0]-.28,.88-target[0]-rad[0],target[1]-rad[1]+.75,.75-target[1]-rad[1])>=.005
        assert max(target[0]+deficit,target[0]+requested)+rad[0]<=.875
        T=self.hand.fk(cmd,side);T0=self.hand.fk(q,side);offset=np.asarray(parent['control_offset_local'])
        measured=T0[:3,3]+T0[:3,:3]@offset;reference=T[:3,3]+T[:3,:3]@offset;delta=reference-measured
        assert np.max(abs(measured-np.asarray(parent['observed_support_xyz'])))<=2e-6
        assert np.max(abs(reference-np.asarray(row['target_xyz'])))<=2e-10
        applied=rr if kind=='loaded_recovery' else record['unload']
        attempts=[a for a in applied['attempts'] if a['accepted']];assert len(attempts)==1 and np.array_equal(attempts[0]['command'],cmd)
        assert applied['applied'] is True and np.max(abs(delta-np.asarray(applied['reference_delta_xyz_m'])))<=2e-10
        event=record['commit'];expected=copy.deepcopy(parent)
        if kind=='loaded_recovery':
            assert rr['reason']=='nominal_rear_corridor_recovery' and not rr['requires_recontact']
            assert abs(delta[1])<=1e-7 and .0001-1e-7<=delta[0]<=requested+1e-7
            cop=R.T@(np.asarray(parent['rear_cop_centering']['cop_world'])-target)
            axes=[k for k in [0,1] if core[k]/2-abs(cop[k])<=.010]
            inward=.0005 if side=='right' else 0.
            assert rr['near_core_axes']==axes and rr['inward_requirement_m']==inward
            for k in axes:assert -np.sign(cop[k])*R[:,k]@delta-inward>=-1e-7
            e=np.asarray(coord['task_inputs']['error']).copy();assert np.array_equal(e,rr['original_error']);i=3 if side=='right' else 0;e[i]=.72*requested;e[i+1]=0.
            assert np.array_equal(e,rr['recovery_error'])
            assert event['kind']=='committed_recovery_reference'
            assert np.max(abs(np.asarray(event['new']['command'])-reference))<2e-10
            assert np.max(abs(np.asarray(event['new']['last_waypoint_xy'])-reference[:2]))<2e-10
            assert event['new']['push_x_anchor']==reference[0]
            expected.update(target_xyz=row['target_xyz'],push_x_anchor_m=event['new']['push_x_anchor'])
        else:
            assert rr['reason']=='no_verified_loaded_recovery' and rr['requires_recontact'] and not rr['applied']
            assert record['unload']['reason']=='nominal_vertical_unload'
            assert max(abs(delta[:2]))<=1e-7 and .0005-1e-7<=delta[2]<=.003+1e-7
            v=np.asarray(self.vertices[side]);low=np.min((v@T[:3,:3].T+T[:3,3])[:,2])-np.min((v@T0[:3,:3].T+T0[:3,3])[:,2]);assert low>=.0005-1e-7
            assert event['kind']=='started_original_recontact_lift'
            assert event['before']['recontacts']==parent['recontacts'] and event['recontacts']==parent['recontacts']+1
            assert event['before']['bias_m']==parent['contact_load']['stored_z_bias_m'] and event['bias_m']==0.
            assert event['filtered_n']==event['before']['filtered_n']==parent['contact_load']['filtered_vertical_load_n']
            expected.update(target_xyz=row['target_xyz'],mode='top_lift',recontacts=parent['recontacts']+1,last_recontact_reason='rear_corridor_no_verified_loaded_step')
            expected['contact_load'].update(applied_z_bias_m=0.,stored_z_bias_m=0.,rear_recovery_reset_after_original_update=True)
        expected['rear_corridor_override']=row['rear_corridor_override']
        assert expected==row,'Unexpected change to original controller evidence'
        return dict(passed=True,step=t,kind=kind,independent_delta_xyz_m=delta.tolist(),independent_elbow_gaps_m=gaps.tolist(),training_ready=False)
