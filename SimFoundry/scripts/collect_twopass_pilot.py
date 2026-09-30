#!/usr/bin/env python3
"""Fresh two-pass paired pilot requiring separately verified feasibility evidence."""
from __future__ import annotations
import argparse
import json
import hashlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from isaaclab.app import AppLauncher
parser = argparse.ArgumentParser()
parser.add_argument('--out-dir', required=True)
parser.add_argument('--twopass-pilot-contract', type=Path, required=True)
parser.add_argument('--role', choices=('diagnostic', 'pilot'), default='diagnostic')
parser.add_argument('--layout-start', type=int, default=0)
parser.add_argument('--spatial-pilot-contract', type=Path, help='Exact reviewed geometry/settings for fresh pilot only; diagnostic files remain excluded.')
parser.add_argument('--diagnostic-layout-json', help='Explicit reviewed geometry proposal; diagnostic only, never training-ready.')
parser.add_argument('--layouts', type=int, default=1)
parser.add_argument('--wait-episodes', type=int, default=0)
parser.add_argument('--wait-layout-start', type=int, default=10000)
parser.add_argument('--steps', type=int, default=160, help='Push frames, including final stable hold [15 Hz].')
parser.add_argument('--idle', action='store_true')
parser.add_argument('--policy-port', type=int, default=0, help='Nonzero selects PI0.5 evaluation, never demonstration collection.')
parser.add_argument('--policy-host', default='127.0.0.1')
parser.add_argument('--eval-seed', type=int, default=0)
parser.add_argument('--policy-max-action-step', type=float, default=0.,
                    help='Diagnostic model-target slew cap [rad/step], 0 disables; raw predictions are retained.')
parser.add_argument('--horizon', type=int, default=10)
parser.add_argument('--prompt-variant', choices=('short', 'unified_ablation'), default='short')
parser.add_argument('--wait-force-n', type=float, default=0., help='Diagnostic only: world-X physical force pulse on left hand, frames20-25 [N].')
parser.add_argument('--wait-force-start', type=int, default=20, help='Physical wait-pulse start, 5 or20.')
parser.add_argument('--recovery-pilot-contract', type=Path, help='Reviewed exact settings permit fresh forced pilot collection; diagnostics remain quarantined.')
parser.add_argument('--push-force-n', type=float, default=0., help='Diagnostic active-hand world-X force at frames5-10 during lift, no parcel force.')
parser.add_argument('--push-force-axis', choices=('x','negative_x','z'), default='x', help='Diagnostic force direction; pilot contracts remain positiveX only.')
parser.add_argument('--push-force-start', type=int, default=5, help='Diagnostic pulse start; pilot contracts remain frame5 only.')
parser.add_argument('--wait-force-side', choices=('left','right','both'), default='left', help='Diagnostic physical force target; each selected hand receives wait-force-n.')
parser.add_argument('--settled-contact', action='store_true', help='Diagnostic expert: settle near contact height before sweeping.')
parser.add_argument('--expert-staging-z', type=float, default=1.0, help='Diagnostic approach palm height [m]; historical default1.0.')
parser.add_argument('--expert-front-reposition', type=float, default=0., help='Diagnostic component-only frontward palm travel for near opposite-side targets.')
parser.add_argument('--expert-front-reposition-hold-yz', action='store_true', help='Diagnostic: retain measured palm Y/Z during retreat and hold.')
parser.add_argument('--expert-front-reposition-measured-start', action='store_true', help='Diagnostic: anchor retreat X at measured palm on phase entry.')
parser.add_argument('--bounded-servo-memory', action='store_true', help='Diagnostic bounded accumulated IK targets; max .10rad lead over measured q.')
parser.add_argument('--finger-heading-weight', type=float, default=0., help='Diagnostic soft world-X finger heading constraint; 0 disables.')
parser.add_argument('--expert-max-contact-x', type=float, default=0., help='Diagnostic cap on palm contact X, 0 keeps parcel-center X.')
parser.add_argument('--expert-contact-confirmed-sweep', action='store_true', help='Diagnostic: after measurable force transfer, sweep from measured contact pose.')
parser.add_argument('--expert-object-feedback-lead', type=float, default=0., help='Diagnostic far-object closed-loop Y lead; 0 disables, m.')
parser.add_argument('--expert-far-contact-offset', type=float, default=0., help='Diagnostic distance rule: override lateral offset for targets X>=.48m, 0 disables.')
parser.add_argument('--expert-contact-offset', type=float, default=-.13, help='Diagnostic signed pre-contact lateral offset [m].')
parser.add_argument('--expert-crossed-contact-offset', type=float, default=0., help='Diagnostic opposite-side target approach offset; zero retains distance rule.')
parser.add_argument('--expert-exit-y', type=float, default=.30, help='Diagnostic absolute lateral palm endpoint [m]; default unchanged.')
parser.add_argument('--recover-contact-height', action='store_true', help='Diagnostic expert: pause lateral sweep while palm is too high, then resume after physical height recovery.')
parser.add_argument('--trace-contacts', action='store_true', help='Diagnostic Newton contact pairs.')
parser.add_argument('--trace-solved-contact-forces', action='store_true', help='Diagnostic read-only last-tick solved MuJoCo forces; no solver refresh.')
parser.add_argument('--trace-episode-contacts', action='store_true', help='Diagnostic read-only last-physics-tick contact buffer after each control action; no force measurement.')
parser.add_argument('--newton-contacts', action='store_true', help='Diagnostic collision-pipeline comparison.')
parser.add_argument('--layout-x-offset', type=float, default=0., help='Diagnostic reachability offset [m].')
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
if args.role!='pilot' or args.layouts!=1 or args.steps!=320 or args.policy_port or args.wait_episodes or args.idle or args.push_force_n or args.wait_force_n:
    parser.error('Fresh two-pass pilot requires one320-frame paired layout; no policy/waits/forces')
