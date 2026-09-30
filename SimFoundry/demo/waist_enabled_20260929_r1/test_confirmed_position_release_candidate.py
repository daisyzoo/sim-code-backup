import unittest
from confirmed_position_release_candidate import ConfirmedPositionRelease
class ReleaseCandidateTests(unittest.TestCase):
 def test_ten_samples_both_directions(self):
  for direction in (-1,1):
   c=ConfirmedPositionRelease(-direction*.12,direction)
   self.assertEqual([c.observe((.4,direction*.203,.77)) for _ in range(10)],[False]*9+[True])
 def test_boundary_recross_needs_new_ten_samples(self):
  c=ConfirmedPositionRelease(.12,-1)
  for _ in range(12):c.observe((.4,-.203,.77))
  self.assertFalse(c.observe((.4,-.199,.77)))
  self.assertEqual([c.observe((.4,-.203,.77)) for _ in range(10)],[False]*9+[True])
 def test_zone_without_progress_fails(self):
  c=ConfirmedPositionRelease(.18,1)
  self.assertFalse(any(c.observe((.4,.21,.77)) for _ in range(20)))
 def test_movement_without_stability_fails(self):
  c=ConfirmedPositionRelease(-.12,1)
  self.assertFalse(any(c.observe((.4+t*.002,.21,.77)) for t in range(30)))
 def test_wrong_side_fails(self):
  c=ConfirmedPositionRelease(.12,-1)
  self.assertFalse(any(c.observe((.4,.22,.77)) for _ in range(20)))
 def test_invalid_observation_rejected(self):
  c=ConfirmedPositionRelease(.12,-1)
  for value in [(0,float('nan'),.77),(0,float('inf'),.77),(0,0)]:
   with self.assertRaises(ValueError):c.observe(value)
if __name__=='__main__':unittest.main()
