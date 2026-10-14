"""Contact evidence against actual scene colliders; no fallback floor."""
def test_contacts(app,stage,cfg,targets):
    import numpy as np
    import omni.physx
    import omni.timeline
    from pxr import Gf,Usd,UsdGeom,UsdPhysics,PhysicsSchemaTools,PhysxSchema
    from isaacsim.core.simulation_manager import SimulationManager as Sim
    Sim.switch_physics_engine('physx')
    assert Sim.get_active_physics_engine()=='physx'
    Sim.setup_simulation(dt=cfg['physics']['dt'],device='cpu');Sim.enable_fabric(False)
    timeline=omni.timeline.get_timeline_interface();query=omni.physx.get_physx_scene_query_interface()
    timeline.play();app.update();Sim.step(steps=10)
    hits=[]
    for probe in cfg['physics']['probes']:
        hit=query.raycast_closest(tuple(probe['origin']),(0,0,-1),10)
        if not hit['hit'] or str(hit['collision']) not in targets:
            raise RuntimeError(f'No scene support for {probe}')
        hits.append((probe,list(hit['position']),str(hit['collision'])))
    timeline.stop();app.update();bodies=[]
    for i,(probe,(x,y,z),collider) in enumerate(hits):
        body=UsdGeom.Sphere.Define(stage,f'/World/Acceptance/Probe_{i}')
        body.CreateRadiusAttr(0.06);body.AddTranslateOp().Set(Gf.Vec3d(x,y,z+0.45))
        UsdPhysics.CollisionAPI.Apply(body.GetPrim());UsdPhysics.RigidBodyAPI.Apply(body.GetPrim())
        UsdPhysics.MassAPI.Apply(body.GetPrim()).CreateMassAttr(0.1)
        PhysxSchema.PhysxContactReportAPI.Apply(body.GetPrim()).CreateThresholdAttr(0)
        bodies.append(body)
    contacts={str(body.GetPath()):0 for body in bodies}
    def on_contacts(headers,data):
        for h in headers:
            paths=[str(PhysicsSchemaTools.intToSdfPath(h.collider0)),str(PhysicsSchemaTools.intToSdfPath(h.collider1))]
            if any(p in targets for p in paths):
                for p in paths:
                    if p in contacts:contacts[p]+=int(h.num_contact_data)
    subscription=omni.physx.get_physx_simulation_interface().subscribe_contact_report_events(on_contacts)
    timeline.play();app.update();trajectories=[[] for _ in bodies]
    for _ in range(24):
        Sim.step(steps=10);omni.physx.get_physx_interface().update_transformations(False,True,True,False)
        for body,trace in zip(bodies,trajectories):
            trace.append(list(UsdGeom.Xformable(body).ComputeLocalToWorldTransform(Usd.TimeCode.Default()).ExtractTranslation()))
    results=[]
    for body,(probe,hit,collider),trace in zip(bodies,hits,trajectories):
        end=trace[-1];support=[]
        def collect(h):
            if str(h.collision) in targets:support.append(float(h.position[2]))
            return True
        query.raycast_all((end[0],end[1],end[2]+0.1),(0,0,-1),10,collect)
        support_z=max(support) if support else None
        count=contacts[str(body.GetPath())]
        surface_ok='expected_z' not in probe or abs(hit[2]-probe['expected_z'])<probe.get('tolerance',0.1)
        passed=np.isfinite(trace).all() and count>0 and support_z is not None and abs(end[2]-support_z-0.06)<0.09 and hit[2]+0.45-end[2]>0.15 and surface_ok
        results.append({'name':probe['name'],'ray_origin':probe['origin'],'surface_xyz':hit,'collider':collider,
                        'final_xyz':end,'final_support_z':support_z,'mesh_contact_count':count,
                        'trajectory_every_10_steps':trace,'passed':bool(passed)})
    subscription=None;timeline.stop();app.update()
    for body in bodies:stage.RemovePrim(body.GetPath())
    return {'backend':'physx','device':'cpu','steps':240,'probes':results,'passed':all(x['passed'] for x in results)}
