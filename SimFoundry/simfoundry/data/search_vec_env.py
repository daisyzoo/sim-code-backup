"""Finite-horizon privileged search wrapper for the installed RSL-RL interface."""
import torch
from tensordict import TensorDict
from simfoundry.data.search_reward import terminal_search_scores

class SearchVecEnv:
    def __init__(self,episode):
        self.episode=episode;self.num_envs=episode.n;self.num_actions=5;self.device=episode.device
        self.max_episode_length=160;self.episode_length_buf=torch.zeros(self.num_envs,dtype=torch.long,device=self.device)
        self.cfg={'purpose':'privileged expert search; no demonstration admission','gamma':.99,'finite_horizon':160}
        self.completed_batches=0;self.last_terminal=None;self.history=[]

    def get_observations(self):
        return TensorDict({'policy':self.episode.observe()},batch_size=[self.num_envs])

    def potential(self):
        e=self.episode;_,tr=e.snapshot();box=(e.tasks==0)[:,None]
        target=torch.where(box,tr['box'],tr['mailer']);palm=torch.where(box,tr['palm_right'],tr['palm_left'])
        contact=target+torch.tensor([0.,0.,.07],device=self.device)
        distance=torch.linalg.norm(palm-contact,dim=1).clamp(max=1.)
        direction=torch.where(e.tasks==0,-1.,1.);gap=(.20-direction*target[:,1]).clamp(0,.5)
        return -distance-.5*gap

    def step(self,actions):
        previous_phi=self.potential();obs,reports=self.episode.step(actions)
        self.episode_length_buf.fill_(self.episode.t)
        done=reports is not None
        next_phi=torch.zeros_like(previous_phi) if done else self.potential()
        reward=.99*next_phi-previous_phi
        extras={}
        if done:
            e=self.episode;trace={k:torch.stack(v).cpu().numpy() for k,v in e.traces.items()}
            orientation={k:torch.stack(v).cpu().numpy() for k,v in e.orientations.items()}
            score,details=terminal_search_scores(reports,e.tasks.cpu().numpy(),trace,orientation)
            reward+=torch.as_tensor(score,device=self.device)
            self.last_terminal=dict(reports=reports,fitness=details);self.completed_batches+=1
            summary=dict(batch=self.completed_batches,success=sum(x['search_success'] for x in details),numeric_passed=sum(x['passed'] for x in reports),mean_terminal_score=float(score.mean()))
            self.history.append(summary);extras['log']={'/search/success':summary['success']/self.num_envs,'/search/terminal_score':summary['mean_terminal_score']}
            callback=getattr(self,'on_terminal',None)
            if callback is not None:callback(e,self.last_terminal,summary)
            obs=e.reset();self.episode_length_buf.zero_()
        # A160-frame task is terminal, not a timeout: no value bootstrap across reset.
        dones=torch.full((self.num_envs,),done,dtype=torch.long,device=self.device)
        assert torch.isfinite(reward).all()
        return TensorDict({'policy':obs},batch_size=[self.num_envs]),reward,dones,extras
