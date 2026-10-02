"""Unwired first-front-only measured landing lifecycle, default off.
Parent guards must run first. First command commits to this path: subsequent
rejection stops explicitly. No parcel mutation or contact-force substitution.
"""
import numpy as np
from front_initial_center_plan import checked_scene
from front_initial_center_selection import plan
from front_initial_center_tracking import propose
from simfoundry.data.projected_support_reference import projected_support_reference


class FrontInitialCenterLifecycle:
    def __init__(self, *, enabled=False, maximum_ticks=240):
        if type(enabled) is not bool or type(maximum_ticks) is not int or maximum_ticks != 240:
            raise ValueError('Invalid explicit initial landing configuration')
        self.enabled = enabled
        self.maximum_ticks = maximum_ticks
        self.active = self.attempted = self.finished = False
        self.index = self.ticks = self.ready = 0
        self.plan = self.scene = self.failure = self.last_step = None

    def stop(self, reason, **evidence):
        self.active = False
        self.failure = reason
        return dict(kind='stop', requires_stop=True, reason=reason, **evidence)

    def update(self, *, step, selected, parent_mode, recontacts, guard_stop,
               observed_load_n, filtered_load_n, scene, current, previous_q,
               previous_command, decay, observed_hand_pose, observed_inactive_hand_pose):
        if not self.enabled:
            return dict(kind='unchanged', reason='disabled')
        if self.failure is not None:
            return dict(kind='stop', requires_stop=True, reason=self.failure)
        if self.finished:
            return dict(kind='unchanged', reason='initial_handover_already_complete')
        if (type(selected) is not bool or type(guard_stop) is not bool or
                type(step) is not int or step < 1 or type(recontacts) is not int or recontacts < 0):
            raise ValueError('Invalid initial landing context')
        eligible_phase = selected and recontacts == 0 and parent_mode in ('top_cross', 'top_descend') and not guard_stop
        if not self.active and not eligible_phase:
            return dict(kind='unchanged', reason='not_initial_front_unloaded_phase')
        q = np.asarray(current, float)
        if q.shape != (11,) or not np.isfinite(q).all():
            raise ValueError('Invalid measured state')
        poses = [np.asarray(p, float) for p in [observed_hand_pose, observed_inactive_hand_pose]]
        for side, pose in zip([scene.side, scene.inactive], poses):
            nominal = scene.guard.model.fk(side, q)[0]
            if pose.shape != (4, 4) or not np.isfinite(pose).all() or np.max(abs(pose-nominal)) > 1e-4:
                raise ValueError('Measured hand pose differs from actual q model')
        if not np.isfinite(observed_load_n) or not np.isfinite(filtered_load_n):
            raise ValueError('Nonfinite measured contact')
        unloaded = observed_load_n == 0. and 0. <= filtered_load_n <= .05
        context = dict(step=step, selected=selected, parent_mode=parent_mode, recontacts=recontacts,
                       guard_stop=guard_stop, observed_load_n=float(observed_load_n),
                       filtered_load_n=float(filtered_load_n), current=q.tolist(),
                       previous_q=np.asarray(previous_q).tolist(), previous_command=np.asarray(previous_command).tolist(),
                       decay=np.asarray(decay).tolist(), observed_hand_pose=poses[0].tolist(),
                       observed_inactive_hand_pose=poses[1].tolist(), scene=scene.record())
        created = None
        if not self.active:
            if self.attempted or not unloaded:
                return dict(kind='unchanged', reason='no_new_unloaded_initial_attempt', context=context)
            self.attempted = True
            created = plan(scene, q, step=step, previous_q=previous_q, previous_command=previous_command, decay=decay)
            if not created['accepted']:
                return dict(kind='unchanged', reason='no_verified_initial_plan', planning=created, context=context)
            self.plan, self.scene = created, scene
            self.active = True
        if not eligible_phase or not unloaded:
            return self.stop('parent_guard_phase_or_contact_changed', context=context)
        if self.last_step is not None and step != self.last_step+1:
            return self.stop('nonconsecutive_observation', context=context)
        self.last_step = step
        moved = scene.moved_since(self.scene)
        if moved['changed']:
            return self.stop('object_pose_changed_during_path', motion=moved, context=context)
        if self.ticks >= self.maximum_ticks:
            return self.stop('initial_front_path_budget_exhausted', context=context)
        if np.max(abs(q-np.asarray(self.plan['waypoints'][self.index]))) <= .003 and self.index < len(self.plan['waypoints'])-1:
            self.index += 1
        command, record = propose(enabled=True, selected=selected, mode='top_cross', recontacts=recontacts,
                                  observed_load_n=observed_load_n, filtered_load_n=filtered_load_n,
                                  current=q, previous_q=previous_q, previous_command=previous_command,
                                  waypoint=self.plan['waypoints'][self.index], decay=decay, guard=scene.guard,
                                  scene_check=lambda x: checked_scene(scene, x))
        if command is None:
            return self.stop('no_verified_initial_front_command', proposal=record, context=context, planning=created)
        self.ticks += 1
        pose, inactive_pose = poses
        vertices = scene.guard.model.vertices[scene.side]
        R = pose[:3, :3]
        points = (vertices@R.T + pose[:3, 3]-scene.target)@scene.rotation
        ix = int(points[:, 2].argmin())
        point = points[ix]
        alignment = abs(scene.rotation[:, 2]@R@np.asarray(self.plan['thin_axis_local']))
        endpoint_close = np.max(abs(q-np.asarray(self.plan['endpoint']))) <= .003
        physical_ready = bool(endpoint_close and max(abs(point[:2])) <= .002+2e-7
                              and np.min(scene.core[:2]/2-abs(point[:2])) >= .01
                              and .004 <= point[2]-scene.core[2]/2 <= .01 and alignment >= .8-2e-7
                              and np.all(q >= scene.guard.lower-2e-7) and np.all(q <= scene.guard.upper+2e-7)
                              and checked_scene(scene, q)['accepted'])
        self.ready = self.ready+1 if physical_ready else 0
        result = dict(kind='command', command=command.tolist(), proposal=record, context=context,
                      waypoint_index=self.index, ticks=self.ticks, measured_ready_count=self.ready,
                      actual_lowest_local=point.tolist(), actual_alignment_abs=float(alignment), ready_numerical_tolerance=2e-7, planning=created)
        if self.ready >= 3:
            center = vertices[ix]
            reference = projected_support_reference(vertices, R, scene.rotation[:, 2], center_local=center)
            measured = pose[:3, 3]+R@reference['reference_local']
            local = scene.rotation.T@(measured-scene.target)
            if np.max(abs(local-point)) > 1e-8:
                raise ValueError('Captured support differs from measured physical lowest vertex')
            result.update(kind='handover', captured_center_local=center.tolist(),
                          captured_inactive_anchor_world=(inactive_pose[:3, 3]+inactive_pose[:3, :3]@np.array([.20, 0, .007])).tolist(),
                          captured_normal_local_up=(R.T@np.array([0., 0., 1.])).tolist(),
                          selected_surface_local_xy=local[:2].tolist(), observed_support_xyz=measured.tolist(),
                          reference={k: reference[k].tolist() for k in ('reference_local', 'center_local', 'lowest_vertex_local', 'world_normal')},
                          handover_scope='Actual three consecutive observations only; caller must capture reference, surface, normal and inactive anchor, reset loading/XY history, and retain original front guards.')
            self.active = False
            self.finished = True
        return result
