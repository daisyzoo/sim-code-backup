"""Independent actual entry-lift events and shared recovery-budget audit.
Uses independent URDF geometry and algebra; imports no candidate lift/controller.
Original center/minimum-motion events retain their full existing event audit.
"""
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from audit_slow_drag_plan import PlanAudit
from audit_box_center_events import EventAudit as OriginalAudit
from audit_unloaded_wrist_prior_live import near

class LiftAudit:
    def __init__(self,repo,stage):
        self.geometry_audit=PlanAudit(repo,stage);self.active=False;self.last=None;self.ticks=0;self.index=0;self.ready=0

    def verify(self,event,*,step,current,previous_q,previous_command,final_command,scene,decay,selected,parent_mode,recontacts,guard_stop,observed_load_n,filtered_load_n):
        a=self.geometry_audit;p=event['proposal'];ctx=event['context'];q,qp,prev,u,d=[np.asarray(x,float) for x in [current,previous_q,previous_command,final_command,decay]]
        assert scene['side']=='right' and event['kind']=='command' and event['entry_lift_phase'] in ('lift_command','lift_ready')
        for x in [q,qp,prev,u,d]:assert x.shape==(11,) and np.isfinite(x).all()
        assert np.all(d>=0) and np.all(d<=.95)
        assert type(step) is int and type(recontacts) is int and selected is True and guard_stop is False and recontacts>0 and parent_mode in ('top_cross','top_descend') and observed_load_n==0 and 0<=filtered_load_n<=.05
        for name,value in dict(step=step,recontacts=recontacts,selected=selected,guard_stop=guard_stop,parent_mode=parent_mode,observed_load_n=observed_load_n,filtered_load_n=filtered_load_n,scene=scene).items():assert ctx[name]==value
        for name,value in [('current',q),('previous_q',qp),('previous_command',prev)]:near(ctx[name],value,1e-7);near(p[name],value,1e-7)
        near(p['decay'],d,0);actual,geom=a.geometry(q,scene);assert actual['accepted'];near(ctx['observed_hand_pose'],geom['pose'],1e-4);near(ctx['observed_inactive_hand_pose'],geom['inactive'],1e-4)
        created=event['planning']
        if not self.active:
            assert created is not None and created['accepted'] is True and created['step']==step and created['scene']==scene
            near(created['start'],q,1e-7);assert a.hand.minz(q,'right')<.84
            height=.845-float(scene['target_xyz'][2])-float(scene['core_size'][2])/2
            a.lift(created['lift'],q,height,scene);assert created['lift']['accepted'] is True
            end=np.array(created['lift']['candidate']);a.checked_path(created['path'],[q,end],scene);assert created['path']['accepted'] is True
            endz=a.hand.minz(end,'right');assert endz>=.84;near(endz,created['endpoint_lowest_world_z_m'],1e-8)
            self.endpoint=end;self.waypoints=np.array(created['path']['waypoints']);self.scene=scene;self.recontacts=recontacts;self.active=True;self.ticks=0;self.index=0;self.ready=0;self.last=None
        else:
            assert created is None and self.last is not None and step==self.last['step']+1 and recontacts==self.recontacts
            near(qp,self.last['q'],1e-7);near(prev,self.last['command'],0)
        for key in ['target','other']:
            assert np.linalg.norm(np.array(scene[key+'_xyz'])-self.scene[key+'_xyz'])<=.002
            assert (Rotation.from_quat(scene[key+'_quat'])*Rotation.from_quat(self.scene[key+'_quat']).inv()).magnitude()<=.02
        assert scene['core_size']==self.scene['core_size'] and scene['other_size']==self.scene['other_size'] and self.ticks<40
        if np.max(abs(q-self.waypoints[self.index]))<=.003 and self.index<len(self.waypoints)-1:self.index+=1
        target=self.waypoints[self.index];assert event['waypoint_index']==self.index;near(p['waypoint'],target,1e-10)
        bias=q-prev-d*(qp-prev);request=(target-d*q-bias)/(1-d);lo=np.maximum.reduce([a.lo,q-a.limits,prev-.055]);hi=np.minimum.reduce([a.hi,q+a.limits,prev+.055]);assert np.all(lo<=hi);expected=np.clip(request,lo,hi).astype(np.float32);predicted=(1-d)*expected+d*q+bias
        for key,value in [('causal_bias',bias),('requested_command',request),('predicted_q',predicted)]:near(p[key],value,1e-10)
        near(p['candidate_command'],expected,0);near(event['command'],expected,0);near(u,expected,0);assert p['applied'] is True and p['reason']=='verified_unloaded_command'
        gaps=a.elbows.gap(u);assert np.all(u>=a.lo-2e-7) and np.all(u<=a.hi+2e-7) and np.all(abs(u-q)<=a.limits+2e-7) and max(abs(u-prev))<=.0550002 and min(gaps)>=.005-2e-7
        check=p['command_check'];assert check['accepted'] is True and check['first'] is False and check['checks']==dict(joint_bounds=True,measured_step=True,previous_slew=True,nominal_margin=True,first_zero=True)
        near(check['command'],u,0);near(check['current'],q,1e-7);near(check['previous'],prev,0);near(check['gaps_m'],gaps,2e-9)
        for key,value in [('nominal_scene',u),('predicted_scene',predicted)]:
            g,_=a.geometry(value,scene);assert g['accepted'];a.compare_geometry(p[key],g)
        T=np.asarray(ctx['observed_hand_pose'],float);z=float(np.min((a.hand.vertices['right']@T[:3,:3].T+T[:3,3])[:,2]));near(z,event['measured_lowest_world_z_m'],1e-8)
        ready=bool(z>=.84 and np.max(abs(q-self.endpoint))<=.003 and np.all(q>=a.lo-2e-7) and np.all(q<=a.hi+2e-7))
        self.ready=self.ready+1 if ready else 0;self.ticks+=1
        assert event['ticks']==self.ticks and event['measured_ready_count']==self.ready and (event['entry_lift_phase']=='lift_ready')==(self.ready>=3)
        assert not any(n in event for n in ['captured_center_local','captured_normal_local_up','captured_inactive_anchor_world','reference'])
        if self.ready>=3:self.active=False
        self.last=dict(step=step,q=q.copy(),command=u.copy())
        return dict(step=step,kind='command',entry_lift_phase=event['entry_lift_phase'],independent_geometry_passed=True,independent_command_passed=True,measured_ready_count=self.ready)

