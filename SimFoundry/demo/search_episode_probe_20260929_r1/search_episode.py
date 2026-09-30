"""Synchronized physical search episodes; privileged observations, no rewards yet."""
import torch
from isaaclab.utils.math import quat_apply
from simfoundry.robots.g1_assets import u1_sorting_default_qpos_np,U1_JOINT_LIMIT_LO,U1_JOINT_LIMIT_HI,G1_U1_23DOF_JOINT_NAMES
from simfoundry.data.sorting_quality import resolve_hand_indices,PALM_OFFSET
from simfoundry.data.search_expert_interface import expert_absolute_targets,terminal_batch_audit
from simfoundry.data.vector_sorting_reset import reset_paired_layouts

def tensor(value):
    return value.torch if hasattr(value,'torch') else value

class SearchEpisode:
    def __init__(self,env,layouts,task_ids):
        self.env=env;self.layouts=layouts;self.device=env.device;self.n=env.num_envs
        self.tasks=torch.as_tensor(task_ids,dtype=torch.long,device=self.device)
        if len(layouts)!=self.n or self.tasks.shape!=(self.n,) or bool(((self.tasks<0)|(self.tasks>1)).any()):raise ValueError('Paired push search requires aligned layouts and two task IDs')
        self.robot=env.scene['robot'];self.ids=[self.robot.joint_names.index(n) for n in G1_U1_23DOF_JOINT_NAMES]
        self.hands=resolve_hand_indices(self.robot);self.upper=[*range(13,23),12]
        self.default=torch.tensor(u1_sorting_default_qpos_np(zero_upper_body=True),device=self.device)
        self.lower=torch.tensor(U1_JOINT_LIMIT_LO,device=self.device);self.upper_limits=torch.tensor(U1_JOINT_LIMIT_HI,device=self.device)
        self.reset()

    def snapshot(self):
        origin=self.env.scene.env_origins;trace={}
        for key,name in [('box','parcel_box'),('mailer','mailer')]:trace[key]=tensor(self.env.scene[name].data.root_pos_w)-origin
        for side,idx in self.hands.items():
            pos=tensor(self.robot.data.body_pos_w)[:,idx];quat=tensor(self.robot.data.body_quat_w)[:,idx]
            offset=torch.tensor(PALM_OFFSET,device=self.device).expand(self.n,-1)
            trace['palm_'+side]=pos+quat_apply(quat,offset)-origin
        return tensor(self.robot.data.joint_pos)[:,self.ids],trace

    def reset(self):
        self.requested=reset_paired_layouts(self.env,list(range(self.n)),self.layouts)
        self.previous=self.default.expand(self.n,-1).clone();self.t=0;self.qs=[];self.actions=[];self.traces={k:[] for k in ['box','mailer','palm_left','palm_right']}
        q,tr=self.snapshot();assert float(q[:,12:].abs().max())<1e-4
        self.initial=torch.cat([tr['box'],tr['mailer']],dim=1).clone()
        return self.observe()

    def observe(self):
        q,tr=self.snapshot();qd=tensor(self.robot.data.joint_vel)[:,self.ids]
        parts=[q[:,self.upper],qd[:,self.upper],self.previous[:,self.upper]]
        for name in ['parcel_box','mailer']:
            asset=self.env.scene[name];parts.extend([tensor(asset.data.root_pos_w)-self.env.scene.env_origins,tensor(asset.data.root_quat_w)])
        for name in ['parcel_box','mailer']:parts.append(tensor(self.env.scene[name].data.root_com_vel_w))
        parts.extend([self.initial,tr['palm_left'],tr['palm_right'],torch.nn.functional.one_hot(self.tasks,2).float(),torch.full((self.n,1),self.t/160,device=self.device)])
        obs=torch.cat(parts,dim=1);assert obs.shape==(self.n,74) and torch.isfinite(obs).all()
        return obs

    def step(self,raw):
        first=torch.full((self.n,),self.t==0,dtype=torch.bool,device=self.device)
        target=expert_absolute_targets(raw,self.previous,self.tasks,first,self.default,self.lower,self.upper_limits)
        return self.step_absolute(target)

    def step_absolute(self,target):
        """Diagnostic replay may supply historical both-arm targets; never for PPO."""
        if self.t>=160:raise RuntimeError('Reset required after complete episode')
        if target.shape!=(self.n,23) or not torch.isfinite(target).all():raise ValueError('Invalid replay action')
        assert float(target[:,12].abs().max())<1e-6
        assert bool((target>=self.lower-1e-6).all() and (target<=self.upper_limits+1e-6).all())
        assert float((target-self.previous).abs().max())<=.080001
        if self.t==0:assert float(target[:,12:].abs().max())<1e-4
        q,tr=self.snapshot();self.qs.append(q.clone());self.actions.append(target.clone())
        for key,value in tr.items():self.traces[key].append(value.clone())
        _,_,terminated,truncated,_=self.env.step(target-self.default)
        if bool(terminated.any() or truncated.any()):raise RuntimeError('Unexpected native reset within search episode')
        self.previous=target.clone();self.t+=1
        reports=None
        if self.t==160:reports=terminal_batch_audit(self.tasks,torch.stack(self.qs),torch.stack(self.actions),{k:torch.stack(v) for k,v in self.traces.items()})
        return self.observe(),reports
