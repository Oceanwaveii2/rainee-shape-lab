"""Experimental regional directional-crease lobe deformation (v5).

shared by Python/Houdini offline fitting and matched to houdini/curvilinear-rear-v5.mjs.
Fixes:
  D-01: Aligns intergluteal cleft to the true sculpted sulcus (X = +0.0122 H) on body-v4-rest.bin.
  D-02: Replaces collapsing inner monomial (sx/cs > 1) with C1 monotonic cubic Hermite expansion.
  D-03: Regularized dihedral V-cusp arc u*(2-u) with 96% sacral anchor hold.
  Winding helper is a radial-facing diagnostic proposal only; it does not certify
  orientation of a concave surface and is not automatically applied to geometry.
"""
import numpy as np
from rear_model import region, smooth, volume

V5_DEFAULTS = {
    'lateral': 1.08,
    'vertical': 1.04,
    'projection': 1.24,
    'separation': 0.26,
    'upper_pole': 1.35,       # Cantilevered sports-car dorsal launch shelf (alias upper_shelf)
    'lower_pole': 1.30,       # Aunt-Fanny teardrop lower pole overhang & tuck (alias lower_overhang)
    'cleft_hold': 0.96,       # 96% sacral anchor hold at true anatomical sulcus (alias cleft_cusp)
    'hip_flare': 1.15,        # Lateral Coke-bottle fender flare
    'roundness': 0.65,        # Cleft-gated curvilinear shell relaxation
    'cleft_x_offset': 0.0122  # True sculpted intergluteal sulcus X in body-v4-rest.bin
}

def _normalize_controls(controls=None):
    c = {**V5_DEFAULTS, **(controls or {})}
    if 'upper_shelf' in c:
        c['upper_pole'] = c['upper_shelf']
    if 'lower_overhang' in c:
        c['lower_pole'] = c['lower_overhang']
    if 'cleft_cusp' in c:
        c['cleft_hold'] = c['cleft_cusp']
    for name in V5_DEFAULTS:
        try:
            c[name] = float(c[name])
        except (TypeError, ValueError):
            raise ValueError(f'{name} must be a finite number') from None
        if not np.isfinite(c[name]):
            raise ValueError(f'{name} must be a finite number')
    if not 0 <= c['cleft_hold'] <= 1 or not 0 <= c['roundness'] <= 1:
        raise ValueError('cleft_hold and roundness must be in [0, 1]')
    if c['separation'] < 0 or any(c[k] <= 0 for k in ('lateral','vertical','projection','upper_pole','lower_pole','hip_flare')):
        raise ValueError('Expansion controls must be positive; separation must be nonnegative')
    return c

def _validate_points(v):
    v = np.asarray(v, dtype=np.float64)
    if v.ndim != 2 or v.shape[1] != 3 or not np.isfinite(v).all():
        raise ValueError('Expected finite XYZ point rows')
    return v

def _validate_amp(amp):
    amp = float(amp)
    if not np.isfinite(amp) or amp < 0:
        raise ValueError('Deformation amplitude must be finite and nonnegative')
    return amp

def _validate_steps(steps):
    if isinstance(steps, bool) or not isinstance(steps, (int, np.integer)) or not 1 <= steps <= 512:
        raise ValueError('RK4 steps must be an integer in [1, 512]')

