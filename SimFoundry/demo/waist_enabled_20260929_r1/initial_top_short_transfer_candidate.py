"""Isolated candidate: retain far/direct-clear checks, lower route-only transfer heuristic to original150mm progress minimum. No original quality gate changed; physics untested."""
import math
from simfoundry.data.tabletop_route_candidates import tabletop_route_candidates


def initial_top_route_candidate(target, obstacle, target_size, obstacle_size,
                                target_quat, obstacle_quat, direction,
                                far_x=.48, min_transfer_m=.15, margin=.02):
    if (not all(math.isfinite(v) for v in (far_x,min_transfer_m,margin))
            or not .36<=far_x<=.62 or not .15<=min_transfer_m<=.35 or margin<.01):
        raise ValueError('Invalid registered direct-top proposal parameters')
    report=tabletop_route_candidates(target,obstacle,target_size,obstacle_size,
        target_quat,obstacle_quat,direction,margin=margin)
    direct=next(r for r in report['candidates'] if r['route']=='direct')
    transfer=direction*(report['goal_y']-target[1]);reasons=[]
    if target[0]<far_x:reasons.append('near target retains existing routing')
    if transfer<=min_transfer_m:reasons.append('short transfer retains existing routing')
    if not direct['object_envelope_eligible']:reasons.append('direct object envelope not clear')
    return dict(proposed=not reasons,reasons=reasons,goal_y=report['goal_y'],
        transfer_m=transfer,far_x=far_x,min_transfer_m=min_transfer_m,
        direct_envelope=direct,scope='Unwired initial top-contact candidate only. No robot reach, hand/arm collision, real force, visual coverage or task success proof.',training_ready=False)
