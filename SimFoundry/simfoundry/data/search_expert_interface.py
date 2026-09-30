"""Bounded privileged expert-search actions and original terminal audit.

This module is not used by the VLA policy server or h10 model evaluation.
"""
import numpy as np
import torch
from simfoundry.data.paired_sorting import audit_rollout

TASKS=('push_box_to_bin','nudge_mailer_to_bin','wait_no_package')

def expert_absolute_targets(raw_action, previous, task_ids, first_frame, default, lower, upper):
    """Five active-arm increments; all other targets fixed at default (upper zero)."""
    n=len(previous)
    if raw_action.shape!=(n,5) or previous.shape!=(n,23) or task_ids.shape!=(n,) or first_frame.shape!=(n,):
        raise ValueError('Invalid expert batch shapes')
    if not torch.isfinite(raw_action).all() or not torch.isfinite(previous).all():
        raise ValueError('Nonfinite expert action or previous target')
    if bool(((task_ids<0)|(task_ids>2)).any()) or task_ids.dtype not in (torch.int32,torch.int64):
        raise ValueError('Unknown task index')
    if float(default[12:].abs().max())>=1e-6:
        raise ValueError('Expert default upper body must be zero')
    target=default.unsqueeze(0).expand(n,-1).clone()
    for task,start in [(0,18),(1,13)]:
        selected=(task_ids==task)&~first_frame
        candidate=previous[selected,start:start+5]+raw_action[selected].clamp(-1,1)*.055
        target[selected,start:start+5]=torch.maximum(torch.minimum(candidate,upper[start:start+5]),lower[start:start+5])
    nonfirst=~first_frame
    if bool(((target[nonfirst]-previous[nonfirst]).abs()>.055001).any()):
        raise ValueError('Task changed without reset or inconsistent previous targets')
    return target

def terminal_batch_audit(task_ids,q,action,trace):
    """Time-major arrays; call the unchanged reference audit per complete episode.

    This is a numeric reward/diagnostic result, never training admission. RGB,
    reset provenance, orientation/support and actual visual review remain required.
    """
    def array(x):
        return x.detach().cpu().numpy() if isinstance(x,torch.Tensor) else np.asarray(x)
    q,action=array(q),array(action);trace={k:array(v) for k,v in trace.items()}
    tasks=array(task_ids)
    if q.ndim!=3 or q.shape!=action.shape or q.shape[2]!=23 or tasks.shape!=(q.shape[1],):
        raise ValueError('Expected time x environment x23 trajectories')
    if not np.issubdtype(tasks.dtype,np.integer) or np.any((tasks<0)|(tasks>=len(TASKS))):
        raise ValueError('Unknown task index')
    if any(v.shape!=(q.shape[0],q.shape[1],3) for v in trace.values()) or set(trace)!={'box','mailer','palm_left','palm_right'}:
        raise ValueError('Missing or misaligned trajectory traces')
    return [audit_rollout(TASKS[int(task)],q[:,i],action[:,i],{k:v[:,i] for k,v in trace.items()}) for i,task in enumerate(tasks)]
