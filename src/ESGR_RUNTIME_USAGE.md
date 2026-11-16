# ESGR V5 Runtime Usage

The runtime routing module is implemented by `src/routing.py`; the new-data
template is `src/routed_entry.py`. Existing model files, `src/workflow.py`, and
paper configuration files are not modified.

New-data preprocessing uses `scanpy`, which is available in the project's
`sidmgf` environment. The module imports it only inside the preparation step.

## One-command run

```powershell
python -m src.routed_entry run `
  --input C:\path\sample.h5ad `
  --dataset DatasetName `
  --sample SampleName `
  --clusters 7
```

This performs the following sequence:

1. Read the new h5ad in place without changing the source file.
2. Detect canonical integer counts or author-normalized expression.
3. Filter genes, select at most 3000 genes, and apply the frozen preprocessing.
4. Build the symmetric KNN8 adjacency and row-normalized transition matrix.
5. Compute the frozen ESGR V5 features and lock the D/S route decision.
6. Train only the selected route for the configured seeds.

The route decision is saved before training at:

```text
data/routed_inputs/<dataset>/<sample>/route_decision.json
```

## Separate preparation and training

```powershell
python -m src.routed_entry prepare `
  --input C:\path\sample.h5ad `
  --dataset DatasetName `
  --sample SampleName `
  --clusters 7

python -m src.routed_entry train `
  --dataset DatasetName `
  --sample SampleName
```

Use `prepare` when the route decision needs to be locked and reviewed before any
expensive training begins.

## Labels, evaluation mask, and cluster count

Default keys are:

- reference labels: `obs["ground_truth"]`
- evaluation mask: `obs["gt_evaluable"]`
- spatial coordinates: `obsm["spatial"]`

Override them with `--label-key`, `--eval-mask-key`, and `--spatial-key`.

If evaluable labels exist, the cluster count is inferred from that mask. If the
new data have no labels, `--clusters` is required and checkpoint selection uses
silhouette score. With labels and an evaluation mask, checkpoint selection uses
the masked ARI.

## Expression modes

`--expression-mode auto` is the default:

- nonnegative integer matrix: canonical counts preprocessing
- continuous matrix without a counts layer: author-normalized expression mode

Use `--expression-mode counts` or `--expression-mode normalized` to make this
choice explicit. The module never converts normalized expression into synthetic
counts.

## Runtime configuration

The frozen route thresholds and selected-branch profiles are in:

```text
config/esgr_v5_runtime.json
```

The route rule only selects D or S. It does not select donor-specific diffusion
parameters or perform a new within-route hyperparameter search. A local copy of
the runtime configuration can be supplied through `--config` when a controlled
branch profile is needed.

## Output placement

New files remain under existing project categories:

- prepared inputs: `data/routed_inputs/...`
- archived routed runs: `results/archived/routed/...`
- prediction arrays: `results/predictions/routed/...`
- weights: `weights/routed/...`

Completed runs validate their artifact hashes and are skipped on rerun. A route
decision or runtime configuration change cannot silently reuse a prior run.
