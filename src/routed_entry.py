"""Template entry point for ESGR-routed new spatial transcriptomics data.

Usage examples:
  python -m src.routed_entry prepare --input new.h5ad --dataset Tissue --sample S1 --clusters 7
  python -m src.routed_entry train --dataset Tissue --sample S1
  python -m src.routed_entry run --input new.h5ad --dataset Tissue --sample S1 --clusters 7

The existing model, workflow, and paper configuration files are not modified.
The selected route is frozen before training and only that route is trained.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import anndata as ad
import numpy as np
import pandas as pd
import scipy.sparse as sp
import torch
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score, silhouette_score
from threadpoolctl import threadpool_limits

from model.propagation import ZINB
from src import routing
from src import workflow as w


def _safe_name(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    if not value:
        raise ValueError("dataset and sample names must not be empty")
    return value


def _paths(
    dataset: str,
    sample: str,
    route: str,
    seed: int,
    *,
    results_root: Path | None = None,
    weights_root: Path | None = None,
) -> dict[str, Path]:
    results_root = Path(results_root or ROOT / "results")
    weights_root = Path(weights_root or ROOT / "weights")
    archive = results_root / "archived/routed" / dataset / sample / route / f"seed_{seed}"
    prediction = results_root / "predictions/routed" / dataset / sample / route / f"seed_{seed}"
    weight = weights_root / "routed" / dataset / sample / route / f"seed_{seed}.pt"
    return {
        "archive": archive,
        "prediction": prediction,
        "weight": weight,
        "best_weight": weight.with_name(weight.stem + "_best.pt"),
    }


def _decision_path(data_root: Path, dataset: str, sample: str) -> Path:
    return data_root / dataset / sample / "route_decision.json"


def _load_decision(data_root: Path, dataset: str, sample: str) -> dict:
    path = _decision_path(data_root, dataset, sample)
    if not path.exists():
        raise FileNotFoundError("Run prepare first: " + str(path))
    return w.read(path)


def _validate_prepared(decision: dict) -> tuple[ad.AnnData, sp.csr_matrix, sp.csr_matrix]:
    prepared = Path(decision["prepared_input"])
    for name, expected in decision["prepared_inputs"].items():
        path = prepared / name
        if w.sha(path) != expected:
            raise ValueError("Prepared routed input changed: " + str(path))
    a = ad.read_h5ad(prepared / "expression.h5ad")
    adjacency = sp.load_npz(prepared / "adjacency.npz").tocsr()
    transition = sp.load_npz(prepared / "transition.npz").tocsr()
    expected_adjacency, expected_transition = routing.build_spatial_graph(
        a.obsm["spatial"],
        int(decision.get("spatial_k", 8)),
    )
    if (adjacency != expected_adjacency).nnz:
        raise ValueError("Prepared adjacency is not the frozen KNN8 union")
    delta = transition - expected_transition
    if delta.nnz and np.max(np.abs(delta.data)) > 1e-6:
        raise ValueError("Prepared transition does not match row_normalize(A + I)")
    return a, adjacency, transition


def _evaluation_mask(a: ad.AnnData, decision: dict) -> np.ndarray:
    key = decision.get("eval_mask_key", "gt_evaluable")
    if key and key in a.obs:
        return a.obs[key].astype(bool).to_numpy()
    reference = a.obs["reference"].astype(str).to_numpy()
    return reference != "UNLABELED"


def _evaluate(
    model,
    x,
    propagation,
    labels: np.ndarray,
    mask: np.ndarray,
    clusters: int,
    seed: int,
):
    model.eval()
    with torch.no_grad():
        embedding = w.embedding(model, x, propagation).cpu().numpy()
    if not np.isfinite(embedding).all():
        raise RuntimeError("Nonfinite model embedding")
    with threadpool_limits(limits=1):
        prediction = KMeans(
            n_clusters=int(clusters), n_init=20, random_state=seed
        ).fit_predict(embedding)
    if mask.any():
        truth = labels[mask]
        metrics = {
            "ARI": float(adjusted_rand_score(truth, prediction[mask])),
            "NMI": float(normalized_mutual_info_score(truth, prediction[mask])),
            "silhouette": float("nan"),
            "selection_value": float(
                adjusted_rand_score(truth, prediction[mask])
            ),
            "selection_metric": "ARI",
        }
    else:
        score = float(silhouette_score(embedding, prediction))
        metrics = {
            "ARI": float("nan"),
            "NMI": float("nan"),
            "silhouette": score,
            "selection_value": score,
            "selection_metric": "silhouette",
        }
    return embedding, prediction, metrics


def _similarity(x: np.ndarray, adjacency, regularization: dict):
    """Expression-similar spatial edges for the combined S route."""
    values = np.log1p(
        x / np.maximum(x.sum(axis=1, keepdims=True), 1) * 10000
    )
    values = (values - values.mean(axis=0)) / np.maximum(values.std(axis=0), 1e-4)
    pcs = PCA(
        n_components=min(
            int(regularization["expression_pcs"]),
            len(values) - 1,
            values.shape[1],
        ),
        random_state=0,
        svd_solver="randomized",
    ).fit_transform(values)
    i, j = sp.triu(adjacency, k=1).nonzero()
    distance = ((pcs[i] - pcs[j]) ** 2).mean(axis=1)
    scale = max(float(np.median(distance)), 1e-8)
    weight = np.exp(-distance / scale) * (
        distance <= np.quantile(distance, float(regularization["similar_edge_quantile"]))
    )
    if weight.sum() <= 0:
        raise ValueError("No expression-similar spatial edges for the S route")
    return i, j, weight.astype("float32")


def _penalties(model, embedding, edges):
    gated = model.GNN_S.last_gate * model.GNN_S.detail
    detail = gated.square().mean()
    unit = torch.nn.functional.normalize(embedding, dim=1, eps=1e-8)
    i, j, weights = edges
    consistency = (
        weights * (unit[i] - unit[j]).square().sum(axis=1)
    ).sum() / weights.sum()
    return detail, consistency


def _completed(report_path: Path, job: dict) -> bool:
    if not report_path.exists():
        return False
    report = w.read(report_path)
    if report.get("job") != job:
        raise ValueError("Existing routed run uses a different job configuration")
    for name, record in report["files"].items():
        path = Path(record["path"])
        if not path.is_absolute():
            path = report_path.parent / path
        if w.sha(path) != record["sha256"]:
            raise ValueError("Existing routed artifact changed: " + str(path))
    return True


def train_selected(
    dataset: str,
    sample: str,
    *,
    config_path: str | Path = routing.DEFAULT_CONFIG,
    data_root: str | Path | None = None,
    results_root: str | Path | None = None,
    weights_root: str | Path | None = None,
    device: str = "auto",
    seeds: list[int] | None = None,
    epochs: int | None = None,
) -> list[dict]:
    dataset, sample = _safe_name(dataset), _safe_name(sample)
    data_root = Path(data_root or ROOT / "data/routed_inputs").resolve()
    decision = _load_decision(data_root, dataset, sample)
    config_path = Path(config_path).resolve()
    if w.sha(config_path) != decision["routing_config_sha256"]:
        raise ValueError("Runtime routing configuration changed after route lock")
    config = routing.load_runtime_config(config_path)
    route = decision["route"]["route"]
    params, regularization, penalties = routing.profile_for_route(
        route, int(decision["clusters"]), config
    )
    if epochs is not None:
        params["epochs"] = int(epochs)
    seeds = list(config["seeds"] if seeds is None else seeds)
    if not seeds or len(seeds) != len(set(seeds)):
        raise ValueError("Seeds must be nonempty and unique")
    torch.set_num_threads(int(params["threads"]))
    device = (
        "cuda" if torch.cuda.is_available() else "cpu"
    ) if device == "auto" else device
    if device.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError("CUDA is unavailable")
    a, adjacency, transition = _validate_prepared(decision)
    X = a.X.toarray() if sp.issparse(a.X) else np.asarray(a.X)
    x = torch.as_tensor(X, dtype=torch.float32, device=device)
    propagation = w.sparse_tensor(transition, device)
    target = torch.as_tensor(adjacency.toarray(), dtype=torch.float32, device=device)
    labels = a.obs["reference"].astype(str).to_numpy()
    evaluation_mask = _evaluation_mask(a, decision)
    reports = []
    for seed in seeds:
        paths = _paths(
            dataset,
            sample,
            route,
            int(seed),
            results_root=Path(results_root) if results_root else None,
            weights_root=Path(weights_root) if weights_root else None,
        )
        for directory in (paths["archive"], paths["prediction"], paths["weight"].parent):
            directory.mkdir(parents=True, exist_ok=True)
        job = {
            "protocol": "esgr_routed_new_data",
            "dataset": dataset,
            "sample": sample,
            "profile": "esgr_" + route,
            "route": route,
            "route_decision_sha256": w.sha(_decision_path(data_root, dataset, sample)),
            "seed": int(seed),
            "parameters": params,
            "regularization": regularization,
            "lambda_detail": penalties["lambda_detail"],
            "lambda_consistency": penalties["lambda_consistency"],
            "input": decision["prepared_input"],
            "input_sha256": decision["prepared_inputs"],
            "weight": str(paths["weight"]),
            "archive": str(paths["archive"]),
            "prediction": str(paths["prediction"]),
        }
        w.write(paths["archive"] / "job.json", job)
        report_path = paths["archive"] / "completed.json"
        if _completed(report_path, job):
            print(f"[skip] {dataset}/{sample} {route} seed {seed}", flush=True)
            reports.append(w.read(report_path))
            continue
        if shutil.disk_usage(paths["archive"]).free < 4 * 1024**3:
            raise RuntimeError("Less than 4 GiB free; completed routed runs were kept")

        w.seed_all(int(seed))
        model = w.build(params, a.n_vars).to(device)
        optimizer = torch.optim.Adam(
            model.parameters(),
            lr=float(params["learning_rate"]),
            weight_decay=float(params["weight_decay"]),
        )
        edges = None
        if route == "S":
            edge_path = paths["archive"] / "similarity_edges.npz"
            if edge_path.exists():
                with np.load(edge_path, allow_pickle=False) as saved:
                    i, j, edge_weight = saved["i"], saved["j"], saved["weight"]
            else:
                i, j, edge_weight = _similarity(X, adjacency, regularization)
                np.savez_compressed(
                    edge_path, i=i, j=j, weight=edge_weight
                )
            edges = (
                torch.as_tensor(i, device=device),
                torch.as_tensor(j, device=device),
                torch.as_tensor(edge_weight, device=device),
            )

        resume_path = paths["prediction"] / "resume.pt"
        history = []
        start = 1
        best = None
        if resume_path.exists():
            state = torch.load(resume_path, map_location="cpu", weights_only=False)
            if state["job"] != job or state["device"] != device:
                raise ValueError("Resume checkpoint belongs to a different routed job")
            model.load_state_dict(state["model"])
            optimizer.load_state_dict(state["optimizer"])
            history = state["history"]
            start = int(state["epoch"]) + 1
            best = state["best"]
            random.setstate(state["python"])
            np.random.set_state(state["numpy"])
            torch.set_rng_state(state["torch"])
            if state["cuda"] is not None:
                torch.cuda.set_rng_state_all(state["cuda"])
            print(f"[resume] {dataset}/{sample} {route} seed {seed}: epoch {start}", flush=True)

        def cpu_state():
            return {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}

        for epoch in range(start, int(params["epochs"]) + 1):
            model.train()
            optimizer.zero_grad()
            embedding, reconstructed, pi, dispersion, mean, _ = model(
                x, propagation, propagation
            )
            expression_loss = ZINB(
                pi, theta=dispersion, ridge_lambda=0
            ).loss(x, mean, mean=True)
            graph_loss = w.structure_loss(reconstructed, target)
            base_loss = expression_loss + float(params["beta"]) * graph_loss
            if route == "S":
                detail_loss, consistency_loss = _penalties(model, embedding, edges)
            else:
                detail_loss = expression_loss.new_zeros(())
                consistency_loss = expression_loss.new_zeros(())
            loss = (
                base_loss
                + float(penalties["lambda_detail"]) * detail_loss
                + float(penalties["lambda_consistency"]) * consistency_loss
            )
            if not torch.isfinite(loss):
                raise RuntimeError("Nonfinite routed training loss")
            loss.backward()
            optimizer.step()
            z, prediction, metrics = _evaluate(
                model,
                x,
                propagation,
                labels,
                evaluation_mask,
                int(params["clusters"]),
                int(seed),
            )
            history.append(
                {
                    "epoch": epoch,
                    "loss": float(loss.detach()),
                    "base_loss": float(base_loss.detach()),
                    "detail_loss": float(detail_loss.detach()),
                    "consistency_loss": float(consistency_loss.detach()),
                    "ARI": metrics["ARI"],
                    "NMI": metrics["NMI"],
                    "silhouette": metrics["silhouette"],
                    "selection_value": metrics["selection_value"],
                    "selection_metric": metrics["selection_metric"],
                }
            )
            if best is None or metrics["selection_value"] > best["metrics"]["selection_value"]:
                best = {
                    "model": cpu_state(),
                    "epoch": epoch,
                    "metrics": metrics,
                    "embedding": z.copy(),
                    "prediction": prediction.copy(),
                }
            if epoch % 10 == 0 or epoch == int(params["epochs"]):
                w.save_torch(
                    resume_path,
                    {
                        "job": job,
                        "device": device,
                        "epoch": epoch,
                        "model": cpu_state(),
                        "optimizer": optimizer.state_dict(),
                        "history": history,
                        "best": best,
                        "python": random.getstate(),
                        "numpy": np.random.get_state(),
                        "torch": torch.get_rng_state(),
                        "cuda": (
                            torch.cuda.get_rng_state_all()
                            if torch.cuda.is_available()
                            else None
                        ),
                    },
                )
                pd.DataFrame(history).to_csv(paths["archive"] / "history.csv", index=False)
            if epoch == 1 or epoch % 25 == 0 or epoch == int(params["epochs"]):
                print(
                    f"{dataset}/{sample} {route} seed {seed} epoch {epoch}: "
                    f"{metrics['selection_metric']}={metrics['selection_value']:.5f}",
                    flush=True,
                )
        if best is None:
            raise RuntimeError("No routed training checkpoint was produced")
        z, prediction, final_metrics = _evaluate(
            model,
            x,
            propagation,
            labels,
            evaluation_mask,
            int(params["clusters"]),
            int(seed),
        )
        final_state = {
            "model": cpu_state(),
            "epoch": int(params["epochs"]),
            "metrics": final_metrics,
            "embedding": z,
            "prediction": prediction,
        }
        artifacts = {}
        for name, state in (("best", best), ("final", final_state)):
            checkpoint = paths["best_weight"] if name == "best" else paths["weight"]
            w.save_torch(
                checkpoint,
                {
                    "format": 1,
                    "checkpoint_kind": name,
                    "job": job,
                    "model": state["model"],
                    "epoch": state["epoch"],
                    "metrics": state["metrics"],
                },
            )
            array_path = paths["archive"] / f"{name}.npz"
            model.load_state_dict(state["model"])
            zz, pp, _ = _evaluate(
                model,
                x,
                propagation,
                labels,
                evaluation_mask,
                int(params["clusters"]),
                int(seed),
            )
            if not np.allclose(zz, state["embedding"], atol=1e-6, rtol=1e-5):
                raise ValueError("Best/final routed checkpoint does not reload")
            w.save_arrays(
                array_path,
                a,
                zz,
                pp,
                int(state["epoch"]),
            )
            artifacts[name + ".npz"] = array_path
            artifacts[name + ".pt"] = checkpoint
        artifacts["history.csv"] = paths["archive"] / "history.csv"
        if route == "S":
            artifacts["similarity_edges.npz"] = paths["archive"] / "similarity_edges.npz"
        pd.DataFrame([job]).to_csv(paths["archive"] / "job.csv", index=False)
        report = {
            "job": job,
            "route_decision": decision["route"],
            "best": {
                "epoch": int(best["epoch"]),
                **best["metrics"],
            },
            "final": final_metrics,
            "files": {
                name: {
                    "path": str(path),
                    "sha256": w.sha(path),
                }
                for name, path in artifacts.items()
            },
        }
        w.write(report_path, report)
        resume_path.unlink(missing_ok=True)
        reports.append(report)
        print(f"[done] {dataset}/{sample} {route} seed {seed}", flush=True)
    return reports


def prepare(
    input_path: str | Path,
    dataset: str,
    sample: str,
    *,
    clusters: int | None,
    label_key: str = "ground_truth",
    eval_mask_key: str = "gt_evaluable",
    spatial_key: str = "spatial",
    expression_mode: str = "auto",
    config_path: str | Path = routing.DEFAULT_CONFIG,
    data_root: str | Path | None = None,
) -> dict:
    return routing.prepare_new_data(
        input_path,
        _safe_name(dataset),
        _safe_name(sample),
        clusters=clusters,
        label_key=label_key,
        eval_mask_key=eval_mask_key,
        spatial_key=spatial_key,
        expression_mode=expression_mode,
        config_path=config_path,
        data_root=data_root,
    )


def _parse_seeds(value: str | None) -> list[int] | None:
    if value is None:
        return None
    seeds = [int(item.strip()) for item in value.split(",") if item.strip()]
    return seeds


def main():
    parser = argparse.ArgumentParser(
        description="Prepare and train a new dataset through the frozen ESGR V5 route."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "run"):
        p = sub.add_parser(name)
        p.add_argument("--input", required=True)
        p.add_argument("--dataset", required=True)
        p.add_argument("--sample", required=True)
        p.add_argument("--clusters", type=int)
        p.add_argument("--label-key", default="ground_truth")
        p.add_argument("--eval-mask-key", default="gt_evaluable")
        p.add_argument("--spatial-key", default="spatial")
        p.add_argument(
            "--expression-mode",
            choices=["auto", "counts", "normalized"],
            default="auto",
        )
        p.add_argument("--config", default=str(routing.DEFAULT_CONFIG))
        p.add_argument("--data-root")
        if name == "run":
            p.add_argument("--results-root")
            p.add_argument("--weights-root")
            p.add_argument("--device", default="auto")
            p.add_argument("--seeds")
            p.add_argument("--epochs", type=int)
    p = sub.add_parser("train")
    p.add_argument("--dataset", required=True)
    p.add_argument("--sample", required=True)
    p.add_argument("--config", default=str(routing.DEFAULT_CONFIG))
    p.add_argument("--data-root")
    p.add_argument("--results-root")
    p.add_argument("--weights-root")
    p.add_argument("--device", default="auto")
    p.add_argument("--seeds")
    p.add_argument("--epochs", type=int)
    args = parser.parse_args()

    if args.command == "prepare":
        decision = prepare(
            args.input,
            args.dataset,
            args.sample,
            clusters=args.clusters,
            label_key=args.label_key,
            eval_mask_key=args.eval_mask_key,
            spatial_key=args.spatial_key,
            expression_mode=args.expression_mode,
            config_path=args.config,
            data_root=args.data_root,
        )
        print(json.dumps(decision["route"], ensure_ascii=False, indent=2))
        return
    if args.command == "run":
        command = [
            sys.executable,
            "-u",
            "-m",
            "src.routed_entry",
            "prepare",
            "--input",
            args.input,
            "--dataset",
            args.dataset,
            "--sample",
            args.sample,
            "--label-key",
            args.label_key,
            "--eval-mask-key",
            args.eval_mask_key,
            "--spatial-key",
            args.spatial_key,
            "--expression-mode",
            args.expression_mode,
            "--config",
            args.config,
        ]
        if args.clusters is not None:
            command.extend(["--clusters", str(args.clusters)])
        if args.data_root:
            command.extend(["--data-root", args.data_root])
        environment = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
        environment["PATH"] = (
            str(Path(sys.prefix) / "Library/bin")
            + os.pathsep
            + environment.get("PATH", "")
        )
        process = subprocess.run(
            command,
            cwd=ROOT,
            env=environment,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        if process.stdout:
            print(process.stdout, end="", flush=True)
        if process.returncode:
            raise RuntimeError("Routed-data preparation subprocess failed")
    train_selected(
        args.dataset,
        args.sample,
        config_path=args.config,
        data_root=args.data_root,
        results_root=args.results_root,
        weights_root=args.weights_root,
        device=args.device,
        seeds=_parse_seeds(args.seeds),
        epochs=args.epochs,
    )


if __name__ == "__main__":
    main()


__all__ = ["prepare", "train_selected"]
