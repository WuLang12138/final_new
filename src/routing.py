"""Runtime ESGR/V5 routing and new-data preparation.

This module only decides the D/S branch. It does not modify the existing model
or paper configurations. It prepares a new h5ad into the standard input layout
used by :mod:`src.workflow`, computes the frozen routing features, and writes a
branch decision before any model training begins.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import anndata as ad
import numpy as np
import pandas as pd
import scipy.sparse as sp
from sklearn.decomposition import PCA
from sklearn.neighbors import kneighbors_graph


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config/esgr_v5_runtime.json"
MISSING_LABELS = {"", "nan", "none", "na", "unknown", "unlabeled"}


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024**2), b""):
            h.update(chunk)
    return h.hexdigest()


def _read(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write(path: Path, value: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    tmp.replace(path)


def _immutable(path: Path, value: Any) -> None:
    path = Path(path)
    if path.exists():
        if _read(path) != value:
            raise ValueError(
                "A frozen routing/input record changed. Use a new sample or data root: "
                + str(path)
            )
        return
    _write(path, value)


def load_runtime_config(path: str | Path = DEFAULT_CONFIG) -> dict:
    config = _read(Path(path))
    if config.get("version") != "v5":
        raise ValueError("Expected the frozen ESGR v5 runtime configuration")
    return config


def _integer_count_matrix(x) -> bool:
    values = x.data if sp.issparse(x) else np.asarray(x).ravel()
    for start in range(0, len(values), 1_000_000):
        block = values[start : start + 1_000_000]
        if not np.isfinite(block).all() or (block < 0).any():
            return False
        if not np.allclose(block, np.rint(block), atol=1e-5, rtol=0):
            return False
    return True


def _filter_genes(a: ad.AnnData, min_cells: int) -> ad.AnnData:
    x = a.X
    counts = np.asarray((x > 0).sum(axis=0)).ravel()
    keep = counts >= int(min_cells)
    return a[:, keep].copy()


def _top_variance_genes(a: ad.AnnData, n_top: int) -> ad.AnnData:
    if a.n_vars <= n_top:
        return a.copy()
    x = a.X.tocsr() if sp.issparse(a.X) else sp.csr_matrix(a.X)
    mean = np.asarray(x.sum(axis=0)).ravel() / x.shape[0]
    mean_square = np.asarray(x.power(2).sum(axis=0)).ravel() / x.shape[0]
    variance = np.maximum(mean_square - mean**2, 0)
    keep = np.sort(np.argpartition(variance, -n_top)[-n_top:])
    return a[:, keep].copy()


def _preprocess_author_style(a: ad.AnnData, config: dict, mode: str) -> ad.AnnData:
    import scanpy as sc

    prep = config["preprocessing"]
    work = _filter_genes(a, int(prep["min_gene_cells"]))
    n_top = min(int(prep["top_hvg"]), work.n_vars)
    if mode == "canonical_counts":
        if n_top < work.n_vars:
            try:
                sc.pp.highly_variable_genes(
                    work, flavor="seurat_v3", n_top_genes=n_top
                )
            except Exception:
                sc.pp.highly_variable_genes(
                    work, flavor="cell_ranger", n_top_genes=n_top
                )
            work = work[:, work.var["highly_variable"]].copy()
        work.layers["counts"] = work.X.copy()
        sc.pp.normalize_total(
            work, target_sum=float(prep["normalize_target_sum"])
        )
    elif mode == "author_normalized_expression":
        work = _top_variance_genes(work, n_top)
        work.layers["author_input"] = work.X.copy()
    else:
        raise ValueError("Unknown expression mode: " + mode)
    sc.pp.scale(work, zero_center=False, max_value=float(prep["scale_max_value"]))
    if work.n_vars < 2:
        raise ValueError("Fewer than two genes remain after preprocessing")
    work.uns["esgr_preprocessing_mode"] = mode
    return work


def build_spatial_graph(coords: np.ndarray, k: int = 8):
    adjacency = kneighbors_graph(
        coords, int(k), mode="connectivity", include_self=False
    )
    adjacency = adjacency.maximum(adjacency.T).tocsr()
    adjacency.setdiag(0)
    adjacency.eliminate_zeros()
    transition = adjacency + sp.eye(len(coords))
    transition = sp.diags(1 / np.asarray(transition.sum(axis=1)).ravel()) @ transition
    return adjacency, transition.tocsr()


def compute_routing_features(
    x,
    coords: np.ndarray,
    adjacency,
    config: dict,
) -> dict[str, float]:
    """Compute the frozen KNN8 diffusion diagnostics without reference labels."""
    feature_config = config["features"]
    X = x.toarray() if sp.issparse(x) else np.asarray(x)
    X = np.asarray(X, dtype=np.float64)
    coords = np.asarray(coords, dtype=np.float64)
    if X.ndim != 2 or coords.shape != (len(X), 2):
        raise ValueError("Expected cells x genes and finite two-column spatial coordinates")
    if not np.isfinite(X).all() or not np.isfinite(coords).all():
        raise ValueError("Nonfinite expression or coordinates")

    expected, _ = build_spatial_graph(coords, int(feature_config["knn"]))
    if (expected != adjacency).nnz:
        raise ValueError("Adjacency does not match the frozen KNN8 union graph")
    with_self = adjacency + sp.eye(len(X))
    propagation = sp.diags(
        1 / np.asarray(with_self.sum(axis=1)).ravel()
    ) @ with_self

    z = PCA(
        n_components=min(
            int(feature_config["pcs"]),
            X.shape[1],
            len(X) - 1,
        ),
        svd_solver="randomized",
        random_state=int(feature_config["random_state"]),
    ).fit_transform(X)
    z -= z.mean(axis=0)
    energy = float((z**2).sum())
    if energy < 1e-12:
        raise ValueError("No expression variance for routing diagnostics")

    i, j = sp.triu(adjacency, k=1).nonzero()
    rng = np.random.default_rng(int(feature_config["random_state"]))
    ri = rng.integers(len(X), size=len(i))
    rj = (ri + rng.integers(1, len(X), size=len(i))) % len(X)
    h = z.copy()
    for _ in range(int(feature_config["propagation_steps"])):
        h = (1.0 - float(feature_config["restart_alpha"])) * (
            propagation @ h
        ) + float(feature_config["restart_alpha"]) * z
    residual = z - h
    residual_energy = (residual**2).sum(axis=1)
    residual_norm = np.sqrt(residual_energy)

    def cosine(left, right):
        denominator = residual_norm[left] * residual_norm[right]
        valid = denominator > 1e-12
        if not valid.any():
            return 0.0
        return float(
            np.mean(
                np.sum(residual[left[valid]] * residual[right[valid]], axis=1)
                / denominator[valid]
            )
        )

    lengths = np.linalg.norm(coords[i] - coords[j], axis=1)
    features = {
        "neighbor_distance_ratio": float(
            np.mean(np.sum((z[i] - z[j]) ** 2, axis=1))
            / max(
                np.mean(np.sum((z[ri] - z[rj]) ** 2, axis=1)),
                1e-12,
            )
        ),
        "residual_concentration": float(
            np.quantile(residual_energy, 0.9)
            / max(np.median(residual_energy), 1e-12)
        ),
        "residual_coherence_excess": cosine(i, j) - cosine(ri, rj),
        "retained_variance": float(
            np.sum((h - h.mean(axis=0)) ** 2) / energy
        ),
        "diffusion_displacement": float(residual_energy.sum() / energy),
        "edge_length_cv": float(
            lengths.std() / max(lengths.mean(), 1e-12)
        ),
    }
    if not np.isfinite(list(features.values())).all():
        raise ValueError("Nonfinite routing features")
    return features


def select_route(features: dict, config: dict) -> dict:
    rule = config["route_rule"]["choose_S_if"]
    high = rule["high_residual_concentration_branch"]
    low = rule["low_neighbor_distance_branch"]
    extended = high["extended_guard"]
    rc_base = (
        features["residual_concentration"]
        >= float(high["residual_concentration_gte"])
        and features["edge_length_cv"] <= float(high["edge_length_cv_lte"])
    )
    rc_extended = (
        features["residual_concentration"]
        >= float(high["residual_concentration_gte"])
        and features["edge_length_cv"]
        <= float(extended["edge_length_cv_lte"])
        and features["retained_variance"]
        >= float(extended["retained_variance_gte"])
    )
    ndr = (
        features["neighbor_distance_ratio"]
        <= float(low["neighbor_distance_ratio_lte"])
        and features["edge_length_cv"] <= float(low["edge_length_cv_lte"])
    )
    route = "S" if (rc_base or rc_extended or ndr) else "D"
    reason = (
        "S_high_rc_base"
        if rc_base
        else (
            "S_high_rc_extended_guard"
            if rc_extended
            else ("S_low_ndr_edge_guarded" if ndr else "D_default")
        )
    )
    return {
        "route": route,
        "reason": reason,
        "branch_flags": {
            "high_rc_base": bool(rc_base),
            "high_rc_extended": bool(rc_extended),
            "low_ndr": bool(ndr),
        },
        "features": features,
    }


def _valid_labels(obs: pd.DataFrame, label_key: str) -> np.ndarray:
    if label_key not in obs:
        return np.zeros(len(obs), dtype=bool)
    labels = obs[label_key]
    return (
        labels.notna()
        & ~labels.astype(str).str.strip().str.lower().isin(MISSING_LABELS)
    ).to_numpy()


def prepare_new_data(
    input_path: str | Path,
    dataset: str,
    sample: str,
    *,
    clusters: int | None = None,
    label_key: str = "ground_truth",
    eval_mask_key: str = "gt_evaluable",
    spatial_key: str = "spatial",
    expression_mode: str = "auto",
    config_path: str | Path = DEFAULT_CONFIG,
    data_root: str | Path | None = None,
) -> dict:
    """Prepare a new h5ad and freeze its route decision before training."""
    input_path = Path(input_path).resolve()
    config_path = Path(config_path).resolve()
    if not input_path.is_file():
        raise FileNotFoundError(input_path)
    config = load_runtime_config(config_path)
    raw = ad.read_h5ad(input_path)
    input_sha = _sha(input_path)
    config_sha = _sha(config_path)
    if spatial_key not in raw.obsm:
        raise ValueError(f"Missing obsm['{spatial_key}']")
    if len(raw) > 6000:
        raise ValueError(
            "The current dense structure decoder is configured for at most 6000 spots"
        )
    coords = np.asarray(raw.obsm[spatial_key])
    if coords.shape != (len(raw), 2) or not np.isfinite(coords).all():
        raise ValueError("Spatial coordinates must be a finite n x 2 matrix")

    integer_counts = _integer_count_matrix(raw.X)
    if expression_mode == "auto":
        mode = "canonical_counts" if integer_counts else "author_normalized_expression"
    elif expression_mode == "counts":
        if not integer_counts:
            raise ValueError("Requested counts mode but X is not nonnegative integer counts")
        mode = "canonical_counts"
    elif expression_mode == "normalized":
        mode = "author_normalized_expression"
    else:
        raise ValueError("expression_mode must be auto, counts, or normalized")

    valid = _valid_labels(raw.obs, label_key)
    if label_key in raw.obs:
        raw.obs[label_key] = raw.obs[label_key].astype("object")
        raw.obs["reference"] = raw.obs[label_key].fillna("UNLABELED").astype(str)
    else:
        raw.obs["reference"] = "UNLABELED"
    if eval_mask_key in raw.obs:
        eval_mask = raw.obs[eval_mask_key].astype(bool).to_numpy()
    else:
        eval_mask = valid
    if eval_mask.any() and raw.obs.loc[eval_mask, "reference"].nunique() < 2:
        raise ValueError("Evaluation mask contains fewer than two reference classes")
    inferred_clusters = (
        int(raw.obs.loc[eval_mask, "reference"].nunique())
        if eval_mask.any()
        else None
    )
    if clusters is None:
        if inferred_clusters is None:
            raise ValueError("--clusters is required when no reference labels are available")
        clusters = inferred_clusters
    elif inferred_clusters is not None and int(clusters) != inferred_clusters:
        raise ValueError(
            f"Requested clusters={clusters}, but evaluable labels contain {inferred_clusters} classes"
        )
    if int(clusters) < 2:
        raise ValueError("clusters must be at least 2")

    data_root = Path(data_root or ROOT / "data/routed_inputs").resolve()
    output_dir = data_root / dataset / sample
    decision_path = output_dir / "route_decision.json"
    if decision_path.exists():
        existing = _read(decision_path)
        expected_identity = {
            "dataset": dataset,
            "sample": sample,
            "input": str(input_path),
            "input_sha256": input_sha,
            "routing_config": str(config_path),
            "routing_config_sha256": config_sha,
            "expression_mode": mode,
            "label_key": label_key,
            "eval_mask_key": eval_mask_key,
            "clusters": int(clusters),
        }
        for key, value in expected_identity.items():
            if existing.get(key) != value:
                raise ValueError(
                    f"Existing route lock differs at {key}; use a new sample or data root"
                )
        for name, expected in existing["prepared_inputs"].items():
            path = output_dir / name
            if not path.exists() or _sha(path) != expected:
                raise ValueError("Existing prepared routed input changed: " + str(path))
        return {
            **existing,
            "decision_path": str(decision_path),
            "expression_path": str(output_dir / "expression.h5ad"),
            "adjacency_path": str(output_dir / "adjacency.npz"),
            "transition_path": str(output_dir / "transition.npz"),
        }

    prepared = _preprocess_author_style(raw, config, mode)
    adjacency, transition = build_spatial_graph(
        prepared.obsm[spatial_key],
        int(config["preprocessing"]["spatial_k"]),
    )
    features = compute_routing_features(prepared.X, prepared.obsm[spatial_key], adjacency, config)
    decision = select_route(features, config)

    output_dir.mkdir(parents=True, exist_ok=True)
    expression_path = output_dir / "expression.h5ad"
    adjacency_path = output_dir / "adjacency.npz"
    transition_path = output_dir / "transition.npz"
    prepared.write_h5ad(expression_path, compression="gzip")
    sp.save_npz(adjacency_path, adjacency)
    sp.save_npz(transition_path, transition)
    input_hashes = {
        "expression.h5ad": _sha(expression_path),
        "adjacency.npz": _sha(adjacency_path),
        "transition.npz": _sha(transition_path),
    }
    decision_record = {
        "schema": 1,
        "dataset": dataset,
        "sample": sample,
        "input": str(input_path),
        "input_sha256": input_sha,
        "prepared_input": str(output_dir),
        "prepared_inputs": input_hashes,
        "routing_config": str(config_path),
        "routing_config_sha256": config_sha,
        "expression_mode": mode,
        "label_key": label_key,
        "eval_mask_key": eval_mask_key,
        "clusters": int(clusters),
        "n_obs": int(prepared.n_obs),
        "n_genes": int(prepared.n_vars),
        "evaluable_spots": int(eval_mask.sum()),
        "route": decision,
        "status": "route_locked_before_training",
    }
    _immutable(decision_path, decision_record)
    return {
        **decision_record,
        "decision_path": str(decision_path),
        "expression_path": str(expression_path),
        "adjacency_path": str(adjacency_path),
        "transition_path": str(transition_path),
    }


def profile_for_route(route: str, clusters: int, config: dict) -> tuple[dict, dict, dict]:
    """Return model parameters, common regularization, and route-specific lambdas."""
    if route not in config["route_profiles"]:
        raise ValueError("Unknown route: " + route)
    profile = config["route_profiles"][route]
    params = dict(
        config["training_common"],
        clusters=int(clusters),
        encoder=profile["encoder"],
    )
    if route == "D":
        params.update(steps=int(profile["steps"]), alpha=float(profile["alpha"]))
        regularization = {}
    else:
        regularization = dict(profile["regularization"])
    lambda_detail = float(profile["lambda_detail"])
    lambda_consistency = float(profile["lambda_consistency"])
    return params, regularization, {
        "lambda_detail": lambda_detail,
        "lambda_consistency": lambda_consistency,
    }


__all__ = [
    "ROOT",
    "DEFAULT_CONFIG",
    "load_runtime_config",
    "build_spatial_graph",
    "compute_routing_features",
    "select_route",
    "prepare_new_data",
    "profile_for_route",
]
