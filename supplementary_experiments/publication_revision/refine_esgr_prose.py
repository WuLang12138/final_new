"""Revise the argument and hierarchy without changing experiments or table values."""
from pathlib import Path
import json
from docx import Document
from docx.shared import Pt, RGBColor
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.enum.text import WD_ALIGN_PARAGRAPH

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'results/manuscript/SpaSRD_ESGR双栏修订稿_待插SVG.docx'
TARGET=ROOT/'results/manuscript/SpaSRD_ESGR论述与版式精修稿.docx'
doc=Document(SOURCE)
paras=list(doc.paragraphs)

# One paragraph, one argumentative role. Experimental definitions remain in Methods/Supplement.
edits={
2: 'Spatial domain identification requires regional expression context to be integrated while preserving differences between adjacent tissue compartments. These demands vary with tissue organization and spatial sampling. We present SpaSRD, a reconstruction-based framework that couples controllable diffusion with common–differential representation decomposition. Its diffusion path separates feature transformation from restarted propagation to regulate the integration of regional context. Its separation path assigns adjacency reconstruction to a common representation and controls local variation through gated differential features and selective regularization. An Expression–Spatial Guided Routing (ESGR) module characterizes expression responses to diagnostic diffusion and neighborhood geometry to select a path before training. Under KNN8 graphs and donor-shared settings, SpaSRD achieved a median section-wise mean peak adjusted Rand index (ARI) of 0.6283 across twelve dorsolateral prefrontal cortex sections, and mean peak ARIs of 0.6498 and 0.6992 on STARmap and osmFISH. In breast cancer, combined regularization increased mean peak ARI from 0.6959 to 0.7105 and reduced within-region fragmentation. Developed on 43 objects and then frozen, ESGR selected the path with the higher five-seed mean peak ARI on four new external datasets. It matched fixed diffusion on three histology-annotated datasets; adding an atlas-reference brain dataset yielded mean gains of 0.0055 over fixed diffusion and 0.0209 over fixed separation. SpaSRD connects spatial representation design with measurable expression and sampling properties, supporting data-guided configuration for spatial domain identification.',
5: '空间域识别需要从局部观测中恢复区域表达背景，并保留相邻组织区室的分子差异。组织结构与空间采样的变化，使这两项需求在不同样本中具有不同权重。针对这一问题，本文提出SpaSRD，将可控扩散、共同—差异表示分解与表达—空间引导选路（ESGR）整合为重建式空间域识别框架。D路径分离特征变换与重启传播，调节区域背景的整合范围；S路径由共同表示承担邻接重建，通过门控差异表示及选择性约束保留局部变化；ESGR依据诊断扩散响应和邻域几何，在训练前确定表示路径。在统一KNN8及供体共享设置下，SpaSRD在12张DLPFC切片上的逐片平均峰值ARI中位数为0.6283，在STARmap和osmFISH上的平均峰值ARI分别为0.6498和0.6992。HBC中，组合约束将平均峰值ARI由0.6959提高至0.7105，并减少域内碎片。ESGR在43个开发对象上确定并冻结后，对四个新外部数据集的选择均与五seed平均峰值ARI较高的路径一致。三个组织学标注数据集上，其表现与固定D路径相同；纳入脑图谱参考数据后，四数据集等权平均分别较固定D和固定S提高0.0055及0.0209。SpaSRD将空间表示设计与可观测的数据结构相联系，为异质组织中的空间域识别提供了数据引导的配置方式。',
8: '空间转录组学将基因表达定位于组织原位，为解析皮层层次、肿瘤亚区及组织交界提供了分子依据。空间域由局部表达及其组织环境共同界定：不同细胞类型可以构成同一组织区室，同一细胞类型也可分布于多个区域[1,2]。因此，空间域识别既需要整合区域内部可共享的表达背景，也需要保留相邻区域之间的分子差异。邻域整合能够增强前者，却可能削弱后者；如何协调这两项需求，是空间表示学习的核心问题。',
11: '多模态整合、集成学习和外部参考进一步拓展了空间域识别的信息来源。SMART和GATCL利用多模态关联或对比学习，SpatialESD整合多个基础划分，GraphScrDom引入参考数据及弱监督标注[10–13]。这些方法依赖的信息条件随实验平台而变化。对于仅有转录表达与空间坐标的样本，区域恢复仍需要充分利用这两类直接观测。本研究在这一输入条件下，重点解决空间信息的整合尺度与表示职责分配问题。',
12: '两项建模需求随组织结构而变化。层状皮层具有沿区域延伸的共同表达背景，但多细胞spot的组成变化、细胞分辨率观测的局部变异及靶向面板有限的基因覆盖，都可能削弱单节点的区域信号[1,14,15]。扩展邻域整合能够为这些局部观测补充组织背景。乳腺癌切片则同时包含共享微环境、肿瘤边缘及不同病变亚区，相邻观测中的区域共性与局部差异需要被区别组织。由此，空间域识别需要两种互补能力：控制背景信息的传播范围，以及调节共享信息和局部变化在潜在表示中的职责。',
13: '针对空间背景整合与局部差异保留之间的协调问题，本文提出SpaSRD（Spatial Scale Regulation and Representation Decomposition）。SpaSRD-D采用带重启的传播算子[16]，将空间整合范围从可训练特征变换深度中分离；SpaSRD-S构建共同—差异表示分工，通过门控、重建输入分配与选择性约束协调域内一致性和局部变化，其多通道计算以ACM为技术基础[17]。为使两条路径适配不同输入，本文进一步提出表达—空间引导选路（Expression–Spatial Guided Routing，ESGR），将诊断扩散响应与邻域几何转化为训练前的路径决定。两条互补路径及其数据引导的配置方式共同构成SpaSRD。',
14: '本文围绕表示能力、结构作用和跨样本配置展开验证。首先，在统一KNN8图上比较核心数据的空间域恢复，并通过结构消融检验表示分离、图重建位置及选择性约束的作用；随后，以跨路径收益建立ESGR，在冻结规则后的新样本上检验训练前统计与路径收益方向的对应关系。',
17: '本研究采用四类公开空间转录组数据，包括12张人背外侧前额叶皮层切片、人乳腺癌组织，以及STARmap和osmFISH小鼠皮层数据。任务是在既有spot或细胞坐标上恢复空间区域。各数据的采样尺度、分子覆盖和区域结构不同，用于检验两条表示路径的适配性。',
18: '人背外侧前额叶皮层（DLPFC）数据来自Maynard等的10x Genomics Visium研究，包含3名供体的12张切片，每名供体4张[1,18]。Br5292对应151507–151510，Br5595对应151669–151672，Br8100对应151673–151676。公开表达矩阵每张含3,460–4,789个组织内spot、33,538个基因特征；本研究纳入具有参考区域注释的3,431–4,788个spot。Br5292与Br8100的分析视野覆盖六个皮层层次及白质，Br5595覆盖L3–L6及白质。供体间的取样视野和区域组成差异，为分析层状组织中的传播需求提供了比较条件。',
26: 'SpaSRD以表达矩阵和空间坐标为输入，将训练前结构诊断与重建式表示学习连接起来（图1）。ESGR在对称化KNN8图上测量表达对固定扩散的响应及邻域几何特征，确定D或S路径。所选路径学习64维节点表示，并由K-means形成空间域。D路径控制区域信息进入表示的范围；S路径分配共同和差异通道的重建职责，并约束局部变化的幅度与一致性。表达与空间邻接的联合重建为两条路径提供共同的学习任务。',
27: '核心数据比较采用供体共享的D配置及HBC组合S配置，评价传播与表示设计的作用。ESGR外部验证使用跨数据固定的内部配置：D路径为K=10、α=0.05，S路径采用共同表示图重建及组合约束。验证阶段运行D、S和空间图GCN，以测量预先选路的相对收益；应用阶段由ESGR先确定路径，再执行该路径的训练与聚类。',
33: '为在模型训练前判断输入所需的表示方式，ESGR以一次固定扩散测量区域整合对表达结构的影响。预处理表达先投影至最多32维主成分空间并中心化，形成诊断表示Z；随后在KNN8行归一化传播矩阵上执行十步、重启比例0.05的传播，得到H。Z与H之间的变化刻画节点表达对空间整合的响应，并与邻域几何共同构成选路依据。',
35: 'ESGR将表达响应与采样几何联合映射为两条路径的适配区域。残差集中度与近邻距离比描述局部变化的分布及其相对于区域背景的强度，边长变异与方差保留率则限定这些表达关系所对应的空间覆盖和整合程度。由开发集的D/S收益确定的联合判别区域，在训练前为每个样本输出唯一的路径选择。完整判别条件及参数见补充方法S7。',
36: '这一设计将两种表示需求落在可计算的输入特征上。扩散残差集中于少量节点时，共同—差异分工为局部变化提供独立的表示容量；近邻表达相似性则补充描述共享背景与全局差异的关系。几何条件使上述关系在相近的邻域覆盖下进行比较，方差保留率反映诊断整合的强度。ESGR据此连接数据特征与路径收益，而组织名称仅用于结果解释。',
37: 'ESGR以43个开发对象的D/S峰值ARI收益为依据确定，于2026年11月9日冻结。四个新验证样本的路径由表达和坐标计算，在模型训练前记录；其区域标签用于后续性能评价。规则开发、训练前决定与外部验证的记录见补充方法S7。',
53: '传播范围由步数与重启强度共同决定。较强的重启能够使多步迭代仍以短程信息为主，因此，期望传播阶数还需结合空间图的几何覆盖解释。本文进一步采用传播加权均方空间位移描述这一关系：',
63: 'SpaSRD-S针对相邻节点共享区域背景、又保留组织亚区差异的情形，设置共同与差异通道的重建分工。以ACM多通道计算为基础[17]，共同表示承接邻域聚合信息，差异表示联合邻域残差与自身特征，并经门控和投影参与表达重建与聚类。图解码器读取共同表示，使邻接恢复与差异表达组织具有不同的直接约束入口。两类通道通过共享特征变换联合优化；表示分离及图重建输入的作用由配对结构消融检验。',
68: '图解码器将表示的成对余弦相似度作为二元交叉熵的logit。损失排除对角项，正边权重取负边数与正边数之比并截断至100。D路径及常规GCN以最终表示重建图，S路径以共同表示重建图。聚类采用20次初始化的K-means，区域数按参考标注设置；以调整兰德指数（adjusted Rand index，ARI）评价预测分区与参考区域的一致性。',
69: '为减少差异通道保留的域内波动，组合配置在表达—结构重建目标上加入两项互补约束。差异幅度惩罚作用于门控后差异表示的元素均方幅度；选择性一致性在KNN8范围内筛选表达相近的邻居，对单位化最终表示施加加权距离约束。前者控制差异贡献的幅度，后者增强具有相似表达背景的局部一致性。边筛选与权重在训练前由表达数据确定，空间图重建保持作用于共同表示。实现与系数见补充方法S6。',
74: '单张切片或单个数据集报告五个种子的峰值均值及样本标准差。DLPFC先计算各切片的五seed平均峰值，再汇总12个切片均值的中位数、算术均值及切片间样本标准差。经典聚类使用单次拟合指标，并按相同数据层级汇总。',
75: '参考区域用于聚类数设定、ARI计算，以及开发阶段的配置选择和峰值选轮；训练目标为表达与空间结构重建。主结果因此采用标签辅助的峰值评价，各模型保留逐轮记录和峰值预测，固定终点结果见补充材料。ESGR的选路一致性以预先决定是否对应五seed平均峰值ARI较高的D/S路径判定。外部主比较对三个组织学标注数据集等权平均，脑图谱参考数据单列，并报告四数据集的附加汇总。',
80: '三个DLPFC供体的归一化空间边长分布相近：以最近邻间距为单位，边长中位数约为1.00–1.01，95%分位数约为1.73–1.74。相近的阵列几何下，Br5595的分析视野包含五个参考区域，L3占各切片观测的40.51%–62.43%；Br5292和Br8100则包含七个区域。区域覆盖、相对面积及边界分布由此成为解释供体间邻域混合差异的主要结构因素。',
90: '三个供体的共享配置形成不同的传播权重分布（图7）。Br5292采用K=15、α=0.04，期望传播阶数约为10.99，对应较宽的区域背景整合。Br8100采用K=4、α=0.0075，期望阶数约为3.93，有限的传播上限与其较高的跨区域边比例相适应。Br5595采用K=20、α=0.20，通过持续重启使期望阶数保持在约3.95。后两者以不同方式形成接近的平均传播阶数，体现了传播上限与初始表示保留的互补调节作用。',
95: '乳腺癌分区对表示与重建协同设计的需求',
96: 'HBC编码器比较揭示了表示能力与重建目标之间的适配需求。在固定KNN8及配对训练条件下，空间图GCN、可控扩散编码器、GATv2和ACM式多通道编码器的平均峰值ARI分别为0.6865、0.6751、0.6690和0.6048。注意力[24]和多通道机制在原重建安排下均未带来提升，促使后续设计将差异提取与重建职责共同考虑。',
99: '六组配对结构消融检验了表示分离与图重建输入的作用（表2，图8A—B）。在最终融合表示重建图、未加入两项正则的条件下，分离架构的平均峰值ARI为0.7163±0.0059，非分离ACM式结构为0.6936±0.0156。共同—差异分离及其门控、投影结构因此在相同重建入口下改善了区域一致性。',
103: '图重建位置进一步改变了组合约束的作用。未加入两项正则时，融合表示和共同表示重建图的ARI分别为0.7163和0.6959；加入组合约束后，两者为0.7111和0.7105，差距缩小至0.0006。此时共同表示配置的边界F1为0.4373，融合表示配置为0.3968。两组结果表明，重建输入决定了正则约束对整体分区与边界恢复的不同影响。',
111: '组合约束的收益与图重建位置相互关联：共同表示配置的ARI由0.6959提高至0.7105，融合表示配置则由0.7163变为0.7111。共同表示组合方案对应较高的边界F1，融合表示无约束方案对应较高的总体ARI；两者揭示了结构一致性与局部区域恢复之间不同的优化侧重。',
112: '传播权重的局部响应',
113: '在KNN8及供体共享设置下，Br8100的局部敏感性实验比较了四个重启比例邻域候选，并保留α=0.01的参照，各组覆盖四张切片及五个种子。K=4时，α由0.01调整为0.0075，DLPFC总体中位数由0.6273变为0.6283，算术均值提高约0.0002。较小的局部增量表明，在该参数邻域内，主要传播行为已由有限步数及较弱重启共同确定。',
116: 'ESGR联合表达响应与采样几何，在开发集合中建立统计特征与路径收益的对应关系。43个开发对象中，41个对象的路径决定与D/S收益方向一致；按14组等权汇总，所选路径的平均峰值ARI为0.5090，固定D和固定S分别为0.4975和0.4661。开发集合包含全部用于规则修订的对象，独立验证在规则冻结后进行。',
117: '四个新外部对象共完成60次运行。ESGR在训练前为结肠、小肠和左心室确定D路径，为成年小鼠脑02A确定S路径；四次决定均对应各数据集五seed平均峰值ARI较高的路径（表4，图9）。',
120: '* 小鼠脑以图谱配准区域为参考，其余三项采用组织学标注。全部spot参与构图和聚类，有效标注spot参与ARI评价。ESGR列报告所选路径的结果；GCN为同KNN8空间图参照。',
122: '三个组织学数据集上，ESGR的平均峰值ARI为0.3956，与固定D一致，固定S及空间图GCN分别为0.3678和0.3626。脑图谱参考样本02A上，S、D和GCN分别为0.6092、0.5872和0.5426；ESGR识别出与前三类组织不同的路径收益方向。四数据集等权汇总时，ESGR为0.4490，固定D、固定S及GCN分别为0.4435、0.4282和0.4076。',
123: '路径选择与区域恢复的难度呈现不同变化。结肠所选D的ARI为0.4296，空间图GCN为0.4354；左心室所选路径的ARI为0.0337，其1,166个spot中1,112个属于心肌，血管与脂肪组织分别仅含34和20个spot。高度不均衡的区域组成仍使少数组织区的恢复成为难点。',
125: 'SpaSRD围绕区域背景整合与局部差异保留，形成传播控制、表示分工和训练前选路的连续设计。D路径使空间整合范围能够独立于可训练变换深度调整；S路径为共享背景与局部变化分配不同的重建职责；ESGR将两种建模方式与样本的表达响应及空间采样联系起来。统一KNN8提供共同的邻域定义，固定诊断扩散则提供比较输入响应的测量尺度，使跨样本配置建立在可重复计算的数据特征上。',
126: 'DLPFC供体比较说明，传播行为需要联系区域组成与边界结构解释。相同平台及相近阵列几何下，Br8100较高的跨区域连接比例与有限传播上限相适应；Br5595通过较强重启抑制远阶贡献，Br5292则采用较宽的传播范围。供体内共享参数将这种配置延伸至相关切片，也使传播阶数分布成为连接模型与组织结构的分析对象。',
127: 'HBC消融进一步表明，局部差异的利用取决于表示组织与重建目标的协同。分离结构在融合表示重建图的条件下提高了ARI；共同表示重建图与组合约束结合后，获得较高的边界F1并减少域内碎片。部分小区域的IoU下降提示，增强区域一致性时仍需保持对少数亚区的分辨能力。后续结构设计可围绕这一尺度冲突，进一步协调邻域约束与小区域信息保留。',
128: 'ESGR将两条路径的适配关系表述为输入统计与模型收益的联系。残差集中度反映空间整合对不同节点的影响分布，近邻距离比刻画局部相似性，边长变异与方差保留描述其采样和传播条件。脑图谱02A虽仅含三个参考大区，仍由S路径取得较高ARI，说明区域数量不足以概括表示需求；表达变化如何分布于空间图上，是更直接的分析对象。',
129: '冻结验证在四个新对象上复现了D/S平均峰值收益方向：三个组织学样本保留固定D的表现，脑图谱样本由S获得增益。当前外部覆盖仍有限，后续应在保持规则冻结的条件下，扩展采样几何与表达分布，并结合不同判别区域检验跨组织适用性。传播参数的供体共享分析与固定内部参数的选路验证，共同构成从模型配置到样本适配的两层证据。',
131: '本文提出SpaSRD，通过可控传播、共同—差异表示分解及ESGR训练前选路，协调空间域识别中的区域背景整合与局部差异保留。核心数据比较与结构消融揭示了传播范围、表示组织和重建职责的不同作用，冻结后的外部验证进一步支持表达—空间统计对路径收益方向的判别。SpaSRD由此提供了将空间表示学习与数据引导配置结合的方法框架。',
138: 'DLPFC数据与注释由spatialLIBD提供；HBC表达和坐标来自10x Genomics，20区注释来自SEDR公开仓库；STARmap整理对象来自SiDMGF引用的Figshare条目；osmFISH来自Linnarsson实验室[18–22]。ESGR外部样本来自RRST、人心脏细胞图谱及成年小鼠脑空间图谱[25–27]。代码按相对路径组织，并保存配置、峰值权重、逐seed结果、方法适配记录与冻结选路文件。外部验证同时记录训练前决定、输入校验值及60次运行结果，详见补充方法S7。公开仓库地址及永久归档标识符将在发布时补充。',
183: '四类数据采用固定方法顺序与配色。DLPFC每点为一张切片的五seed平均峰值ARI，共12点；其余数据每方法五个seed。箱线标示中位数、四分位区间及1.5倍四分位距内的须，小提琴与散点共同显示相应观测的分布。',
211: 'A，固定D、固定S与ESGR所选路径的五seed平均峰值ARI；B，S相对于D的平均收益及冻结选路决定。结肠、小肠和左心室构成组织学标注主验证集，脑图谱对象单列分析。',
219: '冻结判别区域由以下三个条件的并集定义：R≥4.202386192846328且C≤0.285；R≥4.202386192846328、C≤0.325且V≥0.24；N≤0.49352821818117385且C≤0.300。该区域对应S，其补集对应D。代码位于sidmgf_paper_support/experiments/route_rationale_validation，规则文件为results_route_gate_v5/frozen_candidate_rule_v5.json；特征定义及验证实施分别见peak_route_discovery.py和external_v5_validation.py。',
221: '四个新对象的观测ID、基因名及空间坐标经审计均无重复。计数输入采用既定基因过滤、至多3,000个高变基因、总量归一化及不中心化尺度变换；左心室使用作者提供的连续归一化表达，选择方差最高的至多3,000个基因后进行尺度变换。每个对象的三种模型共享表达、邻接及评价掩码。全体spot参与K-means，ARI/NMI在gt_evaluable为真的观测上计算，区域类别数依次为3、5、3和3。',
223: '复核来源集中在results_external_v5_newdata：predictions_before_training.json保存训练前决定，external_plan.json保存60项任务，peak_seed_results.csv与peak_summary.csv分别保存逐seed结果和汇总，validation_decision.json记录主次评价终点。主终点为三个组织学数据集等权平均，成年小鼠脑02A以图谱参考独立分析；四数据集等权结果为附加汇总。选路一致性在数据集五seed均值层面统计。',
}
for i,text in edits.items():
    p=paras[i]
    if i==68:
        from copy import deepcopy
        math_c=deepcopy(p._p.find(qn('m:oMath')))
        before,after=text.split('S路径以共同表示',1)
        p.text=before+'S路径以共同表示'
        p._p.append(math_c)
        p.add_run(after)
        continue
    assert not p._p.findall('.//'+qn('m:oMath')),f'Preserve native math in paragraph {i}'
    p.text=text