for key in ('spatial_pilot_contract','recovery_pilot_contract','diagnostic_layout_json','layout_x_offset',
            'policy_max_action_step','settled_contact','recover_contact_height','expert_front_reposition',
            'expert_front_reposition_hold_yz','expert_front_reposition_measured_start','bounded_servo_memory',
            'finger_heading_weight','expert_max_contact_x','expert_contact_confirmed_sweep',
            'expert_object_feedback_lead','expert_crossed_contact_offset','trace_contacts',
            'trace_solved_contact_forces','trace_episode_contacts'):
    if getattr(args,key):parser.error('Unregistered two-pass pilot option: '+key)
if not args.newton_contacts or args.prompt_variant!='short' or args.expert_exit_y!=.30:
    parser.error('Two-pass pilot requires reviewed Newton collision pipeline, exact prompts and endpoint')
if args.expert_staging_z!=.92 or args.expert_far_contact_offset!=-.11 or args.expert_contact_offset!=-.13:
    parser.error('Two-pass prototype requires reviewed first-phase .92 staging/-.11 far/-.13 near offsets')
if args.policy_port and (args.role != 'diagnostic' or args.horizon != 10 or args.idle):
    parser.error('Policy evaluation requires diagnostic role, horizon=10 and no idle flag')
if args.policy_max_action_step and (not args.policy_port or not 0 < args.policy_max_action_step <= .08):
    parser.error('Action slew diagnostic requires policy evaluation and a cap in (0, .08]')
if args.recover_contact_height and (args.role != 'diagnostic' or args.policy_port or args.idle):
    parser.error('Contact-height recovery requires diagnostic expert only')
if args.settled_contact and (args.role != 'diagnostic' or args.policy_port or args.idle):
    parser.error('Settled-contact experiment requires diagnostic expert collection')
if args.wait_force_n and ((args.role != 'diagnostic' and not args.recovery_pilot_contract) or args.policy_port or args.idle or args.layouts != 0 or not 0 < args.wait_force_n <= 80):
    parser.error('Wait force requires diagnostic wait-only collection and force in (0,80] N')
if args.push_force_n and ((args.role != 'diagnostic' and not args.recovery_pilot_contract) or args.policy_port or args.idle or args.wait_force_n or args.wait_episodes or not 0 < args.push_force_n <= 80):
    parser.error('Push force requires diagnostic push-only expert and force in (0,80] N')
if args.push_force_axis != 'x' or args.push_force_start != 5:
    if args.role != 'diagnostic' or not args.push_force_n or args.policy_port or not 1 <= args.push_force_start <= args.steps-6:
        parser.error('Alternate push-force profile requires diagnostic expert and a valid six-frame window')
if args.wait_force_start not in (5,20):
    parser.error('Wait pulse start must be5 or20')
if args.trace_solved_contact_forces and args.role != 'diagnostic':
    parser.error('Solved force tracing is diagnostic only')
if args.trace_episode_contacts and args.role != 'diagnostic':
    parser.error('Episode contact tracing is diagnostic only')
recovery_contract_hash = None
if args.recovery_pilot_contract:
    if args.role != 'pilot' or args.policy_port or args.idle or not (args.wait_force_n or args.push_force_n):
        parser.error('Recovery contract requires fresh forced pilot expert collection')
    from simfoundry.data.recovery_protocol import validate_contract
    recovery_contract_hash = validate_contract(args.recovery_pilot_contract,
        layouts=range(args.layout_start,args.layout_start+args.layouts),
        waits=range(args.wait_layout_start,args.wait_layout_start+args.wait_episodes),
        push_force=args.push_force_n,wait_force=args.wait_force_n,
        wait_side=args.wait_force_side,wait_start=args.wait_force_start)
if args.diagnostic_layout_json:
    if args.role != 'diagnostic' or args.layouts != 1 or args.wait_episodes or args.layout_x_offset or args.recovery_pilot_contract:
        parser.error('Explicit layouts require one diagnostic pair and no offsets/waits/contracts')
    from simfoundry.data.diverse_layouts import load_diagnostic_layout
    explicit_layout = load_diagnostic_layout(args.diagnostic_layout_json, args.layout_start)

if args.expert_contact_confirmed_sweep and (args.role != 'diagnostic' or args.policy_port or args.idle or not args.expert_object_feedback_lead):
    parser.error('Contact-confirmed sweep requires diagnostic object feedback')
if args.expert_object_feedback_lead and (args.role != 'diagnostic' or args.policy_port or args.idle or not .02 <= args.expert_object_feedback_lead <= .06):
    parser.error('Object feedback requires diagnostic expert and lead .02-.06m')
