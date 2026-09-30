"""Explicit expert-search fitness, separate from unchanged demonstration admission."""
import itertools
import numpy as np
from scipy.spatial.transform import Rotation

EXPLORATION_REASONS={
    'target did not finish stably beyond +/-0.20 m with >=0.15 m progress',
    'no sustained active-hand target proximity',
    'target still moving at end',
}

def terminal_search_scores(reports,task_ids,trace,orientation):
    tasks=np.asarray(task_ids);n=len(reports);scores=[];details=[]
    if tasks.shape!=(n,) or set(orientation)!={'box','mailer'}:raise ValueError('Misaligned search audit')
    support=np.ones(n,dtype=bool);upright=np.ones(n,dtype=bool);margins={};tilts={}
    for key,size in [('box',[.14,.09,.045]),('mailer',[.15,.145,.04])]:
        xyz=np.asarray(trace[key]);q=np.asarray(orientation[key])
        if xyz.ndim!=3 or xyz.shape[1:]!=(n,3) or q.shape!=(*xyz.shape[:2],4):raise ValueError('Pose shape mismatch')
        if not np.isfinite(q).all() or not np.isfinite(xyz).all() or np.max(np.abs(np.linalg.norm(q,axis=-1)-1))>1e-4:raise ValueError('Invalid recorded object pose')
        rot=Rotation.from_quat(q.reshape(-1,4)).as_matrix().reshape(*q.shape[:2],3,3)
        corners=np.asarray(list(itertools.product([-1,1],repeat=3)))*np.asarray(size)/2
        points=np.einsum('tnij,kj->tnki',rot,corners)+xyz[:,:,None,:]
        margin=np.stack([points[...,0]-.28,.88-points[...,0],points[...,1]+.75,.75-points[...,1]],axis=-1).min(axis=(0,2,3))
        tilt=np.arccos(np.clip(rot[...,2,2],-1,1)).max(axis=0)
        margins[key]=margin;tilts[key]=tilt;support&=margin>=0;upright&=tilt<=.20
    for i,report in enumerate(reports):
        if tasks[i] not in (0,1):raise ValueError('Push tasks only')
        hard=[x for x in report['reasons'] if x not in EXPLORATION_REASONS]
        safe=bool(support[i] and upright[i] and not hard)
        success=bool(report['passed'] and safe)
        if success:score=10.
        elif not safe:score=-5.
        else:
            # At most1 for incomplete but otherwise safe task progress; never success.
            metrics=report['metrics'];key='box' if tasks[i]==0 else 'mailer';direction=-1 if tasks[i]==0 else 1
            progress=float(np.clip(metrics['target_final_progress_m']/.15,0,1))
            zone=float(np.clip(direction*trace[key][-1,i,1]/.20,0,1))
            hand='right' if tasks[i]==0 else 'left';contact=min(1.,metrics[hand+'_target_proximity_frames']/3.)
            score=.5*progress+.25*zone+.25*contact
        scores.append(score);details.append(dict(search_success=success,original_numeric_passed=bool(report['passed']),score=score,
            support=bool(support[i]),upright=bool(upright[i]),min_margin_m={k:float(v[i]) for k,v in margins.items()},
            max_tilt_rad={k:float(v[i]) for k,v in tilts.items()},original_hard_reasons=hard,training_ready=False))
    return np.asarray(scores,dtype=np.float32),details
