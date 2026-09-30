import unittest
from pxr import Usd,UsdGeom,UsdPhysics,Gf
from simfoundry.data.parcel_collision_geometry import read_parcel_collision_geometry

class ParcelCollisionGeometryTests(unittest.TestCase):
    def stage(self):
        stage=Usd.Stage.CreateInMemory();root=UsdGeom.Xform.Define(stage,'/parcel');root.AddTranslateOp().Set(Gf.Vec3d(.6,.2,.77));root.AddRotateZOp().Set(43.)
        core=UsdGeom.Cube.Define(stage,'/parcel/core');core.CreateSizeAttr(1.);core.AddScaleOp().Set(Gf.Vec3f(.135,.1276,.04));UsdPhysics.CollisionAPI.Apply(core.GetPrim());core.CreateVisibilityAttr().Set(UsdGeom.Tokens.invisible)
        shell=UsdGeom.Cube.Define(stage,'/parcel/shell');shell.CreateSizeAttr(1.);shell.AddScaleOp().Set(Gf.Vec3f(.15,.145,.04))
        return stage
    def test_hidden_core_not_larger_visual_shell_and_root_rotation_removed(self):
        result=read_parcel_collision_geometry(self.stage(),'/parcel',(.135,.1276,.04))
        for a,b in zip(result['collision_core_size_xyz'],(.135,.1276,.04)):self.assertAlmostEqual(a,b,places=6)
        self.assertEqual(result['collider_path'],'/parcel/core')
    def test_inconsistent_spawn_size_rejected(self):
        with self.assertRaises(ValueError):read_parcel_collision_geometry(self.stage(),'/parcel',(.15,.145,.04))
    def test_multiple_collision_cores_rejected(self):
        stage=self.stage();UsdPhysics.CollisionAPI.Apply(stage.GetPrimAtPath('/parcel/shell'))
        with self.assertRaises(ValueError):read_parcel_collision_geometry(stage,'/parcel')