# Text-node-only changes preserve all inline native equations.
for p in doc.paragraphs:
    for t in p._p.iter(qn('w:t')):
        if t.text:
            t.text=t.text.replace('本项目采用行归一化图算子，是对APPNP传播思想的具体实现。','传播算子采用行归一化形式，将APPNP重启传播[16]用于空间表达的多阶整合。')
            t.text=t.text.replace('后者并非纯粹的高频滤波输出。','')
            t.text=t.text.replace('小提琴仅描述这些观测，不增加独立重复。','')
            t.text=t.text.replace('方法间不比较投影距离。颜色匹配只用于展示，不改变预测。','各方法分别计算投影，区域颜色按参考标签匹配。')
            t.text=t.text.replace('在实际用于本轮训练的KNN8图上','在训练使用的KNN8图上')
            t.text=t.text.replace('这解释了重启如何改变不同空间变化成分的保留比例，该谱响应分析刻画了重启传播的滤波行为，并为理解不同空间变化成分的保留程度提供了理论依据。','该谱响应描述了重启传播对不同空间变化成分的保留程度，为分析区域背景整合与局部差异保留提供了滤波视角。')
paras[216].text='补充方法S7 ESGR计算与验证'

# Remove editorial instructions from the manuscript, retaining figure slots.
paras[177].text=''

