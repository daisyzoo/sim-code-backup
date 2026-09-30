import unittest
from simfoundry.data.object_relative_push import object_relative_push_xy


class ObjectRelativePushTests(unittest.TestCase):
    def test_static_object_does_not_integrate_hand_slip(self):
        previous=(.4,.12)
        for _ in range(1000):
            previous, desired=object_relative_push_xy((.4,.12),(0,0),(.37,-.205),previous)
        self.assertEqual(previous,desired)
        self.assertAlmostEqual(previous[0],.388)
        self.assertAlmostEqual(previous[1],.108)

    def test_anchor_and_target_translation_are_preserved(self):
        anchor=(-.003,.002)
        a=object_relative_push_xy((.4,.1),anchor,(.37,-.205),(.4,.1))[1]
        b=object_relative_push_xy((.41,.11),anchor,(.38,-.195),(.41,.11))[1]
        for x,y in zip(a,b): self.assertAlmostEqual(y-x,.01)

    def test_mirror_is_symmetric(self):
        a=object_relative_push_xy((.4,.12),(-.002,.003),(.37,-.205),(.399,.12))
        b=object_relative_push_xy((.4,-.12),(-.002,-.003),(.37,.205),(.399,-.12))
        for x,y in zip(a,b):
            self.assertEqual(x[0],y[0]);self.assertEqual(x[1],-y[1])

    def test_recovering_excess_drift_obeys_slew(self):
        previous=(.32,.02)
        command,desired=object_relative_push_xy((.4,.12),(0,0),(.37,-.205),previous)
        for i in (0,1):
            self.assertLessEqual(abs(command[i]-previous[i]),.0030000001)
            self.assertLess(abs(command[i]-desired[i]),abs(previous[i]-desired[i]))

    def test_hold_axis_and_near_goal_do_not_overshoot(self):
        _,desired=object_relative_push_xy((.4,-.2),(-.002,.003),(.4,-.205),(.4,-.2))
        self.assertAlmostEqual(desired[0],.398)
        self.assertAlmostEqual(desired[1],-.202)

    def test_invalid_inputs_rejected(self):
        for kw in ({'lead_m':.013},{'step_m':0},{'lead_m':float('nan')}):
            with self.assertRaises(ValueError): object_relative_push_xy((.4,.12),(0,0),(.37,-.205),(.4,.12),**kw)
        with self.assertRaises(ValueError): object_relative_push_xy((float('nan'),.12),(0,0),(.37,-.205),(.4,.12))


if __name__=='__main__': unittest.main()
