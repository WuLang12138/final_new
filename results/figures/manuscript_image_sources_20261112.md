# V5稿内嵌图片与05绘图来源核查

核查日期：2026-11-12。

核查Word：[SpaSRD_V5选路机制整合修订稿.docx](C:/Users/吴浪/Desktop/ST/analysis/manuscript_route_v5_20261111/SpaSRD_V5选路机制整合修订稿.docx)

文档SHA-256：`b99fa9b80b8f9131e3160215fd15e53dff328cea6953f7d0fab4c21f7e51bb78`

结论：Word中的23张图片与historical_manuscript历史图片的SHA-256全部一致，未使用publication目录中的新版图。这是上次V5文稿修订保留原稿内嵌图片所致，并非当前05仍读取旧HBC结果。

## Word实际嵌入的全部23张图片

|序号|图名|当前保存文件（迁移后）|
|---|---|---|
|1|图1　SpaSRD框架与两种编码分支|[Fig1_original.png](C:/Users/吴浪/Desktop/ST/sidmgf_final/results/figures/historical_manuscript/main/Fig1_original.png)|
|2|图2　统一空间图协议下的方法性能分布|[Fig2a_distributions.png](C:/Users/吴浪/Desktop/ST/sidmgf_final/results/figures/historical_manuscript/main/Fig2a_distributions.png)|
|3|图2（续）　重复实验分布的小提琴展示|[Fig2b_violins.png](C:/Users/吴浪/Desktop/ST/sidmgf_final/results/figures/historical_manuscript/main/Fig2b_violins.png)|
|4|图3　代表性皮层切片的空间域恢复|[Fig3a_cortex_spatial.png](C:/Users/吴浪/Desktop/ST/sidmgf_final/results/figures/historical_manuscript/main/Fig3a_cortex_spatial.png)|
|5|图3（续）　皮层潜在表示与区域对应|[Fig3b_cortex_embedding.png](C:/Users/吴浪/Desktop/ST/sidmgf_final/results/figures/historical_manuscript/main/Fig3b_cortex_embedding.png)|
|6|图3（续）　DLPFC 151507的全方法空间分区对照|[151507_all_methods_spatial.png](C:/Users/吴浪/Desktop/ST/sidmgf_final/results/figures/historical_manuscript/external/151507_all_methods_spatial.png)|
|7|图3（续）　DLPFC 151507的全方法UMAP对照（1/2）|[151507_all_methods_umap_1.png](C:/Users/吴浪/Desktop/ST/sidmgf_final/results/figures/historical_manuscript/external/151507_all_methods_umap_1.png)|
|8|图3（续）　DLPFC 151507的全方法UMAP对照（2/2）|[151507_all_methods_umap_2.png](C:/Users/吴浪/Desktop/ST/sidmgf_final/results/figures/historical_manuscript/external/151507_all_methods_umap_2.png)|
|9|图4　HBC共同协议下的细分区域恢复|[Fig4a_HBC_common.png](C:/Users/吴浪/Desktop/ST/sidmgf_final/results/figures/historical_manuscript/main/Fig4a_HBC_common.png)|
|10|图4（续）　共同协议下的表示投影与区域对应|[Fig4b_HBC_common_embedding.png](C:/Users/吴浪/Desktop/ST/sidmgf_final/results/figures/historical_manuscript/main/Fig4b_HBC_common_embedding.png)|
|11|图4（续）　独立匹配优化实验的空间分区|[Fig4c_HBC_refined.png](C:/Users/吴浪/Desktop/ST/sidmgf_final/results/figures/historical_manuscript/main/Fig4c_HBC_refined.png)|
|12|图4（续）　HBC共同协议的全方法空间分区对照|[human_breast_cancer_all_methods_spatial.png](C:/Users/吴浪/Desktop/ST/sidmgf_final/results/figures/historical_manuscript/external/human_breast_cancer_all_methods_spatial.png)|
|13|图4（续）　HBC共同协议的全方法UMAP对照（1/2）|[human_breast_cancer_all_methods_umap_1.png](C:/Users/吴浪/Desktop/ST/sidmgf_final/results/figures/historical_manuscript/external/human_breast_cancer_all_methods_umap_1.png)|
|14|图4（续）　HBC共同协议的全方法UMAP对照（2/2）|[human_breast_cancer_all_methods_umap_2.png](C:/Users/吴浪/Desktop/ST/sidmgf_final/results/figures/historical_manuscript/external/human_breast_cancer_all_methods_umap_2.png)|
|15|图5　STARmap与osmFISH跨平台分区|[Fig5a_mouse_spatial.png](C:/Users/吴浪/Desktop/ST/sidmgf_final/results/figures/historical_manuscript/main/Fig5a_mouse_spatial.png)|
|16|图5（续）　细胞分辨率数据的表示投影与区域对应|[Fig5b_mouse_embedding.png](C:/Users/吴浪/Desktop/ST/sidmgf_final/results/figures/historical_manuscript/main/Fig5b_mouse_embedding.png)|
|17|图5（续）　STARmap的全方法空间分区对照|[starmap_all_methods_spatial.png](C:/Users/吴浪/Desktop/ST/sidmgf_final/results/figures/historical_manuscript/external/starmap_all_methods_spatial.png)|
|18|图5（续）　STARmap的全方法UMAP对照（1/2）|[starmap_all_methods_umap_1.png](C:/Users/吴浪/Desktop/ST/sidmgf_final/results/figures/historical_manuscript/external/starmap_all_methods_umap_1.png)|
|19|图5（续）　STARmap的全方法UMAP对照（2/2）|[starmap_all_methods_umap_2.png](C:/Users/吴浪/Desktop/ST/sidmgf_final/results/figures/historical_manuscript/external/starmap_all_methods_umap_2.png)|
|20|图5（续）　osmFISH的全方法空间分区对照|[osmfish_all_methods_spatial.png](C:/Users/吴浪/Desktop/ST/sidmgf_final/results/figures/historical_manuscript/external/osmfish_all_methods_spatial.png)|
|21|图5（续）　osmFISH的全方法UMAP对照（1/2）|[osmfish_all_methods_umap_1.png](C:/Users/吴浪/Desktop/ST/sidmgf_final/results/figures/historical_manuscript/external/osmfish_all_methods_umap_1.png)|
|22|图5（续）　osmFISH的全方法UMAP对照（2/2）|[osmfish_all_methods_umap_2.png](C:/Users/吴浪/Desktop/ST/sidmgf_final/results/figures/historical_manuscript/external/osmfish_all_methods_umap_2.png)|
|23|图6　供体组织结构与有限传播权重|[Fig6_mechanism.png](C:/Users/吴浪/Desktop/ST/sidmgf_final/results/figures/historical_manuscript/main/Fig6_mechanism.png)|

