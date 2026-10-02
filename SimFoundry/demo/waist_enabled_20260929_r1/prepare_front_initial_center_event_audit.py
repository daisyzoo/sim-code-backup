"""Derive an independent initial-center audit from original geometry/command audit.
All modifications explicit, candidate modules are never imported by the auditor.
"""
from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;source=W/'audit_recontact_pose_events.py';dest=W/'audit_front_initial_center_events.py';assert not dest.exists();s=source.read_text();edits=[]
def edit(old,new):
 global s
 assert s.count(old)==1,old;s=s.replace(old,new);edits.append(dict(old=old,new=new))
edit('recontacts>=1','recontacts==0')
edit("record=dict(accepted=bool(height>=.004 and min(gaps.values())>=.01 and elbow>0 and bounds),", "record=dict(accepted=bool(height>=.004 and min(gaps.values())>=.01 and elbow>=.005-2e-7 and self.hand.minz(q,other)>=.84-2e-7 and bounds),inactive_lowest_z_m=float(self.hand.minz(q,other)),")
edit("    def compare_geometry(self,record,actual):\n", "    def compare_geometry(self,record,actual):\n        near(record['inactive_lowest_z_m'],actual['inactive_lowest_z_m'],2e-9)\n")
start=s.index("            assert self.hand.minz(q,scene['side'])>=.84\n");end=s.index('            self.waypoints=expected;',start)
old=s[start:end]
new="""            near(created['start'],q,1e-7)
            self.verify_center_plan(created,q,scene,a,qp,previous)
            endpoint=np.asarray(created['endpoint']);expected=np.asarray(created['waypoints'])
"""
edit(old,new)
old="        ready=bool(close and min(g['core'][:2]/2-abs(g['point'][:2]))>=.01 and .004<=actual['active_above_top_m']<=.01 and np.all(q>=self.lo-2e-7) and np.all(q<=self.hi+2e-7))"
new="""        pose=np.asarray(c['observed_hand_pose']);verts=self.hand.vertices[scene['side']]
        measured_points=(verts@pose[:3,:3].T+pose[:3,3]-scene['target_xyz'])@g['rotation'];point=measured_points[int(measured_points[:,2].argmin())]
        axis=np.linalg.eigh(np.cov(verts.T))[1][:,0];alignment=abs(g['rotation'][:,2]@pose[:3,:3]@axis)
        near(event['actual_lowest_local'],point,2e-9);near(event['actual_alignment_abs'],alignment,2e-9);assert event['ready_numerical_tolerance']==2e-7
        ready=bool(close and max(abs(point[:2]))<=.002+2e-7 and min(g['core'][:2]/2-abs(point[:2]))>=.01 and .004<=point[2]-g['core'][2]/2<=.01 and alignment>=.8-2e-7 and actual['accepted'] and np.all(q>=self.lo-2e-7) and np.all(q<=self.hi+2e-7))"""
edit(old,new)
s=s.replace('Independent unloaded recovery geometry, causal inverse command and capture audit.','Independent first-front center geometry, causal inverse command and actual capture audit.')
s+='''
    def verify_center_plan(self,created,q,scene,decay,previous_q,previous):
        attempts=created['attempts'];assert [a['seed'] for a in attempts]==['actual_unloaded','neutral_waist_-0.5','neutral_waist_0.0','neutral_waist_0.5']
        usable=[];axis=np.linalg.eigh(np.cov(self.hand.vertices[scene['side']].T))[1][:,0]
        near(abs(np.array(created['thin_axis_local'])@axis),1.,1e-10)
        for attempt in attempts:
            assert type(attempt['status']) is int and type(attempt['endpoint_accepted']) is bool
            assert type(attempt['iterations']) is int and 0<=attempt['iterations']<=220
            if attempt['endpoint'] is None:
                assert not attempt['endpoint_accepted'] and attempt['nominal_path'] is None;continue
            x=np.asarray(attempt['endpoint']);g,d=self.geometry(x,scene)
            align=abs(d['rotation'][:,2]@d['pose'][:3,:3]@axis)
            minimum=float(min(align**2-.8**2,*list(.002-abs(d['point'][:2])),g['active_above_top_m']-.006,.007-g['active_above_top_m'],g['inactive_lowest_z_m']-.84,g['elbow_gap_m']-.005))
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
        chosen=next(x for x in usable if x['seed']==created['selected_seed'])
        near(created['endpoint'],chosen['endpoint'],0);near(created['waypoints'],chosen['nominal_path']['waypoints'],0)
        pre=created['transport_preflight'];assert pre['accepted'] and pre['predicted_capture_discarded'] is True
        init=pre['initial_context'];assert init['step']==created['step']
        for key,value in [('current',q),('previous_q',previous_q),('previous_command',previous),('decay',decay)]:near(init[key],value,1e-7)
        # Prediction traces are checked structurally here, not reused as actual
        # measurements. A separate causal-preflight replay audit is required.
        ordered=sorted(usable,key=lambda x:x['objective']);trials=pre['trials']
        assert 0<len(trials)<=len(ordered) and [t['seed'] for t in trials]==[x['seed'] for x in ordered[:len(trials)]]
        assert all(not t['predicted_transport_accepted'] for t in trials[:-1]) and trials[-1]['predicted_transport_accepted'] is True
        assert trials[-1]['seed']==created['selected_seed'] and trials[-1]['outcome']=='handover' and trials[-1]['predicted_ticks']<=240
        assert all(not any(k.startswith('captured_') for k in t) for t in trials)
'''
dest.write_text(s)
(W/'FRONT_INITIAL_CENTER_EVENT_AUDIT_PREPARATION.json').write_text(json.dumps(dict(parent=str(source),parent_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),auditor_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),edits=edits,scope='Independent original geometry/command/math retained; all static alternatives checked; actual3-frame readiness/capture and first counter0. Causal preflight trace replay and actual episode wrapper still required.',simulation_started=False,training_ready=False),indent=2))
