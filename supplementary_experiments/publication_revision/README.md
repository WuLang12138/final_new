# ESGR 双栏稿与矢量图排版

当前插图稿：`../../results/manuscript/SpaSRD_ESGR最新结果插图版.docx`。文字底稿为 `SpaSRD_ESGR正文统一SiDMGF对照版.docx`，保留原文件。

`insert_current_figures.py` 核验本轮 `figure_manifest.json` 后插入图1—图9及续图，共22个图版。`inserted_figure_sources.json` 记录原图与嵌入图的哈希。Word兼容处理只展开字体声明并简化重复的散点绘图结构，原始发表图件不改写。

SiDMGF展示修订由 `unify_sidmgf_main.py` 从论述精修稿生成。正文SiDMGF只对应既有完整多图运行，内部来源ID仍为 `SiDMGF-full`，不改权重或历史路径。空间图对照、原论文指标和编码器诊断移入补充方法S8、表S4/S5；原表S1/S2/S3保留。外部选路主表保留D/S，空间图GCN完整列存于S5，未将其冒充完整SiDMGF。

2026-11-14 修订由 `refine_esgr_prose.py` 从上一份双栏稿生成：正文两字缩进，一级标题13 pt、二级标题11 pt加粗，调整节间距；摘要、引言、方法和讨论围绕问题、设计及证据重写。正文选路阈值移至补充方法，原有7张表数值、33个公式及27条参考文献保持不变。该文字底稿当时渲染13页，插图稿已另行完成图件嵌入。

## 名称与科学内容

正文将历史 V5 规则命名为**表达—空间引导选路（Expression–Spatial Guided Routing，ESGR）**。这是 SpaSRD 的训练前选路模块，沿用已冻结的规则；没有更换阈值、训练配置、模型、数据或验证结果。为保持可追溯性，补充方法中的原始文件名、历史版本路径和哈希不改名。

插图稿保留统一SiDMGF文字底稿的9张表及33个原生Word公式。正文插图采用本轮已完成的结果，不再使用旧的占位图。

## Word 排版

A4，正文左右双栏，每栏 86 mm，栏间 6 mm；标题、摘要、宽表和图版说明通栏。正文采用中文宋体与英文 Times New Roman，宽表保留三线表，公式仍可编辑。此版本为阅读与后续 LaTeX 转换准备，不是对期刊初投稿强制格式的声明。

参考：
- [Bioinformatics author guidelines](https://academic.oup.com/bioinformatics/pages/author-guidelines)：LaTeX 双栏版式及 86 mm 栏宽。
- [Briefings in Bioinformatics author guidelines](https://academic.oup.com/bib/pages/author-guidelines)：初投稿格式、图件和图注要求。

`format_esgr_manuscript.py` 从已保存的上一稿生成当前 Word；它不是训练或绘图依赖。`export_word.ps1` 和 `render_revision.py` 仅用于本地 Word/PDF 分页核验。

## 重新生成图件

在 sidmgf 环境从首格运行 `../../tutorials/05_统一参数与论文绘图.ipynb`。代码和样式签名改变会自动重画，不必修改 `FORCE_REDRAW`。不重新训练；可复用既有 UMAP 缓存。输出统一位于 `../../results/figures/publication`，以 `figure_manifest.json` 为本轮有效图件清单。

- 主逻辑：`../../src/publication_figures.py`
- 统一样式与矢量导出：`../../src/publication_style.py`
- 调整颜色：`../../config/publication_style.json`
- 消融与外部选路图：`../mechanism_evidence.py`

正文方法对比使用固定顺序与配色，保留14项方法（SpaSRD及13项比较方法）。主图SiDMGF只有一个名称、一个来源，均为完整多图结果。空间图采用A参考分区、B多方法分区、C重复实验分布，15幅空间面板按5行3列排列；UMAP每页最多5行，末页4行，每行参考标签与预测标签共享同一方法的投影。散点不连seed线，不改变标签、不补空白点、不平滑预测。

`05`仍核验原有1125份预测来源，筛出1050份正文记录；空间图对照保存在 `results/figures/supplementary_controls/sidmgf_control_seed_metrics.csv` 和 `sidmgf_control_summary.csv`。完整模型、空间图及文献参照的四数据表为同目录 `sidmgf_reference_comparison.csv`。正文 `method_summary.csv` 显示SiDMGF，源预测索引保留内部ID以便追溯。

组织区域颜色与方法颜色是两套独立编码。HBC 主图沿用组合 S，seed 0 ARI 为 0.707086，五 seed 平均为 0.710499。所有图从既有记录读数，不修改指标。

输出 SVG（Word 后续插图）、PDF（LaTeX）、PNG（Notebook 预览）。SVG 的散点、线和文字为矢量；组织学照片仍为位图，放大清晰度受原图分辨率限制。默认显示 PNG 预览，避免浏览器加载大型矢量套图时占用过多内存。作者框架 SVG/PPTX 保持原样。

本轮外部验证图改名为 `Fig8_ESGR_validation.svg`。旧 `Fig8_V5_validation.*` 即使仍在目录中，也不进入新清单。原历史 CSV 保留 `v5_validation.csv` 名称，不影响重画。

配图组织参考 [STAGATE](https://www.nature.com/articles/s41467-022-29439-6) 的空间分区、重复结果与表示对照，以及 [Proust](https://pmc.ncbi.nlm.nih.gov/articles/PMC12212350/) Fig. 3 的多方法空间图、UMAP 和统计图组合。只借鉴展示结构，不移用其他方法的实验结果或专有通路解释。

## 本轮核验

上一轮绘图核验中，1125 份已有预测记录完成来源、标识与指标核验；代码及 Notebook 语法检查通过。已试绘 HBC 多方法空间套图、三页 UMAP、总体箱线/小提琴及三幅机制图。非组织照片图的 SVG 未含位图图层。Word 经本机 Word 导出并逐页检查。正式全套重画由用户运行上述 Notebook；2026-11-14的文字与版式修订没有更改绘图或训练代码。

## 最新插图交付核验

2026-11-14：已插入22个图版（图1—图9及续图），共34页。除作者框架预览外，结果图均嵌入SVG；DLPFC与HBC大型空间套图按原有行切成矢量条带，绕过Word单图复杂度限制，不改变面板顺序、预测或原始图件。字体声明展开与散点路径简化只作用于Word兼容副本；原始SVG保留在publication目录。嵌入图件与来源哈希见 `results/manuscript/inserted_figure_sources.json`。文字、9张表和33个公式与统一SiDMGF底稿一致。