## 生成入口与迁移

- 旧主体图生成脚本：C:/Users/吴浪/Desktop/ST/analysis/manuscript_illustrated_20261026/build_figures.py
- 旧全方法并列图脚本：C:/Users/吴浪/Desktop/ST/analysis/manuscript_external_comparison_20261027/build_comparison_plates.py
- 迁移记录：results/figures/migration_manifest.json及migration_completed.json；记录显示67个旧文件在复制并校验后从原目录删除，共106,718,820字节。
- 当前唯一入口：tutorials/05_统一参数与论文绘图.ipynb → src/publication_figures.py；固定配置为config/publication_figures.json。

## 当前论文应使用的图件

统一保存目录：[sidmgf_final/results/figures/publication](C:/Users/吴浪/Desktop/ST/sidmgf_final/results/figures/publication)

|内容|当前文件|
|---|---|
|HBC组合组空间分区|[Fig4a_HBC_combined.png](C:/Users/吴浪/Desktop/ST/sidmgf_final/results/figures/publication/Fig4a_HBC_combined.png)|
|HBC组合组UMAP及区域对应|[Fig4b_HBC_combined_embedding.png](C:/Users/吴浪/Desktop/ST/sidmgf_final/results/figures/publication/Fig4b_HBC_combined_embedding.png)|
|HBC全方法空间分区|[human_breast_cancer_all_methods_spatial.png](C:/Users/吴浪/Desktop/ST/sidmgf_final/results/figures/publication/human_breast_cancer_all_methods_spatial.png)|
|HBC全方法UMAP第1页|[human_breast_cancer_all_methods_umap_1.png](C:/Users/吴浪/Desktop/ST/sidmgf_final/results/figures/publication/human_breast_cancer_all_methods_umap_1.png)|
|HBC全方法UMAP第2页|[human_breast_cancer_all_methods_umap_2.png](C:/Users/吴浪/Desktop/ST/sidmgf_final/results/figures/publication/human_breast_cancer_all_methods_umap_2.png)|
|HBC全方法UMAP第3页|[human_breast_cancer_all_methods_umap_3.png](C:/Users/吴浪/Desktop/ST/sidmgf_final/results/figures/publication/human_breast_cancer_all_methods_umap_3.png)|
|全部方法箱线图|[Fig2a_distributions.png](C:/Users/吴浪/Desktop/ST/sidmgf_final/results/figures/publication/Fig2a_distributions.png)|
|全部方法小提琴图|[Fig2b_violins.png](C:/Users/吴浪/Desktop/ST/sidmgf_final/results/figures/publication/Fig2b_violins.png)|

HBC实际读取results/hbc_combined/refined/combined/seed_0/best.npz（其余seed为1、2、3、42）。seed 0为第320轮，ARI=0.707086；五seed均值0.710499、样本标准差0.020054。空间图GCN对应seed 0=0.702925、均值0.692164±0.018260；多图GCN对应seed 0=0.691668、均值0.691380±0.021951。

基础S原本已有共同—差异门控。当前组合组新增的是差异幅度惩罚与选择性一致性两项正则，不是首次加入门控。0.7163属于融合表示重建图的另一结构消融配置，不自动替换本组。

## 本次检查与修正

- 已核验1125份保存预测的文件哈希、参考标签、点位顺序、坐标和ARI。
- HBC主方法强制核验组合组路径及导入报告，不接受改成旧paper/refined基础S后仍标组合组。
- 输出清单限定为本入口26张图及各自PNG/PDF/SVG，避免目录中额外旧图混入。
- 图件缓存增加机制图CSV及组织学底图/配准文件校验；UMAP缓存增加参数、软件版本和点位顺序校验。
- Notebook显式显示HBC本次使用的文件、轮次、单seedARI与五seed统计。
- Notebook检查src模块来源，避免同一kernel残留其他项目模块。

运行05不训练模型，也不会自动修改Word。新图应用于Word时需同时替换图片和历史共同协议图注；旧HBC独立优化图不应混入当前组合组主比较。新版外部方法UMAP为每数据3页，旧稿仅2页，因此不能只逐文件覆盖旧稿而漏掉第3页。

本次未修改Word文件。当前图1展示两条编码路径和组合约束，未绘制V5选路模块；V5正文已单独说明。

验证完成：Notebook代码语法及项目导入通过；全部1125份预测核验通过；缺页/重复图件清单拒绝测试通过；HBC空间图重绘通过；UMAP相同参数复用及参数变更失效测试通过。新版HBC空间图与本次核验重绘的像素完全一致。