class EventAudit:
    def __init__(self,repo,stage):
        self.original=OriginalAudit(repo,stage);self.lift=LiftAudit(repo,stage);self.hand=self.original.hand;self.recontacts=None;self.total=0;self.last=None;self.awaiting_original=False

    @property
    def active(self):return self.original.active or self.lift.active or self.awaiting_original

    def geometry(self,*args):return self.original.geometry(*args)

    def verify_preference(self,*args,**kwargs):return self.original.verify_preference(*args,**kwargs)

    def verify(self,event,**inputs):
        side=inputs['scene']['side'];n=inputs['recontacts']
        if side=='left':
            assert 'entry_lift_phase' not in event and 'recovery_total_ticks' not in event
            return self.original.verify(event,**inputs)
        if self.recontacts!=n:
            assert not self.active
            self.recontacts=n;self.total=0;self.last=None
        if self.last is not None and self.active:
            assert inputs['step']==self.last['step']+1;near(inputs['previous_q'],self.last['q'],1e-7);near(inputs['previous_command'],self.last['u'],0)
        assert self.total<240
        if 'entry_lift_phase' in event:
            assert not self.original.active and not self.awaiting_original
            result=self.lift.verify(event,**inputs)
            if event['entry_lift_phase']=='lift_ready':self.awaiting_original=True
        else:
            assert not self.lift.active
            result=self.original.verify(event,**inputs);self.awaiting_original=False
        self.total+=1;assert event['recovery_total_ticks']==self.total
        self.last=dict(step=inputs['step'],q=np.array(inputs['current']),u=np.array(inputs['final_command']))
        return dict(result,recovery_total_ticks=self.total)
