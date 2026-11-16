"""Assemble the manuscript with verified multi-method publication figures."""
from pathlib import Path
from copy import deepcopy
import json,hashlib
from zipfile import ZipFile
from docx import Document
from docx.shared import Inches,Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT.parent/'analysis/manuscript_route_v5_20261111/SpaSRD_V5选路机制整合修订稿.docx'
FIG=ROOT/'results/figures/publication'
OUT=ROOT/'results/manuscript';OUT.mkdir(exist_ok=True)
TARGET=OUT/'SpaSRD_V5多方法图文统一修订稿.docx'
doc=Document(SOURCE)
for p in doc.paragraphs:
    t=p.text
    if t.startswith('本研究采用SiDMGF基准中的四类公开数据'):
        p.text=t.replace('本研究采用SiDMGF基准中的四类公开数据','本研究采用空间域识别研究中常用的四类公开数据')
    elif t.startswith('供体内共享配置下，DLPFC的12切片'):
        p.text='供体内共享配置下，DLPFC的12切片平均峰值ARI中位数为0.6283，切片间标准差为0.0660，算术均值为0.5936。表1中各比较方法的汇总中位数为0.3285—0.5585，说明该配置在本研究统一协议下取得最高的总体分区一致性。逐切片结果与配对结构参照见表S1；完整重复分布和代表切片的空间分区见图2—3。'
    elif t.startswith('STARmap与osmFISH在相同的KNN8空间图协议'):
        p.text='STARmap与osmFISH采用相同的KNN8空间图协议和共享传播配置，SpaSRD-D的平均峰值ARI分别为0.6498±0.0244和0.6992±0.0149，均为表1本研究统一协议比较中的最高值。不同方法在两类成像数据上的相对表现并不一致，说明测量基因面板、采样密度和区域结构仍会影响表示方法的适配性。多方法空间分区、潜在表示及重复实验分布见图5—6。'
    elif t.startswith('在统一空间图协议下，本文完成12种外部方法'):
        p.text='在统一空间图协议下，本文完成12种外部方法在15个对象、五个随机种子上的900项实验，并纳入空间图及多图重建参照。比较覆盖经典表达聚类、图卷积、图注意力及多图表示方法，各方法基于官方实现并记录输入适配范围。SpaSRD在四类核心数据上取得本研究比较中的最高汇总ARI（表1）。空间分区图展示不同方法对区域边界与内部连续性的恢复，分布图则呈现这一结果在切片或随机初始化之间的变化。发表指标作为文献参照保留，不参与本研究重复实验分布的构造。'
    elif t.startswith('本轮在相同KNN8、500轮和五seed条件下'):
        p.text=t.replace('（表2）','（表2，图8A—B）')
    elif t.startswith('在共同表示图重建配置中，两项新增约束'):
        p.text=t.replace('（表3）','（表3，图8C）')
    elif t.startswith('冻结后的四个新对象共完成60次运行'):
        p.text=t.replace('（表4）','（表4，图9）')
    elif t.startswith('三个供体对应不同的传播权重分布'):
        p.text=t.replace('三个供体对应不同的传播权重分布。','三个供体对应不同的传播权重分布（图7）。')
    elif t.startswith('在统一KNN8、固定供体共享协议下，Br8100'):
        p.text=t.replace('完整比较了四个重启比例','检验了四个邻域候选重启比例，并保留α=0.01的参照结果')
    elif '图3a' in t or '图4a' in t:
        pass  # Original figure block is replaced below.

# Put all methods in the same sequence as plotting; published values remain a separate last row.
t=doc.tables[0]
rows=list(t._tbl)[2:] if False else list(t._tbl.findall(qn('w:tr')))
names={r.cells[0].text:r._tr for r in t.rows}
order=['SpaSRD-D/S','STAGATE','MNMST','MAEST','GraphST','SpaGCN','SEDR','Spatial-MGCN',
       'SiDMGF（空间图）','SiDMGF（多图）','DisConST-RNA','MuCST-RNA','stLearn-RNA','PCA-KMeans','SCANPY-Leiden','SiDMGF（原论文）']
for name in order:t._tbl.append(names[name])

# Replace the whole old image appendix, including old captions and two-page method layouts.
body=doc._element.body
children=list(body)
start=next(i for i,e in enumerate(children) if e.findall('.//'+qn('w:drawing')))
stop=next(i for i,e in enumerate(children) if ''.join(e.itertext()).startswith('补充方法S6'))
anchor=children[stop]
for e in children[start:stop]:body.remove(e)