def deform_v5_base(v, amp, controls=None, is_cage=False):
    c = _normalize_controls(controls)
    v = _validate_points(v)
    amp = _validate_amp(amp)
    if amp == 0.0:
        return v.copy()
    x0_cleft = 0.0 if is_cage else (
        c['cleft_x_offset'] * smooth(0.49, 0.56, v[:, 1]) * (1.0 - smooth(0.67, 0.72, v[:, 1]))
    )
    dx_cleft = v[:, 0] - x0_cleft
    ax = np.abs(dx_cleft)
    side = np.where(dx_cleft < 0.0, -1.0, 1.0)
    y = v[:, 1]
    z = v[:, 2]
    mask = region(v)

    eps_x = 0.0008
    u_cleft = np.clip((np.sqrt(ax * ax + eps_x * eps_x) - eps_x) / 0.046, 0.0, 1.0)
    cusp_arc = u_cleft * (2.0 - u_cleft)
    cleft = (1.0 - c['cleft_hold']) + c['cleft_hold'] * cusp_arc

    shelf_bell = smooth(0.590, 0.650, y) * (1.0 - smooth(0.667, 0.725, y))
    overhang_bell = smooth(0.495, 0.540, y) * (1.0 - smooth(0.570, 0.620, y))
    z_profile = (
        1.0
        + 0.35 * (c['upper_pole'] - 1.0) * shelf_bell
        + 0.40 * (c['lower_pole'] - 1.0) * overhang_bell
    )

    a = amp * mask * cleft
    lat_flare = 1.0 + 0.28 * (c['hip_flare'] - 1.0) * smooth(0.52, 0.63, y) * smooth(0.05, 0.14, ax)
    sx = 1.0 + a * c['lateral'] * lat_flare
    cs = 1.0 + a * c['separation']
    cx = 0.073

    t_x = np.minimum(ax / cx, 1.0)
    s0 = 1.0
    h01 = t_x * t_x * (3.0 - 2.0 * t_x)
    h10 = t_x * (1.0 - t_x) * (1.0 - t_x)
    h11 = t_x * t_x * (t_x - 1.0)
    terminal_slope = np.minimum(sx, 2.2 * cs)
    inner = cx * (cs * h01 + s0 * h10 + terminal_slope * h11)
    # The former inner clamp differed from the outer slope at cx. Match that
    # slope, then smoothly recover full outer expansion over 0.020 source H.
    outer_slope = terminal_slope + (sx - terminal_slope) * smooth(cx, cx + 0.020, ax)
    outer = cx * cs + (ax - cx) * outer_slope

    pole = c['lower_pole'] + (c['upper_pole'] - c['lower_pole']) * smooth(0.585, 0.625, y)
    droop = -0.016 * amp * mask * cusp_arc * overhang_bell * (c['lower_pole'] - 0.8)

    out = v.copy()
    out[:, 0] = x0_cleft + side * np.where(ax <= cx, inner, outer)
    out[:, 1] = y + a * (y - 0.605) * c['vertical'] * pole + droop
    out[:, 2] = z - a * (0.025 - z) * c['projection'] * z_profile
    out[mask == 0] = v[mask == 0]
    return out

def v5_relax_velocity(v, amp, controls=None, is_cage=False):
    c = _normalize_controls(controls)
    x0_cleft = 0.0 if is_cage else (
        c['cleft_x_offset'] * smooth(0.49, 0.56, v[:, 1]) * (1.0 - smooth(0.67, 0.72, v[:, 1]))
    )
    dx_cleft = v[:, 0] - x0_cleft
    side = np.where(dx_cleft < 0.0, -1.0, 1.0)
    ax = np.abs(dx_cleft)
    y = v[:, 1]
    z = v[:, 2]

    z_cantilever = -0.010 * amp * smooth(0.59, 0.66, y)
    center = np.column_stack((
        x0_cleft + side * (0.076 * (1.0 + amp * c['separation'])),
        np.full_like(y, 0.602),
        -0.046 - amp * 0.074 * c['projection'] + z_cantilever
    ))
    radii = np.array([
        0.091 * (1.0 + amp * c['lateral'] * c['hip_flare'] * 0.9),
        0.080 * (1.0 + amp * c['vertical'] * 0.5 * (c['upper_pole'] + c['lower_pole'])),
        0.095 * (1.0 + amp * c['projection'])
    ])
    q = (v - center) / radii
    rho = np.linalg.norm(q, axis=1)
    target = center + radii * q / np.maximum(rho[:, None], 1e-8)

    gate = (
        smooth(0.492, 0.540, y) * (1.0 - smooth(0.665, 0.725, y))
        * (1.0 - smooth(-0.045, 0.015, z))
        * smooth(0.036, 0.072, ax) * (1.0 - smooth(0.185, 0.218, np.abs(v[:, 0])))
        * smooth(0.25, 0.60, rho) * (1.0 - smooth(1.25, 1.65, rho))
    )
    return (target - v) * gate[:, None]

