"""Independently bind all static attempts, including rejected first-front plans.
No candidate import or planning rerun; rejected paths confer no task success.
"""
import numpy as np
from scipy.spatial.transform import Rotation
from audit_trailing_preflight import SelectionAudit as ParentSelectionAudit
from audit_unloaded_wrist_prior_live import near

class SelectionAudit(ParentSelectionAudit):
    def verify_selection(self, planning, *, current, previous_q, previous_command, decay, scene, step):
        assert scene['side']=='right'
        offset=(Rotation.from_quat(scene['target_quat']).as_matrix().T@np.array([0.,.020,0.]))[:2]
        near(planning['landing_preference_local_xy'],offset,1e-12)
        assert planning['planning_xy_reserve_m']==.0005
        assert np.all(abs(offset)<=np.asarray(scene['core_size'])[:2]/2-.012)
        q=np.asarray(current,float)
        assert planning['scene']==scene and planning['step']==step
        near(planning['start'],q,1e-7)
        measured,_=self.geometry(q,scene)
        if not measured['accepted']:
            assert planning['accepted'] is False and planning['reason']=='current_unloaded_geometry_rejected'
            assert planning['attempts']==[] and 'transport_preflight' not in planning
            return dict(passed=True,trials=0,selected=None,rejected_current_geometry=True,training_ready=False)
        usable=self.verify_static_attempts(planning,q,scene)
        if not usable:
            assert planning['accepted'] is False and planning['reason']=='no_verified_center_endpoint_and_path'
            assert 'transport_preflight' not in planning
            return dict(passed=True,trials=0,selected=None,rejected_static_paths=True,training_ready=False)
        assert 'transport_preflight' in planning
        return super().verify_selection(planning,current=q,previous_q=previous_q,previous_command=previous_command,decay=decay,scene=scene,step=step)

    def verify_static_attempts(self,created,q,scene):
        offset=(Rotation.from_quat(scene['target_quat']).as_matrix().T@np.array([0.,.020,0.]))[:2]
        attempts=created['attempts'];assert [a['seed'] for a in attempts]==['actual_unloaded','neutral_waist_-0.5','neutral_waist_0.0','neutral_waist_0.5']
        usable=[];axis=np.linalg.eigh(np.cov(self.hand.vertices[scene['side']].T))[1][:,0]
        if 'thin_axis_local' in created:near(abs(np.array(created['thin_axis_local'])@axis),1.,1e-10)
        for attempt in attempts:
            assert type(attempt['status']) is int and type(attempt['endpoint_accepted']) is bool
            assert type(attempt['iterations']) is int and 0<=attempt['iterations']<=220
            if attempt['endpoint'] is None:
                assert not attempt['endpoint_accepted'] and attempt['nominal_path'] is None;continue
            x=np.asarray(attempt['endpoint']);g,d=self.geometry(x,scene)
            align=abs(d['rotation'][:,2]@d['pose'][:3,:3]@axis)
            minimum=float(min(align**2-.8**2,*list(.0015-abs(d['point'][:2]-offset)),g['active_above_top_m']-.006,.007-g['active_above_top_m'],g['inactive_lowest_z_m']-.84,g['elbow_gap_m']-.005))
            near(attempt['minimum_constraint_m'],minimum,2e-8);near(attempt['objective'],float(np.sum((x-q)**2)),1e-9)
            accepted=bool(attempt['status']==0 and minimum>=-2e-7 and g['accepted'] and np.all(x>=self.lo-2e-7) and np.all(x<=self.hi+2e-7))
            assert attempt['endpoint_accepted'] is accepted
            path=attempt['nominal_path']
            if not accepted:assert path is None;continue
            count=max(1,int(np.ceil(max(abs(x-q)/(self.limits*.25)))))
            waypoints=np.array([np.clip(q+(x-q)*i/count,self.lo,self.hi) for i in range(1,count+1)])
            near(path['waypoints'],waypoints,1e-10);assert len(path['checks'])==len(waypoints)
            checks=[]
            for stored,state in zip(path['checks'],waypoints):
                actual,_=self.geometry(state,scene);self.compare_geometry(stored,actual);checks.append(actual['accepted'])
            assert path['accepted'] is all(checks)
            if all(checks):usable.append(attempt)
        return usable
