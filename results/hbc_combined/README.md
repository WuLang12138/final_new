# HBC组合组绘图结果

本目录保存refined配置中control与combined两组各五seed的峰值和末轮预测、训练历史及指标报告。原始训练权重仍保存在库外hbc_detail_ablation实验目录；本绘图入口不需要权重，不启动训练，也不依赖库外文件。

- `refined/<control或combined>/seed_<seed>/`：best.npz、final.npz、history.csv、report.json。
- `refined/figures/`：已复制的五seed峰值图片；运行06后在此保存图及逐点来源。
- `config/hbc_combined_figures.json`（相对主库根）：锁定导入实验及报告哈希。

全图使用固定点位、H&E底图和论文配色；不平滑预测。区域放大图标出真实区域点位，辅助检查合并与拆分。当前仅导入refined，不自动用别的配置补齐paper。

本次导入不会改变02训练入口、05论文绘图入口或current_selection.json。