def deform_v5(v, amp, controls=None, steps=20, is_cage=False):
    v = _validate_points(v)
    amp = _validate_amp(amp)
    _validate_steps(steps)
    c = _normalize_controls(controls)
    out = deform_v5_base(v, amp, c, is_cage=is_cage)
    roundness = c['roundness']
    if amp == 0.0 or roundness == 0.0:
        return out
    duration = roundness * 3.8 * (1.0 - np.exp(-5.5 * amp))
    dt = duration / steps
    for _ in range(steps):
        k1 = v5_relax_velocity(out, amp, c, is_cage=is_cage)
        k2 = v5_relax_velocity(out + 0.5 * dt * k1, amp, c, is_cage=is_cage)
        k3 = v5_relax_velocity(out + 0.5 * dt * k2, amp, c, is_cage=is_cage)
        k4 = v5_relax_velocity(out + dt * k3, amp, c, is_cage=is_cage)
        out += (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
    active = region(v) > 0
    out[~active] = v[~active]
    return out

def calibrate_v5(cage_pts, cage_tris, ratio, controls=None, steps=20):
    cage_pts = _validate_points(cage_pts)
    _normalize_controls(controls)
    _validate_steps(steps)
    if not np.isfinite(ratio) or ratio < 1.0 or ratio > 4.0:
        raise ValueError('Rear ratio must be between 1 and 4')
    if ratio == 1.0:
        return 0.0, cage_pts.copy()
    target = volume(cage_pts, cage_tris) * ratio
    lo, hi = 0.0, 1.5
    if volume(deform_v5(cage_pts, hi, controls, steps=steps, is_cage=True), cage_tris) < target:
        raise ValueError('Shape controls cannot reach volume target')
    for _ in range(30):
        mid = 0.5 * (lo + hi)
        if volume(deform_v5(cage_pts, mid, controls, steps=steps, is_cage=True), cage_tris) < target:
            lo = mid
        else:
            hi = mid
    amp = 0.5 * (lo + hi)
    return amp, deform_v5(cage_pts, amp, controls, steps=steps, is_cage=True)

def jacobian_screen_v5(body, amp, controls=None, steps=20, epsilon=2e-5):
    v = _validate_points(body)
    amp = _validate_amp(amp)
    _normalize_controls(controls)
    _validate_steps(steps)
    if not np.isfinite(epsilon) or epsilon <= 0:
        raise ValueError('Jacobian finite-difference epsilon must be positive and finite')
    v = v[region(v) > 0]
    if len(v) == 0 or amp == 0.0:
        return {'samples': len(v), 'min_determinant': 1.0, 'nonpositive': 0}
    j = np.empty((len(v), 3, 3))
    for k in range(3):
        off = np.zeros(3)
        off[k] = epsilon
        j[:, :, k] = (
            deform_v5(v + off, amp, controls, steps=steps, is_cage=False)
            - deform_v5(v - off, amp, controls, steps=steps, is_cage=False)
        ) / (2.0 * epsilon)
    det = np.linalg.det(j)
    return {
        'samples': int(len(v)),
        'min_determinant': float(det.min()),
        'nonpositive': int(np.sum(det <= 0.0))
    }

def fix_vdb_triangle_winding(positions, triangles, vdb_vertex_start=98078):
    """Propose radial-facing flips for inspection; never certifies outward winding.

    Concave clefts can legitimately face the chosen center. The index threshold
    is source-specific and does not identify general VDB data. Caller must review
    proposals; this function returns a copy and never modifies source geometry.
    """
    v = np.asarray(positions, dtype=np.float64).reshape(-1, 3)
    f = np.asarray(triangles, dtype=np.uint32).reshape(-1, 3).copy()
    is_vdb = (f >= vdb_vertex_start).any(axis=1)
    tri_v = v[f]
    cent = tri_v.mean(axis=1)
    fn = np.cross(tri_v[:, 1] - tri_v[:, 0], tri_v[:, 2] - tri_v[:, 0])
    out_vec = cent - np.array([0.0, 0.58, -0.01])
    flip = is_vdb & ((fn * out_vec).sum(axis=1) < 0.0)
    f[flip, 1], f[flip, 2] = f[flip, 2].copy(), f[flip, 1].copy()
    return f, int(flip.sum())
