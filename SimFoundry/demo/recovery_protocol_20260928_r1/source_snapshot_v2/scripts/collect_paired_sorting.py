#!/usr/bin/env python3
"""Zero-start paired pilot. Raw diagnostics are quarantined; never auto-train."""
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
parser.add_argument('--role', choices=('diagnostic', 'pilot'), default='diagnostic')
parser.add_argument('--layout-start', type=int, default=0)
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
parser.add_argument('--wait-force-side', choices=('left','right','both'), default='left', help='Diagnostic physical force target; each selected hand receives wait-force-n.')
parser.add_argument('--settled-contact', action='store_true', help='Diagnostic expert: settle near contact height before sweeping.')
parser.add_argument('--trace-contacts', action='store_true', help='Diagnostic Newton contact pairs.')
parser.add_argument('--newton-contacts', action='store_true', help='Diagnostic collision-pipeline comparison.')
parser.add_argument('--layout-x-offset', type=float, default=0., help='Diagnostic reachability offset [m].')
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
if args.policy_port and (args.role != 'diagnostic' or args.horizon != 10 or args.idle):
    parser.error('Policy evaluation requires diagnostic role, horizon=10 and no idle flag')
if args.policy_max_action_step and (not args.policy_port or not 0 < args.policy_max_action_step <= .08):
    parser.error('Action slew diagnostic requires policy evaluation and a cap in (0, .08]')
if args.settled_contact and (args.role != 'diagnostic' or args.policy_port or args.idle):
    parser.error('Settled-contact experiment requires diagnostic expert collection')
if args.wait_force_n and (args.role != 'diagnostic' or args.policy_port or args.idle or args.layouts != 0 or not 0 < args.wait_force_n <= 80):
    parser.error('Wait force requires diagnostic wait-only collection and force in (0,80] N')
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


def collect(env, spec, layout, task_id, root, default):
    robot = env.scene['robot']
    hands = resolve_hand_indices(robot)
    zero = torch.zeros((1, 23), device=env.device)
    rng = np.random.default_rng(layout['seed'])
    env.reset()
    if args.wait_force_n:
        robot.permanent_wrench_composer.reset()
    reset_sorting_parcels(env, task_id=task_id, single_parcel=False, rng=rng,
                         box_xyz=tuple(layout['box_xyz']) if task_id != 'wait_no_package' else None,
                         mailer_xyz=tuple(layout['mailer_xyz']) if task_id != 'wait_no_package' else None)
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
    side = 'right' if task_id == 'push_box_to_bin' else 'left'
    target = initial['box' if side == 'right' else 'mailer']
    expert = CartesianSweepState(side, target[0], target[1], exit_y=.30, contact_x_bias=0.0,
                                 contact_palm_z=.840 if side == "left" else .845,
                                 settled_contact=args.settled_contact)
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
        elif step > 0 and not args.idle and task_id != 'wait_no_package':
            cartesian_sweep_palm(robot, hands, action, state=expert, step=step-1, default_q=default)
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
                                   'settle_count': expert.contact_settle_count})
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
        if args.wait_force_n:
            force_x = args.wait_force_n * float(np.sin(np.pi * (step-19) / 7)) if 20 <= step <= 25 else 0.
            robot.permanent_wrench_composer.reset()
            force_sides = ('left','right') if args.wait_force_side == 'both' else (args.wait_force_side,)
            force_ids = [hands[side] for side in force_sides]
            if force_x:
                force = torch.tensor([[[force_x, 0., 0.]] * len(force_ids)], dtype=torch.float32, device=env.device)
                robot.permanent_wrench_composer.set_forces_and_torques_index(forces=force, body_ids=force_ids, is_global=True)
            force_log.append({'step':step,'bodies':[side+'_hand' for side in force_sides], 'body_indices':force_ids,'force_per_body_world_N':[force_x,0.,0.]})
        obs, _, terminated, truncated, _ = env.step(torch.tensor(action[None], device=env.device))
        sync_shipping_labels(env)
        if bool(terminated[0] or truncated[0]):
            break
    if args.wait_force_n:
        robot.permanent_wrench_composer.reset()
    episode = TrajectoryEpisode(rgb=np.stack(rgbs), q=np.stack(qs), action=np.stack(acts),
        instruction=prompt, scene_id=spec.scene_id, task_id=task_id,
        embodiment_id=spec.embodiment_id, joint_names=spec.joint_names,
        collect_meta={'layout': layout, 'layout_id': layout['layout_id'], 'zero_upper_body': True,
                      'box_xyz': initial['box'], 'mailer_xyz': initial['mailer'],
                      'push_assist': False, 'assist_frames': 0, 'expert': 'pi05_h10' if args.policy_port else 'paired_zero_cartesian',
                      'idle_diagnostic': args.idle, 'collection_role': args.role, 'exit_y': expert.exit_y, 'contact_x_bias': expert.contact_x_bias, 'contact_palm_z': expert.contact_palm_z,
                      'collision_pipeline': 'newton' if args.newton_contacts else 'mujoco',
                      'policy_action_step_cap': args.policy_max_action_step, 'settled_contact': args.settled_contact, 'wait_force_n': args.wait_force_n, 'wait_force_side': args.wait_force_side})
    report = audit_rollout(task_id, episode.q, episode.action, trace, idle=args.idle, require_zero_action=not bool(args.policy_port))
    if task_id != 'wait_no_package':
        for key in ('box', 'mailer'):
            drift = float(np.linalg.norm(np.asarray(initial[key])[:2] - np.asarray(layout[key + '_xyz'])[:2]))
            report['metrics'][key + '_reset_drift_m'] = drift
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
    (folder / 'expert_control.json').write_text(json.dumps(expert_control, indent=2))
    if args.wait_force_n:
        (folder / 'external_force.json').write_text(json.dumps(force_log, indent=2))
    if args.policy_port:
        (folder / 'policy_inferences.json').write_text(json.dumps(infer_log))
        requested = np.asarray(raw_policy_actions)
        np.savez_compressed(folder / 'policy_raw_actions.npz', action=requested)
        report['metrics']['raw_policy_max_action_step_rad'] = float(np.abs(np.diff(requested[:,12:], axis=0)).max())
        report['metrics']['policy_modified_frames'] = int(np.any(np.abs(requested[:,12:] - episode.action[:,12:]) > 1e-6, axis=1).sum())
        report['metrics']['max_policy_action_modification_rad'] = float(np.abs(requested[:,12:] - episode.action[:,12:]).max())
    (folder / 'reset_contacts.json').write_text(json.dumps(reset_trace, indent=2))
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
    (root / 'STATUS.json').write_text(json.dumps({'training_ready': False, 'status': 'collecting_diagnostics'}))
    paths = [Path(__file__).resolve(), ROOT / 'simfoundry/data/paired_sorting.py', ROOT / 'simfoundry/robots/g1_assets.py', ROOT / 'simfoundry/data/sorting_cartesian_expert.py']
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
            layout = sample_layout(i)
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
