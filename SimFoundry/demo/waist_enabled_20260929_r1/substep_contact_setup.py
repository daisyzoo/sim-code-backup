"""Install a prospective independent observer before first scene graph capture."""
from pathlib import Path
import hashlib,json,inspect
from substep_contact_runtime_bridge import SubstepContactBridge

def install_observer(env,cfg,root):
    from isaaclab_newton.physics.newton_manager import NewtonManager
    from isaaclab_newton.physics import mjwarp_manager
    from mujoco_warp._src import support
    import substep_contact_runtime_bridge,substep_contact_observer_prototype,substep_contact_recording
    if cfg.scene.num_envs!=1 or cfg.sim.physics.num_substeps!=3 or cfg.sim.physics.use_cuda_graph is not True:
        raise ValueError('Observer protocol requires original single-world CUDA graph configuration')
    bridge=SubstepContactBridge(NewtonManager,control_decimation=int(cfg.decimation))
    if abs(float(cfg.sim.dt)*int(cfg.decimation)-1/15)>1e-12 or abs(bridge.metadata['solver_dt_s']-1/360)>1e-12:
        raise ValueError('Unexpected actual solver/control timestep')
    # No callbacks are registered until the runtime metadata is fully validated.
    if len(bridge.metadata['geom_to_shape'])!=1:raise ValueError('Single world required')
    root=Path(root);archive=root/'substep_runtime_sources';archive.mkdir(exist_ok=False)
    sources={}
    for source in [Path(__file__),Path(inspect.getfile(NewtonManager)),Path(inspect.getfile(type(NewtonManager._solver))),Path(mjwarp_manager.__file__),Path(support.__file__),Path(substep_contact_runtime_bridge.__file__),Path(substep_contact_observer_prototype.__file__),Path(substep_contact_recording.__file__)]:
        content=source.read_bytes();h=hashlib.sha256(content).hexdigest();dest=archive/(h+'_'+source.name);dest.write_bytes(content);sources[str(source)]=dict(sha256=h,snapshot=str(dest.relative_to(root)))
    bridge.install();env._substep_contact_bridge=bridge
    (root/'SUBSTEP_RUNTIME_BINDING.json').write_text(json.dumps(dict(observer_installed=True,metadata=bridge.metadata,source_files=sources,original_graph_setting=True,training_ready=False,actual_substep_count_verified=False),indent=2))
    return bridge