def face(run,size,bold=False,east='宋体'):
    run.font.name='Times New Roman';run.font.size=Pt(size)
    run.bold=bold;run.font.color.rgb=RGBColor(0,0,0)
    f=run._element.get_or_add_rPr().find(qn('w:rFonts'))
    if f is None:f=OxmlElement('w:rFonts');run._element.get_or_add_rPr().append(f)
    f.set(qn('w:eastAsia'),east)

# Default body: two Chinese characters indent, modest paragraph space.
for name in ['Normal','Body Text','First Paragraph']:
    s=doc.styles[name];s.font.size=Pt(10)
    f=s.paragraph_format;f.first_line_indent=Pt(20);f.space_before=Pt(0);f.space_after=Pt(4);f.line_spacing=1.15
for name,size,before,after in [('Heading 1',13,12,6),('Heading 2',11,10,5)]:
    s=doc.styles[name];s.font.size=Pt(size);s.font.bold=True
    f=s.paragraph_format;f.first_line_indent=Pt(0);f.space_before=Pt(before);f.space_after=Pt(after);f.keep_with_next=True

for i,p in enumerate(paras):
    if p.text.startswith(('补充方法S6','补充方法S7')):p.style='Heading 1'
    f=p.paragraph_format
    f.line_spacing=1.15;f.space_before=Pt(0);f.space_after=Pt(4)
    f.widow_control=True
    f.first_line_indent=Pt(20)
    text=p.text
    size=10;bold=False;east='宋体'
    if p.style.name.startswith('Heading'):
        level=p.style.name=='Heading 1';size=13 if level else 11;bold=True;east='黑体'
        f.space_before=Pt(12 if level else 10);f.space_after=Pt(6 if level else 5)
        f.first_line_indent=Pt(0);f.keep_with_next=True;p.alignment=WD_ALIGN_PARAGRAPH.LEFT
    elif p.style.name=='Title':
        size=15;bold=True;f.first_line_indent=Pt(0);f.space_after=Pt(12)
    elif p.style.name=='Paper Label':
        size=11;bold=True;east='黑体';f.first_line_indent=Pt(0);f.space_before=Pt(8);f.space_after=Pt(4);f.keep_with_next=True
    elif p.style.name=='Paper Abstract' or i in (5,):
        size=9.5;f.line_spacing=1.12;f.first_line_indent=Pt(0)
    elif p.style.name=='Table Caption Paper' or text.startswith(('表S1','表S2','表S3')):
        size=9;bold=True;f.first_line_indent=Pt(0);f.space_before=Pt(6);f.space_after=Pt(4);f.keep_with_next=True
    elif 148<=i<=174:
        size=8.5;f.first_line_indent=Pt(0);f.line_spacing=1.03;f.space_after=Pt(2)
    elif 176<=i<=212 or p.style.name=='Compact':
        size=9;f.first_line_indent=Pt(0)
    elif i in (86,120):
        size=8.5;f.first_line_indent=Pt(0);f.line_spacing=1.1
    # Display equations and continuous-section markers must not acquire body indents.
    if p._p.findall('./'+qn('m:oMathPara')) or p._p.findall('.//'+qn('w:drawing')) or not text:
        f.first_line_indent=Pt(0)
    if not text:
        f.space_before=Pt(0);f.space_after=Pt(0)
    if 176<=i<=212 and text and not text.startswith('图件：'):
        f.keep_with_next=True
        f.keep_together=True
    if i==224:
        f.page_break_before=True
    if 148<=i<=174 or text.startswith('图件：') or p.style.name=='Compact' or i in (219,220,223):
        p.alignment=WD_ALIGN_PARAGRAPH.LEFT
    for r in p.runs:face(r,size,bold,east)

for table in doc.tables:
    for ri,row in enumerate(table.rows):
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.first_line_indent=Pt(0)
                for r in p.runs:face(r,8.5,ri==0)

# Numerical and mathematical preservation gates.
source=Document(SOURCE)
tables=lambda d:[[[c.text for c in r.cells] for r in t.rows] for t in d.tables]
math=lambda d:[''.join(x.itertext()) for x in d._element.iter(qn('m:oMath'))]
assert tables(doc)==tables(source)
assert math(doc)==math(source)
doc.save(TARGET)
print(TARGET)
