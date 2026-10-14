"""Experimental radial-chart descriptors, rational spline fitting and batch PCA.

The chart uses manually assumed source Y and bbox fractions, per-row recentering,
and supplied yaw/torsion. It is not pose/crop invariant anatomical calibration.
Missing bins are recorded separately before interpolation. Curvature describes
the completed radial chart, not the original donor surface or hidden anatomy.
Spline fairing is a discrete control-net penalty; no Class-A/seam certification
or trained anatomical model is supplied. Public API names remain compatible.
"""
from __future__ import annotations
import json
import math
import struct
from pathlib import Path
import importlib.util
import numpy as np
from scipy.interpolate import BSpline
from scipy.ndimage import distance_transform_edt, gaussian_filter


def load_glb_vertices_and_normals(glb_path: str | Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Read active-scene instances in world coordinates; reject unsupported pose data.

Uses the existing accessor/scene reader. Normals use the inverse transpose and
reflected instances reverse winding. Missing normals are returned as zeros.
"""
    project = Path(__file__).resolve().parents[1]
    reader_path = project / "measurements/five-frame-20261013/sequence_reader.py"
    spec = importlib.util.spec_from_file_location("rainee_scene_glb_reader", reader_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Scene-aware GLB reader unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    reader = module.GLBReader(glb_path)
    gltf = reader.document
    if gltf.get("skins") or gltf.get("animations"):
        raise ValueError("Skinned/animated GLBs need an evaluated pose before measurement")
    if not gltf.get("scenes") or not gltf.get("nodes"):
        raise ValueError("An explicit active scene and mesh nodes are required")
    verts, norms, tris = [], [], []
    v_off = 0
    for node_id, mesh_id, world in reader.scene_mesh_nodes():
        linear = world[:3, :3]
        det = float(np.linalg.det(linear))
        if not np.isfinite(world).all() or abs(det) < 1e-12:
            raise ValueError("Nonfinite or singular scene transform")
        for prim in gltf["meshes"][mesh_id].get("primitives", []):
            if prim.get("mode", 4) != 4 or prim.get("targets"):
                raise ValueError("Only evaluated triangle primitives without morph targets are supported")
            if "KHR_draco_mesh_compression" in prim.get("extensions", {}):
                raise ValueError("DRACO requires its decoder")
            attrs = prim["attributes"]
            v = reader.accessor(attrs["POSITION"]).astype(np.float64)
            if v.ndim != 2 or v.shape[1] != 3 or not np.isfinite(v).all():
                raise ValueError("Invalid POSITION accessor")
            verts.append(v @ linear.T + world[:3, 3])
            n = reader.accessor(attrs["NORMAL"]).astype(np.float64) if "NORMAL" in attrs else np.zeros_like(v)
            if n.shape != v.shape or not np.isfinite(n).all():
                raise ValueError("Invalid NORMAL accessor")
            n = n @ np.linalg.inv(linear)
            n /= np.maximum(np.linalg.norm(n, axis=1)[:, None], 1e-12)
            norms.append(n)
            ii = reader.accessor(prim["indices"]).reshape(-1).astype(np.int64) if "indices" in prim else np.arange(len(v))
            if len(ii) % 3 or (ii < 0).any() or (ii >= len(v)).any():
                raise ValueError("Invalid triangle indices")
            ii = ii.reshape(-1, 3)
            if det < 0:
                ii = ii[:, [0, 2, 1]]
            tris.append(ii + v_off)
            v_off += len(v)
    if not verts:
        raise ValueError("Active scene contains no supported mesh geometry")
    return np.vstack(verts), np.vstack(norms), np.vstack(tris)


def _fill_empty_bins(grid: np.ndarray) -> np.ndarray:
    mask = ~np.isfinite(grid)
    if not np.any(mask):
        return grid
    if np.all(mask):
        raise ValueError("No observed radial bins; no surface can be inferred")
    ind = distance_transform_edt(mask, return_distances=False, return_indices=True)
    return grid[tuple(ind)]


def radial_chart_curvature(radius: np.ndarray, y: np.ndarray, theta: np.ndarray):
    """Principal curvature of X(theta,y)=(r cos(theta),y,r sin(theta)).

Outward normals with the second fundamental form give a cylinder k=(0,-1/r).
Theta differences wrap periodically. This chart is not a mesh curvature estimator.
"""
    r = np.asarray(radius, dtype=float)
    if r.ndim != 2 or r.shape != (len(y), len(theta)) or min(r.shape) < 3:
        raise ValueError("Curvature needs a rectangular grid with at least three samples per axis")
    if not np.isfinite(r).all() or (r <= 0).any():
        raise ValueError("Radial surface must be finite and positive")
    dy, dt = float(y[1] - y[0]), float(theta[1] - theta[0])
    if dy <= 0 or dt <= 0 or not np.allclose(np.diff(y), dy) or not np.allclose(np.diff(theta), dt):
        raise ValueError("Curvature requires increasing uniform chart samples")
    ry = np.gradient(r, dy, axis=0, edge_order=2)
    ryy = np.gradient(ry, dy, axis=0, edge_order=2)
    rt = (np.roll(r, -1, axis=1) - np.roll(r, 1, axis=1)) / (2 * dt)
    rtt = (np.roll(r, -1, axis=1) - 2 * r + np.roll(r, 1, axis=1)) / dt**2
    ryt = (np.roll(ry, -1, axis=1) - np.roll(ry, 1, axis=1)) / (2 * dt)
    c, s = np.cos(theta)[None, :], np.sin(theta)[None, :]
    zero, one = np.zeros_like(r), np.ones_like(r)
    xt = np.stack((rt*c-r*s, zero, rt*s+r*c), axis=-1)
    xy = np.stack((ry*c, one, ry*s), axis=-1)
    xtt = np.stack(((rtt-r)*c-2*rt*s, zero, (rtt-r)*s+2*rt*c), axis=-1)
    xty = np.stack((ryt*c-ry*s, zero, ryt*s+ry*c), axis=-1)
    xyy = np.stack((ryy*c, zero, ryy*s), axis=-1)
    normal = np.cross(xy, xt)
    normal /= np.linalg.norm(normal, axis=-1)[..., None]
    dot = lambda a, b: np.sum(a*b, axis=-1)
    e, f, g = dot(xt, xt), dot(xt, xy), dot(xy, xy)
    ell, emm, enn = dot(normal, xtt), dot(normal, xty), dot(normal, xyy)
    metric = e*g-f*f
    mean = (ell*g-2*emm*f+enn*e)/(2*metric)
    gauss = (ell*enn-emm*emm)/metric
    delta = np.sqrt(np.maximum(mean*mean-gauss, 0))
    k1, k2 = mean+delta, mean-delta
    shape = (2/math.pi)*np.arctan2(k1+k2, np.maximum(k1-k2, 1e-12))
    return mean, gauss, shape


def extract_intrinsic_butt_dem(
    vertices: np.ndarray,
    y_fold_norm: float = 0.050,
    y_waist_norm: float = 0.418,
    cleft_yaw_offset_deg: float = 180.0,
    spinal_torsion_deg: float = 34.34,
    n_y: int = 56,
    n_theta: int = 120,
) -> dict[str, np.ndarray | float]:
    """Compute a provisional manually aligned radial chart, with observation provenance."""
    vertices = np.asarray(vertices, dtype=float)
    if vertices.ndim != 2 or vertices.shape[1] != 3 or len(vertices) < 12 or not np.isfinite(vertices).all():
        raise ValueError("Expected at least 12 finite XYZ source points")
    if not isinstance(n_y, (int, np.integer)) or not isinstance(n_theta, (int, np.integer)) or n_y < 3 or n_theta < 4:
        raise ValueError("Chart resolution must be integer n_y>=3 and n_theta>=4")
    if not np.isfinite([y_fold_norm, y_waist_norm, cleft_yaw_offset_deg, spinal_torsion_deg]).all():
        raise ValueError("Chart assumptions must be finite")
    if not 0 <= y_fold_norm < y_waist_norm <= 1:
        raise ValueError("Manual fold/waist bbox fractions must satisfy 0<=fold<waist<=1")
    bmin, bmax = vertices.min(axis=0), vertices.max(axis=0)
    if bmax[1] - bmin[1] <= 1e-9:
        raise ValueError("Source Y height is degenerate")
    span = np.maximum(bmax - bmin, 1e-9)
    yn = (vertices[:, 1] - bmin[1]) / span[1]
    xn = (vertices[:, 0] - 0.5 * (bmin[0] + bmax[0])) / span[1]
    zn = (vertices[:, 2] - 0.5 * (bmin[2] + bmax[2])) / span[1]

    h_pelvis = float(y_waist_norm - y_fold_norm)
    y_star = (yn - y_fold_norm) / h_pelvis

    y_edges = np.linspace(0.0, 1.15, n_y + 1)
    th_edges = np.linspace(-math.pi, math.pi, n_theta + 1)
    y_centers = 0.5 * (y_edges[:-1] + y_edges[1:])
    th_centers = 0.5 * (th_edges[:-1] + th_edges[1:])

    dem = np.full((n_y, n_theta), np.nan, dtype=np.float64)
    for i in range(n_y):
        ym = (y_star >= y_edges[i]) & (y_star < y_edges[i + 1])
        if ym.sum() < 12:
            continue
        xs, zs = xn[ym], zn[ym]
        cx, cz = float(np.median(xs)), float(np.median(zs))
        dx0, dz0 = xs - cx, zs - cz
        ang = math.radians(cleft_yaw_offset_deg + spinal_torsion_deg * float(np.clip(y_centers[i] - 0.30, -0.3, 0.85)))
        c_t, s_t = math.cos(-ang), math.sin(-ang)
        dx = c_t * dx0 - s_t * dz0
        dz = s_t * dx0 + c_t * dz0
        th = (np.arctan2(dz, dx) + math.pi) % (2*math.pi) - math.pi
        rad = np.hypot(dx, dz) / h_pelvis
        for j in range(n_theta):
            tm = (th >= th_edges[j]) & (th < th_edges[j + 1])
            if tm.sum() > 0:
                dem[i, j] = float(np.percentile(rad[tm], 95))

    sampled = dem.copy()
    observed = np.isfinite(sampled)
    dem = gaussian_filter(_fill_empty_bins(dem), sigma=(1.0, 1.2), mode=("nearest", "wrap"))
    if (dem <= 0).any():
        raise ValueError("Observed radial chart is degenerate")
    mean_curv, gauss_curv, shape_idx = radial_chart_curvature(dem, y_centers, th_centers)

    return {
        "elevation": dem,
        "sampled_elevation": sampled,
        "observed_mask": observed,
        "observed_bin_fraction": float(observed.mean()),
        "mean_curvature": mean_curv,
        "gaussian_curvature": gauss_curv,
        "shape_index": shape_idx,
        "y_star": y_centers,
        "theta_deg": np.degrees(th_centers),
        "pelvic_unit_scale": h_pelvis,
        "pelvic_height_source_units": h_pelvis * float(span[1]),
        "calibration_status": "provisional_manual_pelvic_chart",
        "anatomical_calibration": False,
        "curvature_scope": "Completed recentered/untwisted radial chart; outward second fundamental form. Not donor mesh curvature.",
        "completion_scope": "Nearest-bin completion and Gaussian smoothing are estimates. Only observed_mask marks sampled bins.",
        "manual_assumptions": {"up_axis": "source Y", "fold_bbox_fraction": float(y_fold_norm), "waist_bbox_fraction": float(y_waist_norm),
            "cleft_yaw_offset_deg": float(cleft_yaw_offset_deg), "spinal_torsion_deg": float(spinal_torsion_deg)},
    }


def fit_bicubic_nurbs_patch(
    z_grid: np.ndarray,
    n_ctrl_u: int = 14,
    n_ctrl_v: int = 10,
    w_ridge: float = 1.45,
    lambda_fair: float = 0.015,
    knots_u: np.ndarray | None = None,
    knots_v: np.ndarray | None = None,
) -> dict[str, np.ndarray | float]:
    """Fit a scalar rational cubic patch with discrete control-net second differences."""
    z_grid = np.asarray(z_grid, dtype=float)
    if z_grid.ndim != 2 or min(z_grid.shape) < 2 or not np.isfinite(z_grid).all():
        raise ValueError("Fit needs a finite rectangular grid with at least two samples per axis")
    if not isinstance(n_ctrl_u, (int, np.integer)) or not isinstance(n_ctrl_v, (int, np.integer)) or min(n_ctrl_u, n_ctrl_v) < 4:
        raise ValueError("Cubic patches need at least four control points per axis")
    if not np.isfinite([w_ridge, lambda_fair]).all() or w_ridge <= 0 or lambda_fair < 0:
        raise ValueError("Rational weights must be positive and fairing nonnegative")
    nu, nv = z_grid.shape
    u = np.linspace(0.0, 1.0, nu)
    v = np.linspace(0.0, 1.0, nv)

    def bspline_basis(t: np.ndarray, n_ctrl: int, explicit_knots):
        n_int = n_ctrl - 4
        int_knots = np.linspace(0.0, 1.0, n_int + 2)[1:-1] if n_int > 0 else np.array([])
        knots = np.concatenate([[0.0] * 4, int_knots, [1.0] * 4]) if explicit_knots is None else np.asarray(explicit_knots, dtype=float)
        if knots.ndim != 1 or len(knots) != n_ctrl + 4 or not np.isfinite(knots).all() or (np.diff(knots) < 0).any() or knots[n_ctrl] <= knots[3]:
            raise ValueError("Invalid cubic knot vector")
        if not np.all(knots[:4] == knots[3]) or not np.all(knots[-4:] == knots[n_ctrl]):
            raise ValueError("Only clamped cubic knot vectors are supported")
        t = knots[3] + t * (knots[n_ctrl] - knots[3])
        b_mat = np.zeros((len(t), n_ctrl), dtype=np.float64)
        for i in range(n_ctrl):
            c = np.zeros(n_ctrl, dtype=np.float64)
            c[i] = 1.0
            b_mat[:, i] = BSpline(knots, c, 3)(t)
        return b_mat, knots

    bu, knots_u = bspline_basis(u, n_ctrl_u, knots_u)
    bv, knots_v = bspline_basis(v, n_ctrl_v, knots_v)
    weights = np.ones((n_ctrl_u, n_ctrl_v), dtype=np.float64)
    weights[1:-1, 1:-1] = w_ridge

    phi = np.einsum("ui,vj,ij->uvij", bu, bv, weights)
    denom = np.maximum(phi.sum(axis=(2, 3), keepdims=True), 1e-8)
    r_mat = (phi / denom).reshape(nu * nv, n_ctrl_u * n_ctrl_v)

    n_tot = n_ctrl_u * n_ctrl_v
    reg_rows = []
    for i in range(n_ctrl_u):
        for j in range(n_ctrl_v):
            idx = i * n_ctrl_v + j
            if 0 < i < n_ctrl_u - 1:
                row = np.zeros(n_tot, dtype=np.float64)
                row[(i - 1) * n_ctrl_v + j] = 1.0
                row[idx] = -2.0
                row[(i + 1) * n_ctrl_v + j] = 1.0
                reg_rows.append(row)
            if 0 < j < n_ctrl_v - 1:
                row = np.zeros(n_tot, dtype=np.float64)
                row[i * n_ctrl_v + (j - 1)] = 1.0
                row[idx] = -2.0
                row[i * n_ctrl_v + (j + 1)] = 1.0
                reg_rows.append(row)

    l_reg = np.array(reg_rows, dtype=np.float64) * math.sqrt(lambda_fair)
    a_aug = np.vstack([r_mat, l_reg])
    b_aug = np.concatenate([z_grid.ravel(), np.zeros(len(reg_rows), dtype=np.float64)])
    ctrl_pts, _, _, _ = np.linalg.lstsq(a_aug, b_aug, rcond=None)
    recon = (r_mat @ ctrl_pts).reshape(nu, nv)
    rms = float(np.sqrt(np.mean((z_grid - recon) ** 2)))
    return {
        "reconstructed": recon,
        "control_points": ctrl_pts.reshape(n_ctrl_u, n_ctrl_v),
        "weights": weights,
        "knots_u": knots_u,
        "knots_v": knots_v,
        "degree": 3,
        "class_a_certified": False,
        "fairing_scope": "Discrete control-net second differences, not continuous thin-plate bending energy",
        "rms_error": rms,
    }


def fit_bicubic_nurbs_gluteal_complex(
    dem_grid: np.ndarray,
    theta_deg: np.ndarray,
    n_ctrl_u: int = 14,
    n_ctrl_v: int = 10,
    w_ridge: float = 1.45,
    lambda_fair: float = 0.015,
) -> dict[str, object]:
    """Fit two independent scalar rear charts; seam continuity is not constrained."""
    dem_grid, theta_deg = np.asarray(dem_grid, dtype=float), np.asarray(theta_deg, dtype=float)
    if dem_grid.ndim != 2 or theta_deg.ndim != 1 or dem_grid.shape[1] != len(theta_deg) or not np.isfinite(theta_deg).all():
        raise ValueError("DEM columns must match a finite theta vector")
    rear_cols = (theta_deg >= -165.0) & (theta_deg <= -15.0)
    patch = dem_grid[:, rear_cols]
    if patch.shape[1] < 4:
        raise ValueError("Insufficient observed rear-angle chart columns for paired fitting")
    mid = patch.shape[1] // 2
    left_fit = fit_bicubic_nurbs_patch(patch[:, : mid + 1], n_ctrl_u, n_ctrl_v, w_ridge, lambda_fair)
    right_fit = fit_bicubic_nurbs_patch(patch[:, mid:], n_ctrl_u, n_ctrl_v, w_ridge, lambda_fair)
    combined = np.hstack([left_fit["reconstructed"][:, :-1], right_fit["reconstructed"]])
    rms_total = float(np.sqrt(np.mean((patch - combined) ** 2)))
    return {
        "reconstructed_posterior": combined,
        "left_lobe_control_net": left_fit["control_points"],
        "right_lobe_control_net": right_fit["control_points"],
        "left_weights": left_fit["weights"], "right_weights": right_fit["weights"],
        "knots_u": left_fit["knots_u"], "knots_v": left_fit["knots_v"],
        "seam_continuity_constrained": False,
        "class_a_certified": False,
        "rms_error": rms_total,
    }


class ButtMorphableModel:
    """Small batch PCA study; stores all charts and recomputes a full SVD per donor.

Charts need independently reviewed alignment before interpreting this basis.
No anatomical learned model or semantic meaning of beta sliders is provided.
"""

    def __init__(self, max_components: int = 8):
        if not isinstance(max_components, (int, np.integer)) or max_components < 1:
            raise ValueError("max_components must be a positive integer")
        self.max_components = max_components
        self.donor_names: list[str] = []
        self.grid_shape: tuple[int, int] | None = None
        self.data_matrix: np.ndarray | None = None
        self.mean_vector: np.ndarray | None = None
        self.components: np.ndarray | None = None
        self.singular_values: np.ndarray | None = None
        self.variance_ratio: np.ndarray | None = None

    def add_donor(self, name: str, dem_elevation: np.ndarray) -> None:
        """Append a complete finite chart and recompute batch PCA."""
        dem_elevation = np.asarray(dem_elevation, dtype=float)
        if dem_elevation.ndim != 2 or not dem_elevation.size or not np.isfinite(dem_elevation).all():
            raise ValueError("PCA requires a complete finite two-dimensional chart")
        if self.grid_shape is None:
            self.grid_shape = dem_elevation.shape
        elif dem_elevation.shape != self.grid_shape:
            raise ValueError(f"Expected grid shape {self.grid_shape}, got {dem_elevation.shape}")

        vec = dem_elevation.astype(np.float64).reshape(1, -1)
        self.donor_names.append(name)
        if self.data_matrix is None:
            self.data_matrix = vec
        else:
            self.data_matrix = np.vstack([self.data_matrix, vec])
        self._recompute_basis()

    def _recompute_basis(self) -> None:
        assert self.data_matrix is not None
        self.mean_vector = self.data_matrix.mean(axis=0)
        if len(self.donor_names) < 2:
            self.components = np.zeros((1, self.data_matrix.shape[1]), dtype=np.float64)
            self.singular_values = np.array([0.0], dtype=np.float64)
            self.variance_ratio = np.array([0.0], dtype=np.float64)
            return
        centered = self.data_matrix - self.mean_vector
        _, s_vals, vt = np.linalg.svd(centered, full_matrices=False)
        k = min(self.max_components, len(s_vals))
        self.components = vt[:k]
        self.singular_values = s_vals[:k] / math.sqrt(max(len(self.donor_names) - 1, 1))
        total_var = float(np.sum(s_vals ** 2))
        self.variance_ratio = (s_vals[:k] ** 2) / max(total_var, 1e-12)

    def synthesize(self, beta_weights: list[float] | np.ndarray) -> np.ndarray:
        """Synthesize a complete chart from numerical, nonsemantic PCA coefficients."""
        if self.mean_vector is None or self.components is None or self.singular_values is None:
            raise RuntimeError("Morphable model has no donors.")
        b = np.asarray(beta_weights, dtype=np.float64)
        if b.ndim != 1 or not np.isfinite(b).all():
            raise ValueError("PCA coefficients must be a finite vector")
        k = min(len(b), len(self.singular_values))
        disp = np.sum((b[:k] * self.singular_values[:k])[:, None] * self.components[:k], axis=0)
        return (self.mean_vector + disp).reshape(self.grid_shape)

    def project(self, target_dem: np.ndarray, ridge_lambda: float = 1e-2) -> dict[str, object]:
        """Project a complete chart into this batch basis; not held-out validation."""
        if self.mean_vector is None or self.components is None or self.singular_values is None:
            raise RuntimeError("Morphable model has no donors.")
        target_dem = np.asarray(target_dem, dtype=float)
        if target_dem.shape != self.grid_shape or not np.isfinite(target_dem).all():
            raise ValueError("Projection requires a complete finite chart with the training grid shape")
        if not np.isfinite(ridge_lambda) or ridge_lambda <= 0:
            raise ValueError("ridge_lambda must be positive to support rank-deficient training sets")
        y = target_dem.reshape(-1) - self.mean_vector
        basis_scaled = self.components * self.singular_values[:, None]
        gram = basis_scaled @ basis_scaled.T + ridge_lambda * np.eye(len(self.singular_values))
        rhs = basis_scaled @ y
        beta = np.linalg.solve(gram, rhs)
        recon = self.synthesize(beta)
        rms = float(np.sqrt(np.mean((target_dem - recon) ** 2)))
        return {"beta": beta.tolist(), "reconstructed": recon, "rms_error": rms,
            "method": "batch-recomputed SVD PCA", "validation_scope": "Complete chart projection in the fitted basis; not independent accuracy evidence"}
