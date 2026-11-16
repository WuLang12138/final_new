# 论文图件统一目录

唯一推荐入口：`tutorials/05_统一参数与论文绘图.ipynb`，调用`src/publication_figures.py`。

- `publication/`：当前论文的总图、空间分区、UMAP/热力图、多方法箱线/小提琴图。主方法HBC为共同表示图重建的组合组，两个GCN使用对应匹配设置；外部方法为v2的12种。各方法固定seed 0展示，分布用全五seed，DLPFC按切片汇总。不自动选择最高分候选。
- `historical_manuscript/main/`：从原20261026论文配图目录迁来的原图。
- `historical_manuscript/external/`：从原20261027外部方法配图目录迁来的原图。这两处与既有Word内嵌图片一致，属于历史状态，不是当前结果。
- `source_data/`：供体结构与传播机制图所用的4张源表。
- `current/`、`peak/`、`framework/`：此前单方法绘图的输出，保留用于核查；当前05不从这里选择论文方案。
- `migration_manifest.json`：旧路径、新路径、文件哈希及迁移记录。

当前绘图配置与逐seed预测索引在`config/publication_figures.json`。所有路径相对于sidmgf_final；外部训练结果继续位于同级sidmgf_paper_support，未复制大型权重。该依赖会在外部结果缺失时报错，不会用旧方法结果替补。

`publication/seed_metrics.csv`与`method_summary.csv`是实际绘图的指标来源；`figure_manifest.json`记录来源和图件哈希。再次运行05，先核验预测，再复用匹配的完整图件。`FORCE_REDRAW=True`可重画，不会训练。

旧图原生成脚本：`analysis/manuscript_illustrated_20261026/build_figures.py`（主图），`analysis/manuscript_external_comparison_20261027/build_comparison_plates.py`（外部并列图）。它们只用于历史复核，输出路径已改至本目录historical_manuscript，不再写回原analysis的figures文件夹。图1旧文件由当时的框架示意图导入；当前框架由`src/figures.py::draw_framework(combined=True)`生成，显示组合约束。

迁移不改变Word已嵌入的图片。本轮更新绘图入口和文件存放，未自动替换Word中的旧图。
