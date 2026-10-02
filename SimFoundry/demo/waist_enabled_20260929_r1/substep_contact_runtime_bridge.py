"""Prospective diagnostic bridge; not installed into any current collector.
Setup reads model metadata once. Callbacks only enqueue the installed read-only
contact decoder and independent snapshot kernels. No physics refresh or controls.
Actual GPU graph/runtime validation is still required before adoption.
"""
import numpy as np
import warp as wp
from mujoco_warp._src.support import contact_force
from substep_contact_observer_prototype import SubstepBuffers

class SubstepContactBridge:
    def __init__(self,manager,*,control_decimation,fixture_cpu=False):
        if type(control_decimation) is not int or control_decimation<1:
            raise ValueError('Explicit control decimation required')
        if manager._graph is not None:
            raise ValueError('Must install before initial graph capture; never recapture')
        solver=manager._solver
        if solver.use_mujoco_cpu or not manager._use_single_state or solver.update_data_interval!=1:
            raise ValueError('Requires single-state Warp backend and update_data_interval=1')
        data=solver.mjw_data;model=manager.get_model();state=manager.get_state_0()
        device=data.contact.pos.device
        if not device.is_cuda and not fixture_cpu:
            raise ValueError('Production bridge requires CUDA; CPU is fixture-only')
        if fixture_cpu and device.is_cuda:
            raise ValueError('CPU fixture may not allocate on GPU')
        if type(manager._num_substeps) is not int or manager._num_substeps<1:
            raise ValueError('Invalid substep count')
        all_graphable=manager._is_all_graphable()
        if all_graphable and manager._decimation!=control_decimation:
            raise ValueError('Manager/control decimation mismatch')
        shape_body=model.shape_body.numpy();labels=list(model.shape_label)
        mask=np.array([int('/parcel_box/' in s or '/mailer/' in s) for s in labels],dtype=np.int32)
        bodies=[]
        for token in ['/parcel_box/','/mailer/']:
            found={int(shape_body[i]) for i,s in enumerate(labels) if token in s}
            if len(found)!=1 or min(found)<0:
                raise ValueError('Exactly one dynamic body per parcel required')
            bodies.append(found.pop())
        if len(set(bodies))!=2 or max(bodies)>=state.body_q.shape[0]:
            raise ValueError('Parcel body identity mismatch')
        masses=model.body_mass.numpy()[bodies];com=model.body_com.numpy()[bodies];inertia=model.body_inertia.numpy()[bodies]
        if not all(np.isfinite(x).all() for x in [masses,com,inertia]) or not np.all(masses>0):
            raise ValueError('Invalid physical parcel mass/COM/inertia')
        self.manager=manager;self.solver=solver;self.data=data;self.device=device
        self.control_decimation=control_decimation;self.all_graphable=all_graphable
        self.expected_substeps=control_decimation*manager._num_substeps
        self.expected_manager_steps=1 if all_graphable else control_decimation
        if self.expected_substeps!=24:
            raise ValueError('Current prospective protocol requires exactly24 solver substeps/control')
        self.buffers=SubstepBuffers(device=device,body_ids=bodies,shape_is_target=mask,contact_capacity=int(data.naconmax),capacity=self.expected_substeps+self.expected_manager_steps)
        self.ids=wp.array(np.arange(data.naconmax,dtype=np.int32),dtype=int,device=device)
        self.forces=wp.zeros(data.naconmax,dtype=wp.spatial_vector,device=device)
        self._installed=False;self.fixture_cpu=fixture_cpu
        self.metadata=dict(body_ids=bodies,body_labels=[model.body_label[i] for i in bodies],body_mass_kg=masses.tolist(),body_com_local=com.tolist(),body_inertia_local=inertia.tolist(),shape_body=shape_body.tolist(),shape_labels=labels,geom_to_shape=solver.mjc_geom_to_newton_shape.numpy().tolist(),solver_dt_s=float(manager._solver_dt),control_decimation=control_decimation,substeps_per_physics_tick=manager._num_substeps,expected_substeps=self.expected_substeps,expected_manager_steps=self.expected_manager_steps,all_graphable=all_graphable,fixture_cpu=fixture_cpu,training_ready=False,force_timing='Most recently completed solve; tick0 precedes current action integration. End-state pose may differ from force-evaluation pose. Boundary duplicates are retained explicitly.')

    def install(self):
        if self._installed or self.manager._graph is not None:
            raise ValueError('Already installed or graph already captured')
        self.manager.register_state_force_callback(self._pre)
        self.manager.register_post_step_callback(self._post)
        self._installed=True

    def _capture(self,kind,state):
        # No numpy readback, array allocation, forward(), reset(), or force write.
        with wp.ScopedDevice(self.device):
            contact_force(self.solver.mjw_model,self.data,self.ids,True,self.forces)
            self.buffers.capture(kind,state_q=state.body_q,state_qd=state.body_qd,nacon=self.data.nacon,geom=self.data.contact.geom,world=self.data.contact.worldid,mapping=self.solver.mjc_geom_to_newton_shape,positions=self.data.contact.pos,world_forces=self.forces)

    def _pre(self,state):
        self._capture(0,state)

    def _post(self):
        self._capture(1,self.manager.get_state_0())

    def begin(self,action_step):
        if not self._installed:
            raise ValueError('Observer not installed')
        if self.manager._solver is not self.solver or self.manager._is_all_graphable()!=self.all_graphable or self.manager._num_substeps*self.control_decimation!=self.expected_substeps:
            raise ValueError('Runtime schedule/solver changed')
        if self.all_graphable and self.manager._decimation!=self.control_decimation:
            raise ValueError('Runtime decimation changed')
        self.buffers.begin(action_step)

    def finish(self):
        return self.buffers.finish(expected_substeps=self.expected_substeps,expected_manager_steps=self.expected_manager_steps)