if args.expert_far_contact_offset and ((args.role != 'diagnostic' and not args.spatial_pilot_contract and not args.twopass_pilot_contract) or args.policy_port or args.idle or not -.13 <= args.expert_far_contact_offset <= -.04):
    parser.error('Far contact offset requires diagnostic expert and bounded -.13..-.04m offset')
if args.finger_heading_weight and (args.role != 'diagnostic' or args.policy_port or args.idle or not .02 <= args.finger_heading_weight <= .12):
    parser.error('Finger heading requires diagnostic expert and weight .02-.12')
if args.expert_max_contact_x and (args.role != 'diagnostic' or args.policy_port or args.idle or not .42 <= args.expert_max_contact_x <= .50):
    parser.error('Contact-X cap requires diagnostic expert and cap .42-.50m')
if args.bounded_servo_memory and (args.role != 'diagnostic' or args.policy_port or args.idle):
    parser.error('Bounded servo memory is diagnostic expert only')
if args.expert_staging_z != 1.0 or args.expert_contact_offset != -.13:
    if (args.role != 'diagnostic' and not args.spatial_pilot_contract and not args.twopass_pilot_contract) or args.policy_port or args.idle or not .90 <= args.expert_staging_z <= 1.0 or not -.13 <= args.expert_contact_offset <= -.04:
        parser.error('Alternative approach geometry requires diagnostic expert and bounded geometry')

if args.expert_exit_y != .30:
    if args.role != 'diagnostic' or args.policy_port or args.idle or args.spatial_pilot_contract or not .30 <= args.expert_exit_y <= .34:
        parser.error('Alternate endpoint requires diagnostic expert and .30-.34m endpoint')

if args.expert_crossed_contact_offset and (args.role != 'diagnostic' or args.policy_port or args.idle or args.spatial_pilot_contract or not -.13 <= args.expert_crossed_contact_offset <= -.04):
    parser.error('Crossed approach offset requires diagnostic expert and -.13..-.04m offset')

if args.expert_front_reposition and (args.role != 'diagnostic' or args.policy_port or args.idle or args.spatial_pilot_contract or args.wait_episodes or not .02 <= args.expert_front_reposition <= .04):
    parser.error('Front reposition requires diagnostic push-only expert and .02-.04m travel')

if args.expert_front_reposition_hold_yz and not args.expert_front_reposition_measured_start:
    parser.error('Hold Y/Z requires measured front reposition start')
if args.expert_front_reposition_measured_start and not args.expert_front_reposition:
    parser.error('Measured retreat start requires the diagnostic front reposition primitive')

spatial_contract_hash = None
if args.spatial_pilot_contract:
    if (args.role != 'pilot' or args.layouts != 1 or args.wait_episodes or args.policy_port or args.idle
            or args.diagnostic_layout_json or args.layout_x_offset or args.recovery_pilot_contract
            or args.wait_force_n or args.push_force_n or args.settled_contact or args.recover_contact_height
            or args.bounded_servo_memory or args.finger_heading_weight or args.expert_max_contact_x):
        parser.error('Spatial pilot requires one fresh registered unforced pair and reviewed expert settings only')
    from simfoundry.data.spatial_protocol import validate_spatial_contract
    from simfoundry.data.diverse_layouts import validate_diagnostic_layout
    explicit_layout, spatial_contract_hash = validate_spatial_contract(args.spatial_pilot_contract,
        layout_id=args.layout_start, steps=args.steps, staging_z=args.expert_staging_z,
        contact_offset=args.expert_contact_offset, far_contact_offset=args.expert_far_contact_offset)
    validate_diagnostic_layout(explicit_layout, args.layout_start)

from simfoundry.data.twopass_protocol import validate_twopass_contract, EXPERT as TWOPASS_EXPERT
explicit_layout, twopass_contract_hash = validate_twopass_contract(args.twopass_pilot_contract, layout_id=args.layout_start, steps=args.steps)

app = AppLauncher(args, enable_cameras=True).app

import numpy as np
from PIL import Image
import torch
from isaaclab.envs import ManagerBasedRLEnv
from simfoundry.calibration.sorting_station import reset_sorting_parcels, _set_visible, _write_pose, _DECORATIVE_PARCELS, _OFFTABLE_XYZ
from simfoundry.data.paired_sorting import sample_layout, audit_rollout, audit_pair
from simfoundry.data.prompts import PAIRED_SORTING_PROMPTS, VLA_SORTING_UNIFIED_PROMPT
from simfoundry.data.pi05_rpc import request as policy_request
from simfoundry.data.schema import TrajectoryEpisode, save_episode
from simfoundry.data.sorting_cartesian_expert import CartesianSweepState, cartesian_sweep_palm
from simfoundry.data.sorting_quality import resolve_hand_indices, palm_xyz, parcel_xyz
from simfoundry.robots.g1_assets import G1_U1_23DOF_JOINT_NAMES
from simfoundry.isaac_envs.registry import resolve_scene_env
from simfoundry.robots.g1_assets import u1_sorting_default_qpos_np, U1_JOINT_LIMIT_LO, U1_JOINT_LIMIT_HI
from simfoundry.scene_bridge.labels import sync_shipping_labels


