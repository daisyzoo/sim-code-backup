"""Training-query phase labels from original raw states/actions and expert log.

No quality approval, cropping, relabeling of tasks, or changes to action chunks.
A release command is active until its withdrawal has actually settled.
"""
from collections import Counter
import numpy as np
RELEASE_MODES={'goal_release','top_release','bypass_release','done','hold'}

def episode_query_phases(task_id,q,action,control,*,prefix_frames=3,step_rad=.001,endpoint_rad=.01):
    q=np.asarray(q,dtype=float);action=np.asarray(action,dtype=float)
    if (q.ndim!=2 or q.shape!=action.shape or q.shape[1]!=23 or len(q)<50
            or not np.isfinite(q).all() or not np.isfinite(action).all()):
        raise ValueError('Invalid complete raw23D state/action table')
    if (type(prefix_frames) is not int or not 1<=prefix_frames<=20
            or not np.isfinite([step_rad,endpoint_rad]).all()
            or not 0<step_rad<=endpoint_rad<=.02):
        raise ValueError('Invalid declared phase thresholds')
    n=len(q)
    if len(control)!=n or [r.get('step') for r in control]!=list(range(n)):
        raise ValueError('Expert control log must align exactly with every raw frame')
    modes=[r['mode'] for r in control]
    if task_id=='wait_no_package':labels=['wait']*n;terminal=None
    elif task_id in {'push_box_to_bin','nudge_mailer_to_bin'}:
        if n<120:raise ValueError('Incomplete pushing episode')
        upper_q=q[:,12:23];upper_a=action[:,12:23]
        steps=np.maximum(np.max(np.abs(np.diff(upper_q,axis=0)),axis=1),np.max(np.abs(np.diff(upper_a,axis=0)),axis=1))
        # Incoming movement is included: the first settled query cannot hide a
        # just-completed large lift. Endpoint condition rejects long slow drift.
        small_step=np.r_[False,steps<=step_rad]
        near_end=np.maximum(np.max(abs(upper_q-upper_q[-1]),axis=1),np.max(abs(upper_a-upper_a[-1]),axis=1))<=endpoint_rad
        settled=small_step & near_end & np.array([m in RELEASE_MODES for m in modes])
        terminal=n
        while terminal>prefix_frames and settled[terminal-1]:terminal-=1
        if n-terminal<10 or terminal<=prefix_frames:raise ValueError('No distinct active phase and settled ten-frame terminal suffix')
        labels=['start']*prefix_frames+['active']*(terminal-prefix_frames)+['terminal']*(n-terminal)
    else:raise ValueError('Unregistered sorting task')
    runs=[]
    for i,label in enumerate(labels):
        if not runs or runs[-1]['phase']!=label:runs.append(dict(phase=label,start=i,end=i+1))
        else:runs[-1]['end']=i+1
    return dict(frames=n,runs=runs,counts=dict(Counter(labels)),terminal_start=terminal,
                definition=dict(prefix_frames=prefix_frames,max_joint_step_rad=step_rad,max_distance_from_final_joint_rad=endpoint_rad,terminal_min_frames=10,release_modes=sorted(RELEASE_MODES)),
                scope='Query-index labels; withdrawal/recovery remains active until a settled terminal suffix. Full original frames/actions retained. Labels do not certify original quality or training readiness.')


def expand_query_phases(record):
    n=record['frames'];labels=[]
    if type(n) is not int or n<=0:raise ValueError('Invalid phase frame count')
    for run in record['runs']:
        if (type(run['start']) is not int or type(run['end']) is not int or run['start']!=len(labels)
                or not run['start']<run['end']<=n or run['phase'] not in {'start','active','terminal','wait'}):
            raise ValueError('Gapped/overlapping/invalid phase run')
        labels.extend([run['phase']]*(run['end']-run['start']))
    if len(labels)!=n or dict(Counter(labels))!=record['counts']:raise ValueError('Phase coverage/count mismatch')
    return labels
