"""Independent bounded causal-preflight replay, no candidate imports.
Synthetic response may screen plans but never supplies physical handover proof.
"""
import numpy as np
from audit_front_initial_center_events import EventAudit
from audit_unloaded_wrist_prior_live import near


class SelectionAudit(EventAudit):
    def predict_trial(self, candidate, scene, context):
        q,qp,previous,a=[np.asarray(context[k],float) for k in ('current','previous_q','previous_command','decay')]
        assert all(v.shape==(11,) and np.isfinite(v).all() for v in [q,qp,previous,a])
        assert np.all(a>=0.) and np.all(a<=.95)
        waypoints=np.asarray(candidate['nominal_path']['waypoints']);endpoint=np.asarray(candidate['endpoint'])
        index=0;ticks=0;ready=0;events=[]
        axis=np.linalg.eigh(np.cov(self.hand.vertices[scene['side']].T))[1][:,0]
        for _ in range(241):
            kind='command';reason=None
            if ticks>=240:
                kind='stop';reason='initial_front_path_budget_exhausted'
            else:
                if max(abs(q-waypoints[index]))<=.003 and index<len(waypoints)-1:index+=1
                waypoint=waypoints[index]
                measured,details=self.geometry(q,scene)
                low=np.maximum.reduce([self.lo,q-self.limits,previous-.055]);high=np.minimum.reduce([self.hi,q+self.limits,previous+.055])
                if np.any(waypoint<self.lo-2e-7) or np.any(waypoint>self.hi+2e-7) or not measured['accepted'] or np.any(low>high):
                    kind='stop';reason='no_verified_initial_front_command'
                else:
                    bias=q-previous-a*(qp-previous);request=(waypoint-a*q-bias)/(1-a)
                    command=np.clip(request,low,high).astype(np.float32);pred=(1-a)*command+a*q+bias
                    nominal,_=self.geometry(command,scene);predicted,_=self.geometry(pred,scene)
                    valid=bool(np.all(command>=self.lo-2e-7) and np.all(command<=self.hi+2e-7) and np.all(abs(command-q)<=self.limits+2e-7) and max(abs(command-previous))<=.0550002 and nominal['accepted'] and predicted['accepted'])
                    if not valid:
                        kind='stop';reason='no_verified_initial_front_command'
                    else:
                        ticks+=1;point=details['point'];alignment=abs(details['rotation'][:,2]@details['pose'][:3,:3]@axis)
                        physical_ready=bool(max(abs(q-endpoint))<=.003 and max(abs(point[:2]))<=.002+2e-7 and min(details['core'][:2]/2-abs(point[:2]))>=.01 and .004<=measured['active_above_top_m']<=.01 and alignment>=.8-2e-7 and np.all(q>=self.lo-2e-7) and np.all(q<=self.hi+2e-7))
                        ready=ready+1 if physical_ready else 0
                        if ready>=3:kind='handover'
            events.append(dict(kind=kind,ticks=ticks,waypoint_index=index,measured_ready_count=ready,reason=reason))
            if kind!='command':break
            qp,q,previous=q,pred,command.astype(float)
        return dict(events=events,outcome=kind,reason=reason,predicted_ticks=ticks,predicted_transport_accepted=kind=='handover')

    def verify_selection(self, planning, *, current, previous_q, previous_command, decay, scene, step):
        assert planning['scene']==scene and planning['step']==step
        near(planning['start'],current,1e-7)
        pre=planning['transport_preflight'];assert pre['predicted_capture_discarded'] is True
        ctx=pre['initial_context'];assert ctx['step']==step
        for k,v in [('current',current),('previous_q',previous_q),('previous_command',previous_command),('decay',decay)]:near(ctx[k],v,1e-7)
        valid=sorted([a for a in planning['attempts'] if a['endpoint_accepted'] and a['nominal_path']['accepted']],key=lambda x:x['objective'])
        trials=pre['trials'];assert 0<len(trials)<=len(valid)
        selected=None
        for index,stored in enumerate(trials):
            candidate=valid[index];assert stored['seed']==candidate['seed']
            assert stored['nominal_nodes']==len(candidate['nominal_path']['waypoints']);near(stored['objective'],candidate['objective'],0)
            actual=self.predict_trial(candidate,scene,ctx)
            for key,value in actual.items():assert stored[key]==value,(stored['seed'],key)
            if actual['predicted_transport_accepted']:
                assert index==len(trials)-1;selected=candidate['seed'];break
        if selected is None:
            assert len(trials)==len(valid) and planning['accepted'] is False and pre['accepted'] is False
            assert planning['reason']=='no_original_budget_causal_transport_candidate'
        else:
            assert planning['accepted'] is True and pre['accepted'] is True
            assert planning['selected_seed']==pre['selected_seed']==selected
        return dict(passed=True,trials=len(trials),selected=selected,predicted_only=True,training_ready=False)
