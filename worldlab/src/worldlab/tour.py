"""Deterministic eye-level loop; yaw is unwrapped for a full turn."""
import math

# Fraction of one lap, eye XYZ, yaw degrees (0 = +Y), pitch degrees.
KEYFRAMES = (
    (0.00, (0.00, -1.00, 1.55),   0, -5),
    (0.13, (0.00,  0.30, 1.55),   0, -7),
    (0.26, (0.00,  1.00, 1.55), -55, -18),
    (0.37, (0.00,  1.10, 1.55),   0, -8),
    (0.49, (0.05,  0.85, 1.55),  65, -15),
    (0.62, (0.05,  0.50, 1.55), 145, -5),
    (0.74, (0.00, -0.20, 1.55), 205, -5),
    (0.87, (0.00, -1.00, 1.55), 285, -8),
    (1.00, (0.00, -1.00, 1.55), 360, -5),
)


def tour_pose(fraction):
    fraction = max(0.0, min(1.0, fraction))
    for a, b in zip(KEYFRAMES, KEYFRAMES[1:]):
        if fraction <= b[0]:
            t = (fraction - a[0]) / (b[0] - a[0])
            t = t * t * (3 - 2 * t)
            eye = [x + (y - x) * t for x, y in zip(a[1], b[1])]
            yaw = math.radians(a[2] + (b[2] - a[2]) * t)
            pitch = math.radians(a[3] + (b[3] - a[3]) * t)
            direction = (math.sin(yaw) * math.cos(pitch),
                         math.cos(yaw) * math.cos(pitch), math.sin(pitch))
            return eye, [x + d for x, d in zip(eye, direction)]
