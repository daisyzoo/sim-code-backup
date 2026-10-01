"""Independent unloaded recovery geometry, causal inverse command and capture audit.
Does not import candidate planning, lifecycle, response or geometry code. Uses
independent URDF hand/elbow reconstruction from existing read-only auditors.
verify() requires caller-bound actual q, previous q/action, final action, object
scene and contact gates. A synthetic fixture pass is not physical validation.
Only selected hand/parcel and elbow geometry at sampled ticks is certified.
"""
from pathlib import Path
import itertools
import numpy as np
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation
from audit_unloaded_wrist_prior_live import HandModel, near
from audit_unloaded_wrist_task_optimality import IndependentElbows
from simfoundry.robots.g1_assets import U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI

class EventAudit:
    def __init__(self,repo,stage):
        repo,stage=Path(repo),Path(stage)
        urdf=repo/'third_party/unitree_ros/robots/g1_description/g1_23dof_rev_1_0_u1_black.urdf'
        self.hand=HandModel(urdf,repo/'assets/robots/g1_hand_support_vertices.json')
        self.elbows=IndependentElbows(stage/'elbow_torso_hulls.json',urdf)
        self.axes={}
        for side,vertices in self.hand.vertices.items():
            axes=np.unique(np.round(ConvexHull(vertices).equations[:,:3],10),axis=0)
            self.axes[side]=axes/np.linalg.norm(axes,axis=1)[:,None]
        self.lo=np.array(U1_JOINT_LIMIT_LO[12:23],float);self.hi=np.array(U1_JOINT_LIMIT_HI[12:23],float)
        self.lo[0]=-.98;self.hi[0]=.98;self.limits=np.r_[.015,np.full(10,.04)]
        self.active=False;self.index=0;self.ticks=0;self.ready=0;self.last=None

    def gap(self,side,pose,position,quat,size):
        boxR=Rotation.from_quat(quat).as_matrix()
        axes=np.vstack([self.axes[side]@pose[:3,:3].T,boxR.T])
        hands=(self.hand.vertices[side]@pose[:3,:3].T+pose[:3,3])@axes.T
        boxes=(np.array(list(itertools.product([-1.,1.],repeat=3)))*np.array(size)/2@boxR.T+position)@axes.T
        return float(np.max(np.r_[boxes.min(0)-hands.max(0),hands.min(0)-boxes.max(0)]))

    def geometry(self,q,scene):
        q=np.asarray(q,float);assert q.shape==(11,) and np.isfinite(q).all()
        side=scene['side'];assert side in ('left','right');other='right' if side=='left' else 'left'
        T=self.hand.fk(q,side);I=self.hand.fk(q,other)
        R=Rotation.from_quat(scene['target_quat']).as_matrix();core=np.array(scene['core_size'])
        points=(self.hand.vertices[side]@T[:3,:3].T+T[:3,3]-scene['target_xyz'])@R
        ix=int(points[:,2].argmin());point=points[ix]
        gaps=dict(active_other=self.gap(side,T,scene['other_xyz'],scene['other_quat'],scene['other_size']),inactive_target=self.gap(other,I,scene['target_xyz'],scene['target_quat'],core),inactive_other=self.gap(other,I,scene['other_xyz'],scene['other_quat'],scene['other_size']))
        elbow=float(min(self.elbows.gap(q)));low=self.lo.copy();high=self.hi.copy();low[0]=-1;high[0]=1
        bounds=bool(np.all(q>=low-2e-7) and np.all(q<=high+2e-7));height=float(point[2]-core[2]/2)
        record=dict(accepted=bool(height>=.004 and min(gaps.values())>=.01 and elbow>0 and bounds),active_above_top_m=height,hand_parcel_gaps_m=gaps,elbow_gap_m=elbow,physical_bounds=bounds,contact_object_local=point.tolist())
        return record,dict(pose=T,inactive=I,rotation=R,core=core,point=point,vertex=self.hand.vertices[side][ix],vertex_index=ix)

    def compare_geometry(self,record,actual):
        assert record['accepted'] is actual['accepted'] and record['physical_bounds'] is actual['physical_bounds']
        for key in ['active_above_top_m','elbow_gap_m','contact_object_local']:near(record[key],actual[key],2e-9)
        assert set(record['hand_parcel_gaps_m'])==set(actual['hand_parcel_gaps_m'])
        for key,value in actual['hand_parcel_gaps_m'].items():near(record['hand_parcel_gaps_m'][key],value,2e-9)

    def verify(self,event,*,step,current,previous_q,previous_command,final_command,scene,decay,selected,parent_mode,recontacts,guard_stop,observed_load_n,filtered_load_n):
        assert event['kind'] in ('command','handover')
        c=event['context'];p=event['proposal'];q,qp,previous,command,a=[np.asarray(v,float) for v in [current,previous_q,previous_command,final_command,decay]]
        for v in [q,qp,previous,command,a]:assert v.shape==(11,) and np.isfinite(v).all()
        assert np.all(a>=0) and np.all(a<=.95)
        for key,value in dict(step=step,selected=selected,parent_mode=parent_mode,recontacts=recontacts,guard_stop=guard_stop,observed_load_n=observed_load_n,filtered_load_n=filtered_load_n).items():assert c[key]==value,(step,key)
        assert selected is True and parent_mode in ('top_cross','top_descend') and recontacts>=1 and guard_stop is False and observed_load_n==0 and 0<=filtered_load_n<=.05
        assert c['scene']==scene
        for key,value in [('current',q),('previous_q',qp),('previous_command',previous)]:near(c[key],value,1e-7);near(p[key],value,1e-7)
        near(p['decay'],a,0)
        actual,g=self.geometry(q,scene);assert actual['accepted']
        near(c['observed_hand_pose'],g['pose'],1e-4);near(c['observed_inactive_hand_pose'],g['inactive'],1e-4)
        created=event['planning']
        if not self.active:
            assert created is not None and created['accepted'] is True and created['step']==step and created['scene']==scene
            assert self.hand.minz(q,scene['side'])>=.84
            near(created['start'],q,1e-7);endpoint=np.array(created['endpoint']);near(endpoint,created['best']['candidate'],0)
            assert np.all(endpoint>=self.lo-2e-7) and np.all(endpoint<=self.hi+2e-7)
            endpoint_geometry,eg=self.geometry(endpoint,scene)
            assert np.min(eg['core'][:2]/2-abs(eg['point'][:2]))>=.012-2e-7
            assert .006-2e-7<=endpoint_geometry['active_above_top_m']<=.007+2e-7
            assert min(endpoint_geometry['hand_parcel_gaps_m'].values())>=.01-2e-7 and endpoint_geometry['elbow_gap_m']>=.005-2e-7
            inactive='right' if scene['side']=='left' else 'left';assert self.hand.minz(endpoint,inactive)>=.84-2e-7
            count=max(1,int(np.ceil(max(abs(endpoint-q)/(self.limits*.25)))))
            expected=np.array([np.clip(q+(endpoint-q)*i/count,self.lo,self.hi) for i in range(1,count+1)])
            near(created['waypoints'],expected,1e-10)
            self.waypoints=expected;self.endpoint=endpoint;self.scene=scene;self.recontacts=recontacts;self.active=True;self.index=0;self.ticks=0;self.ready=0
        else:
            assert created is None and recontacts==self.recontacts and self.last is not None and step==self.last['step']+1
            near(qp,self.last['q'],1e-7);near(previous,self.last['command'],0)
        for key in ['target','other']:
            assert np.linalg.norm(np.array(scene[key+'_xyz'])-self.scene[key+'_xyz'])<=.002
            assert (Rotation.from_quat(scene[key+'_quat'])*Rotation.from_quat(self.scene[key+'_quat']).inv()).magnitude()<=.02
        assert scene['core_size']==self.scene['core_size'] and scene['other_size']==self.scene['other_size']
        assert self.ticks<240
        if max(abs(q-self.waypoints[self.index]))<=.003 and self.index<len(self.waypoints)-1:self.index+=1
        waypoint=self.waypoints[self.index];near(p['waypoint'],waypoint,1e-10);assert event['waypoint_index']==self.index
        bias=q-previous-a*(qp-previous);request=(waypoint-a*q-bias)/(1-a)
        low=np.maximum.reduce([self.lo,q-self.limits,previous-.055]);high=np.minimum.reduce([self.hi,q+self.limits,previous+.055]);assert np.all(low<=high)
        expected=np.clip(request,low,high).astype(np.float32);predicted=(1-a)*expected+a*q+bias
        for key,value in [('causal_bias',bias),('requested_command',request),('predicted_q',predicted)]:near(p[key],value,1e-10)
        near(p['candidate_command'],expected,0);near(event['command'],expected,0);near(command,expected,0)
        assert p['applied'] is True and p['reason']=='verified_unloaded_command'
        gaps=self.elbows.gap(command)
        assert np.all(command>=self.lo-2e-7) and np.all(command<=self.hi+2e-7) and np.all(abs(command-q)<=self.limits+2e-7) and max(abs(command-previous))<=.0550002 and min(gaps)>=.005-2e-7
        check=p['command_check'];assert check['accepted'] is True and check['first'] is False
        assert check['checks']==dict(joint_bounds=True,measured_step=True,previous_slew=True,nominal_margin=True,first_zero=True)
        near(check['command'],command,0);near(check['current'],q,1e-7);near(check['previous'],previous,0);near(check['gaps_m'],gaps,2e-9)
        for key,value in [('nominal_scene',command),('predicted_scene',predicted)]:
            verified,_=self.geometry(value,scene);assert verified['accepted'];self.compare_geometry(p[key],verified)
        close=max(abs(q-self.endpoint))<=.003
        ready=bool(close and min(g['core'][:2]/2-abs(g['point'][:2]))>=.01 and .004<=actual['active_above_top_m']<=.01 and np.all(q>=self.lo-2e-7) and np.all(q<=self.hi+2e-7))
        self.ready=self.ready+1 if ready else 0;self.ticks+=1
        assert event['measured_ready_count']==self.ready and event['ticks']==self.ticks
        assert (event['kind']=='handover')==(self.ready>=3)
        if event['kind']=='handover':
            # Capture uses actual measured pose, independently checked against FK.
            pose=np.array(c['observed_hand_pose']);inactive_pose=np.array(c['observed_inactive_hand_pose']);verts=self.hand.vertices[scene['side']]
            points=(verts@pose[:3,:3].T+pose[:3,3]-scene['target_xyz'])@g['rotation'];vertex=verts[int(points[:,2].argmin())]
            world=pose[:3,3]+pose[:3,:3]@vertex;local=g['rotation'].T@(world-scene['target_xyz'])
            assert min(g['core'][:2]/2-abs(local[:2]))>=.01-1e-9
            near(event['captured_center_local'],vertex,1e-10);near(event['selected_surface_local_xy'],local[:2],1e-9)
            near(event['captured_normal_local_up'],pose[2,:3],1e-10)
            near(event['captured_inactive_anchor_world'],inactive_pose[:3,3]+inactive_pose[:3,:3]@np.array([.20,0,.007]),1e-10)
            near(event['observed_support_xyz'],world,1e-9)
            for key in ['center_local','reference_local','lowest_vertex_local']:near(event['reference'][key],vertex,1e-9)
            near(event['reference']['world_normal'],g['rotation'][:,2],1e-10)
            self.active=False
        self.last=dict(step=step,q=q.copy(),command=command.copy())
        return dict(step=step,kind=event['kind'],independent_geometry_passed=True,independent_command_passed=True,measured_ready_count=self.ready)
