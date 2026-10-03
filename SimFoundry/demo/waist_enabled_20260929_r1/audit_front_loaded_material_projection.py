"""Independent material-cap geometry, eligibility and emitted-history verification.
The caller must verify native initial-front events and source binding first.
This checker does not import the cap, adapter, controller, or contact reader.
Parent COP waypoints must be independently reconstructed by the enclosing audit.
"""
import numpy as np
from scipy.spatial.transform import Rotation
from front_initial_center_reference_ledger import verified_reference_lifetimes
from front_loaded_projection_independent_math import verify as verify_projection


def close(actual, expected, tolerance=1e-10):
    a,b=np.asarray(actual,dtype=float),np.asarray(expected,dtype=float)
    assert a.shape==b.shape and np.isfinite(a).all() and np.isfinite(b).all()
    assert np.max(abs(a-b),initial=0.)<=tolerance,(actual,expected,tolerance)


class MaterialCapAudit:
    def __init__(self, rows, plan, target, quats, packets, key, q, hand,
                 verified_front_events, *, enabled):
        assert type(enabled) is bool
        self.rows={r['step']:r for r in rows};assert list(self.rows)==list(range(1,len(rows)+1))
        self.selected=bool(plan.get('front_route_selected'))
        self.enabled=enabled;self.active={};self.checked={};self.records=[]
        if not (enabled and self.selected):
            assert all('loaded_reference_cap' not in r for r in rows)
            return
        ledger=verified_reference_lifetimes(rows,verified_front_events)
        capture=ledger['handover_step'];side='right' if key=='box' else 'left';actor='parcel_box' if key=='box' else 'mailer'
        size=np.asarray(plan['top_recontact']['contact_size_xyz'],dtype=float)
        # Existing parent surface uses nominal size; landing/edge planning uses
        # separately audited physical core size. Never conflate these models.
        close(size,[.14,.09,.045] if key=='box' else [.15,.145,.04],0.)
        fraction=plan['top_recontact']['effective_top_fraction']
        assert not plan['top_recontact']['visible_corner'] and not plan['contact_center_calibration']['enabled']
        for row in rows:
            t=row['step'];a=row['loaded_reference_cap'];r=Rotation.from_quat(quats[t]).as_matrix()
            assert a['scope']=='post_COP_before_action'
            captured=capture is not None and t>=capture
            assert a['capture_step']==(capture if captured else None)
            guarded=bool(row.get('route_stop_reason') or row.get('release_reason'))
            assert a['parent_guard_precedence'] is guarded
            parent=np.asarray(a['parent_target_xyz'],dtype=float);assert parent.shape==(3,) and np.isfinite(parent).all()
            close(parent[2],row['target_xyz'][2],0.)
            # Force on parcel: packet sign belongs to slot1; sum normal contacts
            # above the unchanged original .05N per-contact threshold.
            packet=packets[t-1];assert packet['after_action_step']==t-1
            close(packet['post_action_pose'][key],target[t],2e-6)
            normal=0.
            for contact in packet['parcel_contacts']:
                slots=[j for j,label in enumerate(contact['shapes']) if '/'+actor+'/' in label]
                if len(slots)!=1 or not any(side+'_wrist' in label for label in contact['shapes']):continue
                f=np.asarray(contact['force_world_N'])*(1. if slots[0]==1 else -1.)
                load=-float(np.dot(f,r[:,2]));assert np.isfinite(load)
                if load>.05:normal+=load
            eligible=captured and not guarded and row['mode']=='top_push' and normal>=.3
            assert a['requires_recontact'] is False,'A complete emitted stream cannot include a rejected empty intersection'
            if not eligible:
                reason='no_actual_initial_capture' if not captured else 'original_non_push_mode' if guarded or row['mode']!='top_push' else 'original_unloaded_parent'
                assert a['applied'] is False and a['changed'] is False and a['reason']==reason
                close(a['command_xy'],parent[:2],0.);close(parent,row['target_xyz'],0.)
                self.records.append(dict(step=t,eligible=False,reason=reason));continue
            assert a['applied'] is True and a['reason']=='bounded_material_reference'
            assert a['cap_xy_m']==.010 and a['original_step_m']==.003 and a['original_hand_lead_m']==.030
            close(a['normal_load_n'],normal,2e-6)
            # Derive current material surface from measured parcel pose and the
            # independently verified surface-reset ledger, never cap metadata.
            local=np.array([0.,0.,size[2]/2]);axis=int(np.argmax(abs(r[0,:2])))
            inset=.02 if fraction is None else fraction*size[axis]/2
            local[axis]=(-1 if r[0,axis]>=0 else 1)*(size[axis]/2-inset)
            if t in ledger['surface_local_by_step']:local[:2]=ledger['surface_local_by_step'][t]
            surface=np.asarray(target[t])+r@local
            close(row['observed_target'],target[t],1e-7);close(row['parcel_top_xyz'],surface,1e-7)
            # Independently rebuild the observed supporting-plane reference
            # with URDF FK and archived physical hull vertices.
            pose=hand.fk(q[t],side);local_normal=pose[:3,:3].T@r[:,2];center=np.asarray(ledger['centers'][t]);vertices=hand.vertices[side]
            heights=[float(v@local_normal) for v in vertices]
            offset=center+local_normal*(min(heights)-float(center@local_normal))
            reference=pose[:3,3]+pose[:3,:3]@offset
            close(row['control_offset_local'],offset,2e-6);close(row['observed_support_xyz'],reference,2e-6)
            # Compare exact solver arithmetic to the bound observations. FK
            # independently constrains their pre-existing measurement tolerance.
            obs_ref=np.asarray(row['observed_support_xyz'][:2]);obs_surface=np.asarray(row['parcel_top_xyz'][:2])
            previous=np.asarray(self.rows[t-1]['target_xyz'][:2])
            close(a['previous_command_xy'],previous,0.);close(a['reference_xy'],obs_ref,0.);close(a['material_surface_xy'],obs_surface,0.)
            close(a['parent_xy'],parent[:2],0.)
            assert np.max(abs(parent[:2]-previous))<=.003+1e-10
            # Scalar projection verifier is separate from production code.
            checked=verify_projection(a,parent=parent[:2].tolist(),previous=previous.tolist(),reference=obs_ref.tolist(),material=obs_surface.tolist(),normal=normal)
            assert checked['feasible'],'A genuinely empty set must stop before action'
            expected=np.asarray(checked['command_xy'])
            close(row['target_xyz'][:2],expected)
            self.active[t]=dict(parent_xy=parent[:2].copy(),final_xy=expected,normal=normal,previous_xy=previous)
            self.records.append(dict(step=t,eligible=True,changed=a['changed'],normal_load_n=normal,material_offset_xy_m=(expected-obs_surface).tolist()))

    def verify_parent_waypoint(self, step, row, independently_reconstructed_parent, previous, normal):
        """Called by original independent COP math before actual-waypoint check."""
        expected=np.asarray(independently_reconstructed_parent,dtype=float)
        if step in self.active:
            a=self.active[step];close(expected,a['parent_xy'],2e-6);close(previous,a['previous_xy'],1e-10);close(normal,a['normal'],2e-6)
            assert step not in self.checked;self.checked[step]=True
            return a['final_xy'].copy()
        if self.enabled and self.selected:
            close(row['loaded_reference_cap']['parent_target_xyz'][:2],expected,2e-6)
        return expected

    def finish(self):
        assert set(self.checked)==set(self.active),'Every capped waypoint requires independent parent-COP reconstruction'
        return dict(passed=True,enabled=self.enabled,selected=self.selected,rows_checked=len(self.records),loaded_rows=len(self.active),changed_rows=sum(r.get('changed',False) for r in self.records),records=self.records,training_ready=False)
