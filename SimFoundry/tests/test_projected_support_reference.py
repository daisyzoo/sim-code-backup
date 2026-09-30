import unittest
import numpy as np
from scipy.spatial.transform import Rotation
from simfoundry.data.projected_support_reference import projected_support_reference,projected_support_jacobian

class ProjectedSupportTests(unittest.TestCase):
    def setUp(self):
        self.v=np.array([[x,y,z] for x in (-.08,.08) for y in (-.03,.03) for z in (-.02,.02)])
    def test_exact_lowest_plane_and_center_tangent(self):
        r=Rotation.from_euler('xyz',[.3,.6,.2]).as_matrix();n=Rotation.from_euler('xy',[.1,.2]).apply([0,0,1])
        ref=projected_support_reference(self.v,r,n);p=r@ref['reference_local'];center=r@ref['center_local']
        self.assertAlmostEqual(p@n,min((self.v@r.T)@n))
        np.testing.assert_allclose((np.eye(3)-np.outer(n,n))@(p-center),0,atol=1e-12)
    def test_reference_continuous_at_vertex_switch(self):
        a=projected_support_reference(self.v,Rotation.from_rotvec([0,-1e-7,0]).as_matrix(),np.array([0,0,1]))
        b=projected_support_reference(self.v,Rotation.from_rotvec([0,1e-7,0]).as_matrix(),np.array([0,0,1]))
        self.assertGreater(np.linalg.norm(a['lowest_vertex_local']-b['lowest_vertex_local']),.1)
        self.assertLess(np.linalg.norm(a['reference_local']-b['reference_local']),1e-7)
    def test_hybrid_jacobian_matches_finite_difference(self):
        rng=np.random.default_rng(619);r=Rotation.from_rotvec([.4,.2,.1]).as_matrix();n=np.array([0,0,1.]);jl=rng.normal(size=(3,11));jw=rng.normal(size=(3,11))
        ref=projected_support_reference(self.v,r,n);j=projected_support_jacobian(jl,jw,r,ref);eps=1e-7
        for i in range(11):
            rp=Rotation.from_rotvec(jw[:,i]*eps).as_matrix()@r;rm=Rotation.from_rotvec(-jw[:,i]*eps).as_matrix()@r
            a=projected_support_reference(self.v,rp,n);b=projected_support_reference(self.v,rm,n)
            fd=(jl[:,i]*2*eps+rp@a['reference_local']-rm@b['reference_local'])/(2*eps)
            np.testing.assert_allclose(j[:,i],fd,atol=1e-8)
    def test_invalid_normal_rejected(self):
        with self.assertRaises(ValueError):projected_support_reference(self.v,np.eye(3),[0,0,2])

if __name__=='__main__':unittest.main()