def snap(env, robot, hands):
    return {'box': parcel_xyz(env, 'parcel_box'), 'mailer': parcel_xyz(env, 'mailer'),
            'palm_left': palm_xyz(robot, hands['left']), 'palm_right': palm_xyz(robot, hands['right'])}



def read_episode_contact_buffer(action_step):
    """Read existing collision candidates; never refresh/mutate solver contacts.

    Sampled after the control step; buffer reflects the last physics collision
    query, not every substep or solved contact impulse. Candidate presence alone
    is not proof of a load-bearing contact.
    """
    from isaaclab_newton.physics.newton_manager import NewtonManager
    contacts = NewtonManager.get_contacts()
    if contacts is None:
        raise RuntimeError('No Newton contact buffer available for diagnostic')
    model = NewtonManager.get_model()
    count = int(contacts.rigid_contact_count.numpy()[0])
    shape0 = contacts.rigid_contact_shape0.numpy()
    shape1 = contacts.rigid_contact_shape1.numpy()
    if count > len(shape0) or count > len(shape1):
        raise RuntimeError('Contact buffer overflow; diagnostic incomplete')
    pairs = {}
    for a,b in zip(shape0[:count],shape1[:count]):
        if a < 0 or b < 0:
            continue
        labels = tuple(sorted((model.shape_label[int(a)],model.shape_label[int(b)])))
        if not any('/parcel_box/' in x or '/mailer/' in x for x in labels):
            continue
        pairs[labels] = pairs.get(labels,0) + 1
    return {'after_action_step':action_step,'total_contact_candidates':count,
            'target_pairs':[{'shapes':list(k),'candidate_points':v} for k,v in sorted(pairs.items())]}


