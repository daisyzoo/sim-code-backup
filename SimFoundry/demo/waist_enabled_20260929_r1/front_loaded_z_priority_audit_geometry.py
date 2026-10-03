"""Pure independent geometry extracted unchanged from the archived offline audit.
No candidate runtime/solver imports and no import-time episode execution.
"""
import numpy as np
from support_vertex_stationarity import certificate

def evaluate(a, c, x, parent, hand, elbows, g, side):
    x = np.asarray(x, float)
    if x.shape != (11,) or not np.isfinite(x).all():
        return dict(passed=False, reason='nonfinite_or_wrong_shape')
    q = np.asarray(a['current'])
    J = np.asarray(a['jacobian'])
    e = np.asarray(a['error'])
    prior = np.asarray(a['preferred_step'])
    D = np.asarray(a['damping']) ** 2
    zr = 5 if side == 'right' else 2
    d = x - q
    dp = parent - q
    target = np.array(c['contact_normal_tracking']['target_local_up'])
    target /= np.linalg.norm(target)
    A = J[6:]
    v = e[6:]
    r = A @ d - v
    pn = float(np.linalg.norm(A @ dp - v))
    rn = float(np.linalg.norm(r))
    ze = float(J[zr] @ d - e[zr])
    h = 2e-07

    def exact(z):
        return float(np.linalg.norm(hand.fk(z, side)[:3, :3][2] - target))
    pe = exact(parent)
    ce = exact(x)
    gx = np.array([-(exact(x + np.eye(11)[j] * h) - exact(x - np.eye(11)[j] * h)) / (2 * h) for j in range(11)])
    vals = np.array([ze, -ze, pn - rn, pe - ce])
    jac = np.vstack([J[zr], -J[zr], -r @ A / max(rn, 1e-15), gx])
    lo = np.maximum.reduce([a['lower'], q - a['step_limits'], np.asarray(a['previous']) - 0.055])
    hi = np.minimum.reduce([a['upper'], q + a['step_limits'], np.asarray(a['previous']) + 0.055])
    grad = J.T @ (J @ d - e) + D * (d - prior)
    cert = certificate(geometry=elbows, x=x, gradient=grad, lower=lo, upper=hi, extra_values=vals, extra_jacobian=jac)
    table = g.table_margins(g.fk(x))
    return dict(passed=bool(cert['passed'] and min(table) >= 0 and (abs(ze) <= 2e-07) and (ce <= pe + 1e-06) and (rn <= pn + 2e-07)), certificate=cert, nominal_table_margins_m=table, z_error_mm=ze * 1000, exact_attitude_delta=ce - pe, linear_attitude_delta_mm=(rn - pn) * 1000)

def point(model, q, side, normal, center):
    M = model.fk(q, side)
    local = M[:3, :3].T @ normal
    vertices = model.vertices[side]
    offset = center + local * (np.min(vertices @ local) - center @ local)
    return M[:3, 3] + M[:3, :3] @ offset

def radii(hand, side):
    chain = hand.chains[side]
    out = np.zeros(11)
    extent = float(np.linalg.norm(hand.vertices[side], axis=1).max())
    for k, (_, axis, i) in enumerate(chain):
        if i is not None:
            assert abs(np.linalg.norm(axis) - 1) < 1e-09
            out[i] = extent + sum((np.linalg.norm(O[:3, 3]) for O, _, _ in chain[k + 1:]))
    return out

def sweep(g, hand, q, x, side, xyz, rotation, size):
    travel = float(radii(hand, side) @ abs(x - q))
    intervals = [(0.0, 1.0, 0)]
    leaves = []
    samples = []
    while intervals:
        a, b, depth = intervals.pop()
        m = (a + b) / 2
        pose = g.fk(q + (x - q) * m)
        gap = g.hand_box_gap(pose, side, xyz, rotation, size)
        lower = gap - travel * (b - a) / 2
        samples.append(dict(fraction=m, gap_m=gap, interval=[a, b], lower_bound_m=lower))
        if lower > 0:
            leaves.append(lower)
            continue
        if gap <= 0 or depth >= 12:
            return dict(certified=False, reason='sample_has_no_separation_witness' if gap <= 0 else 'subdivision_limit', travel_bound_m=travel, samples=samples)
        intervals.extend([(a, m, depth + 1), (m, b, depth + 1)])
    return dict(certified=True, minimum_certified_gap_lower_bound_m=min(leaves), travel_bound_m=travel, samples=samples)