figures=[('SpaSRD_framework_preview.png','图1 SpaSRD模型框架',
 '表达矩阵与空间坐标构成共享输入。D路径通过带重启传播整合区域背景；S路径组织共同表示与门控差异表示，并以共同表示恢复空间邻接。两条路径是同一框架的替代配置，并非同时运行的集成预测。当前S组合方案还施加差异幅度与表达选择性一致性正则，其消融见图8；上游V5统计选路与外部验证见方法部分及图9。'),
 ('Fig2a_distributions.png','图2 各方法在四类核心数据上的ARI分布',
 '箱线表示中位数、四分位区间及1.5倍四分位距范围内的观测，散点展示全部重复。DLPFC每点为一张切片的五seed平均峰值，共12点；其余数据每方法五个seed。方法使用固定颜色，点之间不连线。HBC为共同图重建组合S及相应匹配参照。'),
 ('Fig2b_violins.png','图2续 各方法ARI分布的小提琴展示',
 '与图2使用相同的观测和分组。轮廓为描述性核密度估计，五seed分布不代表额外生物学重复。')]
for num,s,label in [(3,'151507','DLPFC代表切片151507'),(4,'human_breast_cancer','HBC'),(5,'starmap','STARmap'),(6,'osmfish','osmFISH')]:
    figures.append((s+'_all_methods_spatial.png',f'图{num} {label}多方法空间域恢复',
        'A，参考区域。B，各方法在相同观测与坐标范围内的分区，图中ARI为固定seed 0的实际保存结果；神经网络使用已记录的主评价峰值；MNMST及经典方法使用最终拟合结果。颜色匹配仅用于展示，不改变预测或指标。C，各方法重复实验分布；DLPFC为全部12切片的五seed均值，其余为该数据集五seed。H&E仅用作可视化底图。HBC使用组合S，seed 0峰值ARI为0.7071，五seed均值为0.7105。' if s=='human_breast_cancer' else
        'A，参考区域。B，各方法在相同观测与坐标范围内的分区，图中ARI为固定seed 0的实际保存结果；神经网络使用已记录的主评价峰值；MNMST及经典方法使用最终拟合结果。颜色匹配仅用于展示。C，各方法重复实验分布；DLPFC为全部12切片的五seed均值，其余为该数据集五seed。组织学底图仅用于有配准图像的数据，不改变预测和真实缺失点位。'))
    for page in range(1,4):figures.append((f'{s}_all_methods_umap_{page}.png',f'图{num}续 {label}各方法潜在表示 第{page}组',
        '同一方法的两幅UMAP共享投影坐标，分别按参考标签与预测标签着色；标签不参与UMAP拟合。不同方法的投影独立计算，方法间坐标位置与距离不可直接比较。配置、seed及检查点与对应空间分区图一致，图中ARI来自原始聚类，而非UMAP后的重新聚类。'))
figures += [('Fig6_mechanism.png','图7 供体结构与传播权重',
 'A，统一KNN8下的跨参考区域边比例，每点为一张切片。B，各供体的参考区域组成。C，供体共享传播参数对应的阶数权重。D，Br8100局部重启参数搜索对12切片汇总中位数的影响。参考标签用于事后结构解释，不作为V5选路输入。'),
 ('Fig7_HBC_ablation.png','图8 HBC表示分离与组合约束的作用',
 'A—B，六种结构及约束配置的峰值ARI和边界F1。点及误差线为五seed均值和样本标准差，边界指标取峰值ARI对应检查点。C，共同图重建配置下四组约束消融的域内混杂率，越低越好。图据表2—3归档结果绘制，未新增训练。'),
 ('Fig8_V5_validation.png','图9 冻结V5的外部选路验证',
 'A，固定D、固定S及V5所选路径的五seed平均峰值ARI。B，实际S减D的平均收益方向，标注训练前冻结的选择。前三项为组织学标注主验证，星号小鼠脑为图谱参考次级验证。三个人工标注对象上V5与固定D相同，四对象等权增益包含图谱对象的贡献；不据此推断普遍选路准确率。')]
manifest=[]
for fn,title,caption in figures:
    path=FIG/fn
    assert path.is_file(),path
    p=doc.add_paragraph();p.paragraph_format.page_break_before=True
    shape=p.add_run().add_picture(str(path),width=Inches(6.15))
    # Bound image height, leaving room for the caption on a single page.
    if shape.height>Inches(7.25):
        ratio=Inches(7.25)/shape.height;shape.width=int(shape.width*ratio);shape.height=Inches(7.25)
    p.alignment=1
    anchor.addprevious(p._p)
    p=doc.add_paragraph(title);p.paragraph_format.keep_with_next=True
    p.runs[0].bold=True;p.runs[0].font.size=Pt(10);anchor.addprevious(p._p)
    p=doc.add_paragraph(caption);p.paragraph_format.line_spacing=1.05
    for r in p.runs:r.font.size=Pt(9)
    anchor.addprevious(p._p)
    manifest.append(dict(figure=title,path=str(path.relative_to(ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
# Remove image relationships that belonged only to the replaced appendix.
# Otherwise Word keeps obsolete figure binaries even though they are invisible.
used={e.get(qn('r:embed')) for e in doc._element.iter(qn('a:blip'))}
for rid,rel in list(doc.part.rels.items()):
    if rel.reltype.endswith('/image') and rid not in used:doc.part.drop_rel(rid)
doc.save(TARGET)
(OUT/'figure_sources.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(TARGET)