def collect(env, spec, layout, task_id, root, default):
    robot = env.scene['robot']
    hands = resolve_hand_indices(robot)
    zero = torch.zeros((1, 23), device=env.device)
    rng = np.random.default_rng(layout['seed'])
    env.reset()
    if args.wait_force_n or args.push_force_n:
        robot.permanent_wrench_composer.reset()
    reset_sorting_parcels(env, task_id=task_id, single_parcel=False, rng=rng,
                         box_xyz=tuple(layout['box_xyz']) if task_id != 'wait_no_package' else None,
                         mailer_xyz=tuple(layout['mailer_xyz']) if task_id != 'wait_no_package' else None,
                         box_yaw=layout.get('box_yaw', 0.), mailer_yaw=layout.get('mailer_yaw', 0.))
    # Hidden rigid bodies still collide. Give each one its own offstage spot
    # rather than stacking them at a common position and producing impulses.
    hidden = list(_DECORATIVE_PARCELS)
    if task_id == 'wait_no_package':
        hidden += ['parcel_box', 'mailer']
    for index, name in enumerate(hidden):
        _set_visible(env, name, False)
        _write_pose(env, name, (5.0 + index, 5.0, .3))
    reset_trace = []
    print('RESET_REQUEST', layout, 'ACTUAL', snap(env, robot, hands), flush=True)
    for warmup_step in range(60):
        env.step(zero)
        sync_shipping_labels(env)
        if args.trace_contacts and warmup_step in (0, 1, 5, 15, 30, 59):
            from isaaclab_newton.physics.newton_manager import NewtonManager
            contacts = NewtonManager.get_contacts()
            NewtonManager._solver.update_contacts(contacts, NewtonManager.get_state_0())
            model = NewtonManager.get_model()
            n = int(contacts.rigid_contact_count.numpy()[0])
            a, b = contacts.rigid_contact_shape0.numpy()[:n], contacts.rigid_contact_shape1.numpy()[:n]
            pairs = sorted(set(tuple(sorted((model.shape_label[int(x)], model.shape_label[int(y)])))
                               for x, y in zip(a, b) if x >= 0 and y >= 0
                               and any(tag in model.shape_label[int(x)] or tag in model.shape_label[int(y)]
                                       for tag in ('/parcel_box/', '/mailer/'))))
            geometry = []
            if warmup_step == 0:
                for idx, label in enumerate(model.shape_label):
                    if any(tag in label for tag in ('/table/', '/table_edge_wear/', '/parcel_box/', '/mailer/')):
                        body = int(model.shape_body.numpy()[idx])
                        geometry.append({'label': label, 'type': int(model.shape_type.numpy()[idx]),
                            'scale': model.shape_scale.numpy()[idx].tolist(),
                            'local': model.shape_transform.numpy()[idx].tolist(),
                            'body_pose': NewtonManager.get_state_0().body_q.numpy()[body].tolist() if body >= 0 else None})
            row = {'step': warmup_step, 'pose': snap(env, robot, hands), 'contacts': pairs,
                   'geometry': geometry, 'normals': contacts.rigid_contact_normal.numpy()[:n].tolist()}
            reset_trace.append(row)
            print('RESET_CONTACTS', json.dumps(row), flush=True)
    # Reset real physical joint state after scene settling, before capture.
    # No data values are relabeled. Rendering and observations read this state.
    ordered_ids = [robot.joint_names.index(n) for n in G1_U1_23DOF_JOINT_NAMES]
    actual_default = robot.data.default_joint_pos.torch[0, ordered_ids].cpu().numpy()
    if not np.allclose(actual_default, default, atol=1e-6):
        raise RuntimeError('Action offset baseline differs from configured robot default')
    q0 = torch.tensor(default[None], device=env.device)
    robot.write_joint_position_to_sim_index(position=q0, joint_ids=ordered_ids)
    robot.write_joint_velocity_to_sim_index(velocity=torch.zeros_like(q0), joint_ids=ordered_ids)
    env.scene.write_data_to_sim()
    env.sim.forward()
    for _ in range(3):
        env.sim.render()
        env.scene.update(0.0)
    obs = env.observation_manager.compute()
    initial = snap(env, robot, hands)
    initial_quats = {key: env.scene[name].data.root_quat_w.torch[0].detach().cpu().numpy().copy()
                     for key, name in [('box', 'parcel_box'), ('mailer', 'mailer')]}
    side = 'right' if task_id == 'push_box_to_bin' else 'left'
    target = initial['box' if side == 'right' else 'mailer']
    contact_bias = min(0., args.expert_max_contact_x-target[0]) if args.expert_max_contact_x else 0.
    from simfoundry.data.diverse_layouts import contact_offset_for_approach
    effective_offset = contact_offset_for_approach(target[0], target[1], -1 if side == 'right' else 1, args.expert_contact_offset, args.expert_far_contact_offset, args.expert_crossed_contact_offset)
    expert = CartesianSweepState(side, target[0], target[1], exit_y=args.expert_exit_y, contact_x_bias=contact_bias,
                                 contact_palm_z=.840 if side == "left" else .845,
                                 staging_palm_z=args.expert_staging_z, contact_side_offset=effective_offset,
                                 object_feedback_lead=args.expert_object_feedback_lead if target[0] >= .48 else 0.,
                                 contact_confirmed_sweep=args.expert_contact_confirmed_sweep and target[0] >= .48,
                                 finger_heading_weight=args.finger_heading_weight, bounded_servo_memory=args.bounded_servo_memory,
                                 settled_contact=args.settled_contact, recover_contact_height=args.recover_contact_height)
    if args.expert_front_reposition and target[0] < .43 and (-1 if side == 'right' else 1)*target[1] < -.03:
        expert.front_reposition_distance = args.expert_front_reposition
        expert.front_reposition_measured_start = args.expert_front_reposition_measured_start
        expert.front_reposition_hold_yz = args.expert_front_reposition_hold_yz
    recontact_event=None
    initial_target_x=float(target[0])
    parcel_orientations = {'box': [], 'mailer': []}
    horizon = 70 if args.idle or task_id == 'wait_no_package' else args.steps
    rgbs, qs, acts = [], [], []
    trace = {key: [] for key in initial}
    previous = np.zeros(23, dtype=np.float32)
    prompt = PAIRED_SORTING_PROMPTS[task_id]
    if args.policy_port and args.prompt_variant == 'unified_ablation':
        prompt = VLA_SORTING_UNIFIED_PROMPT
    chunk, cursor = None, 0
    infer_log = []
    raw_policy_actions = []
    expert_control = []
    force_log = []
    episode_contacts = []
    solved_contact_forces = []
    if args.policy_port:
        policy_request(args.policy_host, args.policy_port, {'cmd': 'reset_seed', 'seed': args.eval_seed})
    for step in range(horizon):
        action = np.zeros(23, dtype=np.float32)
        if args.policy_port:
            if chunk is None or cursor >= min(args.horizon, len(chunk)):
                state = obs['policy'][0].detach().cpu().numpy()[[*range(13,23), 12]]
                image = obs['rgb'][0].detach().cpu().numpy()
                if image.shape[0] in (3,4):
                    image = image[:3].transpose(1,2,0)
                reply = policy_request(args.policy_host, args.policy_port,
                    {'cmd': 'infer', 'image': image, 'state': state, 'task': prompt})
                chunk = np.asarray(reply['actions'], dtype=np.float32)
                if chunk.ndim != 2 or chunk.shape[1] != 11 or len(chunk) < 1 or not np.isfinite(chunk).all():
                    raise ValueError('Invalid policy action chunk')
                cursor = 0
                infer_log.append({'step': step, 'state': state.tolist(), 'prompt': prompt,
                                  'actions': chunk.tolist(), 'infer_ms': reply.get('infer_ms')})
            action[[*range(13,23), 12]] = chunk[cursor]
            cursor += 1
            raw_policy_actions.append((default + action).copy())
            if args.policy_max_action_step:
                action = np.clip(action, previous - args.policy_max_action_step,
                                 previous + args.policy_max_action_step)
        elif step>=160 and initial_target_x<.48:
            action=previous.copy()
        elif step > 0 and not args.idle and task_id != 'wait_no_package':
            if step==160:
                current=parcel_xyz(env,'parcel_box' if side=='right' else 'mailer')
                expert=CartesianSweepState(side,float(current[0]),float(current[1]),exit_y=.30,
                    contact_palm_z=(.840 if side=='left' else .845)-.02,staging_palm_z=1.,
                    contact_side_offset=-.11)
                recontact_event=dict(step=160,target_xyz=np.asarray(current).tolist(),height_offset_m=-.02)
            observed_y = parcel_xyz(env, 'parcel_box' if side == 'right' else 'mailer')[1] if expert.object_feedback_lead else None
            cartesian_sweep_palm(robot, hands, action, state=expert, step=step-1, default_q=default, observed_parcel_y=observed_y)
            # The legacy expert instantly parks the inactive arm. Ramp every
            # joint target so the zero-pose start never creates a discontinuity.
            action = np.clip(action, previous - .055, previous + .055)
        action = np.clip(default + action, U1_JOINT_LIMIT_LO, U1_JOINT_LIMIT_HI) - default
        action[12] = 0.
        action = action.astype(np.float32)
        previous = action.copy()
        sample = snap(env, robot, hands)
        if not args.policy_port:
            expert_control.append({'step': step, 'mode': expert.mode, 'mode_step': expert.mode_step,
                                   'settle_count': expert.contact_settle_count, 'height_paused': expert.sweep_height_paused, 'height_settle_count': expert.sweep_height_settle_count, 'sweep_pause_frames': expert.sweep_pause_frames, 'target_xyz': expert.last_target_xyz, 'feedback_target_y': expert.feedback_target_y, 'front_reposition_start_x': expert.front_reposition_start_x, 'front_reposition_start_yz': expert.front_reposition_start_yz})
        if True:
            for key, actor in [('box', 'parcel_box'), ('mailer', 'mailer')]:
                parcel_orientations[key].append(env.scene[actor].data.root_quat_w.torch[0].detach().cpu().numpy().copy())
        for key in trace:
            trace[key].append(sample[key])
        rgb = obs['rgb'][0].detach().cpu().numpy()
        if rgb.shape[-1] in (3, 4):
            rgb = rgb[..., :3].transpose(2, 0, 1)
        rgb = rgb[:3]
        if rgb.dtype != np.uint8:
            rgb = np.clip(rgb * (255 if rgb.max() <= 1.5 else 1), 0, 255).astype(np.uint8)
        if step % 30 == 0:
            progress = {'layout_id': layout['layout_id'], 'task': task_id, 'step': step,
                        'expert_mode': expert.mode, 'pose': sample}
            (root / 'progress.json').write_text(json.dumps(progress, indent=2))
            Image.fromarray(rgb.transpose(1, 2, 0)).save(root / 'progress.jpg')
            print('PROGRESS', json.dumps(progress), flush=True)
        rgbs.append(rgb)
        qs.append(obs['policy'][0].detach().cpu().numpy().copy())
        acts.append(default + action)
        if args.wait_force_n or args.push_force_n:
            force_start = args.push_force_start if args.push_force_n else args.wait_force_start
            force_amplitude = args.push_force_n or args.wait_force_n
            force_value = force_amplitude * float(np.sin(np.pi * (step-force_start+1) / 7)) if force_start <= step <= force_start+5 else 0.
            force_axis = args.push_force_axis if args.push_force_n else 'x'
            force_vector = ([0.,0.,force_value] if force_axis == 'z' else [-force_value if force_axis == 'negative_x' else force_value,0.,0.])
            robot.permanent_wrench_composer.reset()
            force_sides = (side,) if args.push_force_n else (('left','right') if args.wait_force_side == 'both' else (args.wait_force_side,))
            force_ids = [hands[side] for side in force_sides]
            if force_value:
                force = torch.tensor([[force_vector] * len(force_ids)], dtype=torch.float32, device=env.device)
                robot.permanent_wrench_composer.set_forces_and_torques_index(forces=force, body_ids=force_ids, is_global=True)
            force_log.append({'step':step,'bodies':[side+'_hand' for side in force_sides], 'body_indices':force_ids,'force_per_body_world_N':force_vector})
        obs, _, terminated, truncated, _ = env.step(torch.tensor(action[None], device=env.device))
        if args.trace_episode_contacts:
            contact_record = read_episode_contact_buffer(step)
            contact_record['post_action_pose'] = snap(env, robot, hands)
            episode_contacts.append(contact_record)
        if args.trace_solved_contact_forces:
            from simfoundry.data.solved_contact_trace import read_solved_contact_forces
            force_record = read_solved_contact_forces(step)
            force_record['post_action_pose'] = snap(env, robot, hands)
            solved_contact_forces.append(force_record)
        sync_shipping_labels(env)
        if bool(terminated[0] or truncated[0]):
            break
    if args.wait_force_n or args.push_force_n:
        robot.permanent_wrench_composer.reset()
    episode = TrajectoryEpisode(rgb=np.stack(rgbs), q=np.stack(qs), action=np.stack(acts),
        instruction=prompt, scene_id=spec.scene_id, task_id=task_id,
        embodiment_id=spec.embodiment_id, joint_names=spec.joint_names,
        collect_meta={'layout': layout, 'layout_id': layout['layout_id'], 'zero_upper_body': True,
                      'box_xyz': initial['box'], 'mailer_xyz': initial['mailer'],
                      'box_quat_xyzw': initial_quats['box'].tolist(), 'mailer_quat_xyzw': initial_quats['mailer'].tolist(),
                      'push_assist': False, 'assist_frames': 0, 'expert': 'pi05_h10' if args.policy_port else 'paired_zero_cartesian',
                      'idle_diagnostic': args.idle, 'collection_role': args.role, 'exit_y': expert.exit_y, 'contact_x_bias': expert.contact_x_bias, 'contact_palm_z': expert.contact_palm_z,
                      'staging_palm_z': expert.staging_palm_z, 'contact_side_offset': expert.contact_side_offset, 'bounded_servo_memory': expert.bounded_servo_memory, 'max_contact_x': args.expert_max_contact_x, 'far_contact_offset': args.expert_far_contact_offset, 'base_contact_offset': args.expert_contact_offset, 'front_reposition_distance': expert.front_reposition_distance, 'front_reposition_measured_start': expert.front_reposition_measured_start, 'front_reposition_hold_yz': expert.front_reposition_hold_yz, 'crossed_contact_offset': args.expert_crossed_contact_offset, 'object_feedback_lead': expert.object_feedback_lead, 'contact_confirmed_sweep': expert.contact_confirmed_sweep, 'finger_heading_weight': args.finger_heading_weight,
                      'collision_pipeline': 'newton' if args.newton_contacts else 'mujoco',
                      'policy_action_step_cap': args.policy_max_action_step, 'settled_contact': args.settled_contact, 'recover_contact_height': args.recover_contact_height, 'wait_force_n': args.wait_force_n, 'wait_force_side': args.wait_force_side, 'push_force_n': args.push_force_n, 'push_force_axis': args.push_force_axis, 'push_force_start': args.push_force_start, 'wait_force_start': args.wait_force_start, 'twopass_contract_sha256': twopass_contract_hash, 'twopass_expert': TWOPASS_EXPERT, 'spatial_pilot_contract_sha256': spatial_contract_hash, 'recovery_contract_sha256': recovery_contract_hash})
    report = audit_rollout(task_id, episode.q, episode.action, trace, idle=args.idle, require_zero_action=not bool(args.policy_port))
    if task_id != 'wait_no_package':
        for key in ('box', 'mailer'):
            drift = float(np.linalg.norm(np.asarray(initial[key])[:2] - np.asarray(layout[key + '_xyz'])[:2]))
            report['metrics'][key + '_reset_drift_m'] = drift
            if key + '_yaw' in layout:
                yaw = layout[key + '_yaw']
                requested_quat = np.array([0., 0., np.sin(yaw/2), np.cos(yaw/2)])
                angle_error = float(2*np.arccos(np.clip(abs(np.dot(requested_quat, initial_quats[key])), 0., 1.)))
                report['metrics'][key + '_reset_angle_error_rad'] = angle_error
                if angle_error > .03:
                    report['reasons'].append(f'{key} orientation drift during reset/settling')
            if drift > .015:
                report['reasons'].append(f'{key} moved {drift:.4f} m during reset/settling')
        report['passed'] = not report['reasons']
    rgb_means = episode.rgb.mean(axis=(1, 2, 3))
    frame_changes = [float(np.abs(a.astype(np.int16) - b.astype(np.int16)).mean())
                     for a, b in zip(episode.rgb[:-1], episode.rgb[1:])]
    report['metrics']['min_frame_rgb_mean'] = float(rgb_means.min())
    report['metrics']['max_frame_rgb_change'] = max(frame_changes, default=0.)
    if float(rgb_means.min()) < 255 * .12:
        report['reasons'].append('one or more RGB frames too dark')
    if max(frame_changes, default=0.) > 40:
        report['reasons'].append('large RGB discontinuity: inspect rendering/reset')
    report['passed'] = not report['reasons']
    report['expert_end_mode'] = expert.mode
    report['frames'] = len(qs)
    folder = root / f"layout_{layout['layout_id']:04d}_{task_id}"
    folder.mkdir()
    # Raw failures and candidates stay outside training dataset directories.
    save_episode(episode, folder / 'raw.npz')
    np.savez_compressed(folder / 'trace.npz', **trace)
    if True:
        np.savez_compressed(folder / 'parcel_orientation.npz', **{k: np.asarray(v) for k,v in parcel_orientations.items()})
    (folder / 'expert_control.json').write_text(json.dumps(expert_control, indent=2))
    if args.wait_force_n or args.push_force_n:
        (folder / 'external_force.json').write_text(json.dumps(force_log, indent=2))
    if args.policy_port:
        (folder / 'policy_inferences.json').write_text(json.dumps(infer_log))
        requested = np.asarray(raw_policy_actions)
        np.savez_compressed(folder / 'policy_raw_actions.npz', action=requested)
        report['metrics']['raw_policy_max_action_step_rad'] = float(np.abs(np.diff(requested[:,12:], axis=0)).max())
        report['metrics']['policy_modified_frames'] = int(np.any(np.abs(requested[:,12:] - episode.action[:,12:]) > 1e-6, axis=1).sum())
        report['metrics']['max_policy_action_modification_rad'] = float(np.abs(requested[:,12:] - episode.action[:,12:]).max())
    (folder / 'reset_contacts.json').write_text(json.dumps(reset_trace, indent=2))
    if args.trace_episode_contacts:
        (folder / 'episode_contacts.json').write_text(json.dumps({'sampling':'read-only last physics collision buffer after control action; not all substeps, not forces/impulses','rows':episode_contacts},indent=2))
    if args.trace_solved_contact_forces:
        (folder / 'solved_contact_forces.json').write_text(json.dumps({'sampling':'last physics tick after control action; solved force, not integrated impulse; separate output arrays; no solver refresh', 'rows':solved_contact_forces},indent=2))
    (folder / 'recontact_event.json').write_text(json.dumps(dict(event=recontact_event,initial_target_x=initial_target_x,training_ready=False),indent=2))
    (folder / 'quality.json').write_text(json.dumps(report, indent=2))
    frames = np.linspace(0, len(rgbs)-1, 12).astype(int)
    sheet = Image.new('RGB', (640*4, 480*3))
    for i, t in enumerate(frames):
        sheet.paste(Image.fromarray(rgbs[t].transpose(1, 2, 0)), ((i%4)*640, (i//4)*480))
    sheet.save(folder / 'contact_sheet.jpg')
    print(json.dumps({'layout': layout['layout_id'], 'task': task_id, **report}), flush=True)
    return episode, report


def main():
    root = Path(args.out_dir)
    root.mkdir(parents=True, exist_ok=False)
    (root / 'STATUS.json').write_text(json.dumps({'training_ready': False, 'status': 'collecting_fresh_twopass_pilot'}))
    if args.spatial_pilot_contract:
        (root/'spatial_pilot_contract.json').write_bytes(args.spatial_pilot_contract.read_bytes())
    if args.recovery_pilot_contract:
        (root/'recovery_pilot_contract.json').write_bytes(args.recovery_pilot_contract.read_bytes())
    if args.diagnostic_layout_json:
        (root/'explicit_layout.json').write_bytes(Path(args.diagnostic_layout_json).read_bytes())
    (root/'twopass_pilot_contract.json').write_bytes(args.twopass_pilot_contract.read_bytes())
    paths = [ROOT / 'simfoundry/data/twopass_protocol.py', ROOT / 'simfoundry/calibration/sorting_station.py', ROOT / 'simfoundry/data/spatial_protocol.py', ROOT / 'simfoundry/data/diverse_layouts.py', ROOT / 'simfoundry/data/recovery_protocol.py', Path(__file__).resolve(), ROOT / 'simfoundry/data/paired_sorting.py', ROOT / 'simfoundry/robots/g1_assets.py', ROOT / 'simfoundry/data/sorting_cartesian_expert.py']
    (root / 'provenance.json').write_text(json.dumps({
        'args': vars(args), 'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        'physics': 'Newton MJWarp (existing scene backend)', 'training_ready': False,
    }, indent=2, default=str))
    spec = resolve_scene_env('sorting_station_g1_23')
    default = u1_sorting_default_qpos_np(zero_upper_body=True)
    cfg = spec.env_cfg_cls()
    cfg.scene.num_envs = 1
    cfg.sim.device = args.device
    cfg.episode_length_s = 40.
    if args.newton_contacts:
        cfg.sim.physics.default.solver_cfg.use_mujoco_contacts = False
    cfg.scene.robot.init_state.joint_pos = dict(zip(G1_U1_23DOF_JOINT_NAMES, default.tolist()))
    env = None
    results = []
    try:
        env = ManagerBasedRLEnv(cfg=cfg)
        for i in range(args.layout_start, args.layout_start + args.layouts):
            layout = dict(explicit_layout) if (args.diagnostic_layout_json or args.spatial_pilot_contract or args.twopass_pilot_contract) else sample_layout(i)
            for key in ('box_xyz', 'mailer_xyz'):
                layout[key][0] += args.layout_x_offset
            episodes, reports = [], []
            for task_id in ('push_box_to_bin', 'nudge_mailer_to_bin'):
                ep, report = collect(env, spec, layout, task_id, root, default)
                episodes.append(ep)
                reports.append(report)
            prompts = ({key: VLA_SORTING_UNIFIED_PROMPT for key in PAIRED_SORTING_PROMPTS}
                       if args.policy_port and args.prompt_variant == 'unified_ablation' else PAIRED_SORTING_PROMPTS)
            pair = audit_pair(*episodes, prompts=prompts)
            results.append({'layout': layout, 'episodes': reports, 'pair': pair})
            (root / 'manifest.json').write_text(json.dumps(results, indent=2))
            if not args.policy_port and (not pair['passed'] or not all(r['passed'] for r in reports)):
                raise RuntimeError('Quality gate failed. Stop; no retries or training export. See manifest.json.')
        for i in range(args.wait_episodes):
            layout = sample_layout(args.wait_layout_start+i)
            _, report = collect(env, spec, layout, 'wait_no_package', root, default)
            results.append({'layout': layout, 'episodes': [report]})
            (root / 'manifest.json').write_text(json.dumps(results, indent=2))
            if not args.policy_port and not report['passed']:
                raise RuntimeError('Wait quality gate failed.')
        (root / 'STATUS.json').write_text(json.dumps({'training_ready': False, 'status': 'evaluation_complete' if args.policy_port else 'numeric_pass_visual_review_pending'}))
    except Exception as exc:
        (root / 'STATUS.json').write_text(json.dumps({'training_ready': False, 'status': 'blocked_quality_or_runtime', 'error': str(exc)}))
        raise
    finally:
        if env is not None:
            env.close()
        app.close()

if __name__ == '__main__':
    main()
