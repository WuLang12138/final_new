# 论文机制证据与文稿整理

这些工具不参与模型训练或预测。统一绘图入口仍是 `tutorials/05_统一参数与论文绘图.ipynb`。

- `mechanism_evidence.py`：读取已完成的 HBC 六组结构消融、四组正则消融及冻结 V5 外部验证结果，生成机制证据图，不启动训练。输入位于 `results/figures/source_data`；原始来源及校验值见同目录的 `mechanism_provenance.json`。
- `publication_revision/revise_manuscript.py`：从历史 V5 稿件更新多方法叙述和图片，输出 `results/manuscript/SpaSRD_V5多方法图文统一修订稿.docx`。这是本项目的文稿整理辅助工具，历史源稿不随模型预测代码要求发布。
- `publication_revision/export_framework.ps1`：通过本机 PowerPoint 将作者的框架 PPTX 导出预览 PNG。修改框架原稿后应重新执行此脚本；自动绘图不会覆盖作者的 SVG/PPTX。
- `publication_revision/export_word.ps1` 与 `render_revision.py`：本机 Word 排版检查工具，不是训练依赖。

## 图件使用

当前论文图片统一在 `results/figures/publication`，`figure_manifest.json` 记录当前图件和实际实验输入。四个 `*_all_methods_spatial` 包含 A 参考分区、B 各方法空间分区、C 重复实验箱线分布；`*_all_methods_umap_1/2/3` 包含所有比较方法的参考标签/预测标签配对投影。

稿件图号与文件名对应：图1为作者框架；图2为 `Fig2a/2b`；图3—6依次为 DLPFC、HBC、STARmap、osmFISH 的多方法图；图7为 `Fig6_mechanism`；图8为 `Fig7_HBC_ablation`；图9为 `Fig8_V5_validation`。保留既有机制图文件名以避免断开其他引用。

之前只并列 SpaSRD 与两类 GCN 的六组图片移至 `results/figures/supplementary_controls`，不再进入当前主图清单。历史嵌图归档与当前主图分开，不能通过目录中最晚修改时间替代清单选择。

HBC 主图固定使用共同表示重建图的组合约束组，五 seed 平均峰值 ARI 为 0.7105；不是旧的 paper/refined 基础 S，也不是 0.7163 的融合图重建无约束消融组。配置与检查点信息保存在清单和图注，不写进图内标题。

现有 `src/marker_figures.py` 仍可绘制指定基因的观察表达与解码期望，但历史 HBC 解码图使用基础 S 权重，不能作为当前组合组图直接沿用。本次主图未纳入这些历史重建图，也没有把 SiDMGF 专属通路图移植到不使用信号图的 SpaSRD。区域表达差异是通用生物学展示；解码期望则需要匹配当前权重，并不能单独证明生物学机制。
