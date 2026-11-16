"""Keep the complete SiDMGF comparator in the main text; retain controls in SI."""
from pathlib import Path
from copy import deepcopy
import csv
from docx import Document
from docx.shared import Pt,Mm
from docx.enum.section import WD_SECTION_START
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'results/manuscript/SpaSRD_ESGR论述与版式精修稿.docx'
TARGET=ROOT/'results/manuscript/SpaSRD_ESGR正文统一SiDMGF对照版.docx'
doc=Document(SOURCE);ps=list(doc.paragraphs)
original_main=deepcopy(doc.tables[0]._tbl)
original_external=deepcopy(doc.tables[3]._tbl)
controls=[r for r in doc.tables[0].rows if r.cells[0].text.startswith(('SpaSRD','SiDMGF'))]
control_rows=[[c.text for c in r.cells] for r in controls]
control_header=[c.text for c in doc.tables[0].rows[0].cells]

edits={
22: ps[22].text.split('SpaSRD只使用')[0]+'SpaSRD使用表达与坐标。正文比较中的SiDMGF保留通路活动图及融合结构，空间邻接统一采用KNN8；各方法的输入与适配设置见补充方法。',
27: '核心数据比较采用供体共享的D配置及HBC组合S配置，评价传播与表示设计的作用。ESGR外部验证使用跨数据固定的内部配置：D路径为K=10、α=0.05，S路径采用共同表示图重建及组合约束。验证阶段运行D和S，以测量预先选路的相对收益；应用阶段由ESGR先确定路径，再执行该路径的训练与聚类。补充空间图对照见表S5。',
67: '表达重建采用零膨胀负二项（zero-inflated negative binomial，ZINB）形式的损失，解码器分别估计表达均值、离散度和零膨胀参数，以描述预处理表达数据中的数值分布及零值特征。D路径的均值解码通道保留空间聚合，S路径采用逐节点的局部表达解码，使表达恢复直接依赖共同—差异联合潜在表示。',
71: '所有核心空间图采用KNN8。深度模型训练500轮，使用五个随机种子和64维聚类表示；DLPFC在每名供体的四张切片间共享传播配置，STARmap与osmFISH共享同一扩散配置。HBC以共同表示重建图的组合约束方案作为主比较配置；表2在相同训练条件下交叉改变表示架构、图重建输入与新增约束，表3单独拆分两项约束。比较方法采用已记录的受控适配设置，各方法的配置及搜索范围见补充方法。冻结选路的外部验证使用相同KNN8、500轮和五seed预算，D与S的内部参数跨数据保持不变。',
83: '在统一空间邻接协议下，本文比较13种方法在15个对象、五个随机种子上的975项运行结果。比较覆盖经典表达聚类、图卷积、图注意力及多图表示方法，各方法基于官方实现并记录输入适配范围。SpaSRD在四类核心数据上取得本研究比较中的最高汇总ARI（表1）。空间分区图展示各方法对区域边界与内部连续性的恢复，分布图呈现其在切片或随机初始化之间的变化。',
86: '神经网络按已记录的主评价峰值汇总，MNMST与经典方法使用最终拟合结果。SpaGCN采用DEC输出，MNMST采用亲和矩阵上的Leiden，其余深度方法主表使用K-means。RNA后缀表示限定输入的适配版本，MNMST采用官方无图像方案。† HBC采用组合约束S配置，SiDMGF使用相应配对训练设置；其他比较方法未进行相同规模的优化搜索。DLPFC采用供体共享传播参数；固定内部参数的ESGR外部验证见表4。',
89: ps[89].text.replace('0.3285—0.5585','0.3285—0.5559'),
120: '* 小鼠脑以图谱配准区域为参考，其余三项采用组织学标注。全部spot参与构图和聚类，有效标注spot参与ARI评价。ESGR列表示训练前决定，其结果对应所选D或S路径。含空间图对照的完整记录见表S5。',
122: '三个组织学数据集上，ESGR的平均峰值ARI为0.3956，与固定D一致，固定S为0.3678。脑图谱参考样本02A上，S和D分别为0.6092和0.5872；ESGR识别出与前三类组织不同的路径收益方向。四数据集等权汇总时，ESGR为0.4490，固定D和固定S分别为0.4435和0.4282。',
123: '区域恢复仍受组织组成影响。左心室所选路径的ARI为0.0337，其1,166个spot中1,112个属于心肌，血管与脂肪组织分别仅含34和20个spot。高度不均衡的区域组成使少数组织区的恢复成为难点。',
}
for i,t in edits.items():
    assert not ps[i]._p.findall('.//'+qn('m:oMath'))
    # Retain paragraph and run formatting on textual revision.
    if ps[i].runs:
        ps[i].runs[0].text=t
        for r in ps[i].runs[1:]:r.text=''
    else:ps[i].add_run(t)
for t in ps[68]._p.iter(qn('w:t')):
    if t.text:t.text=t.text.replace('D路径及常规GCN','D路径')
for r in list(doc.tables[0].rows):
    label=r.cells[0].text
    if label in ['SiDMGF（空间图）','SiDMGF（原论文）']:r._tr.getparent().remove(r._tr)
    elif label=='SiDMGF（多图）':r.cells[0].paragraphs[0].runs[0].text='SiDMGF'
assert [r.cells[0].text for r in doc.tables[0].rows].count('SiDMGF')==1
assert len(doc.tables[0].rows)==15

# The external GCN is spatial-only. It is not relabelled as full SiDMGF.
t=doc.tables[3]
for row in t.rows:row._tr.remove(row.cells[-1]._tc)
t._tbl.tblGrid.remove(t._tbl.tblGrid.gridCol_lst[-1])
for col,w in zip(t.columns,[52,24,51,51]):col.width=Mm(w)
for row in t.rows:
    for cell,w in zip(row.cells,[52,24,51,51]):cell.width=Mm(w)

encoder_heading=ps[95].text;encoder_text=[ps[i].text for i in [96,97]]
for i in [95,96,97]:ps[i]._p.getparent().remove(ps[i]._p)

# A separate full-width supplementary block preserves all removed comparisons.
section=doc.add_section(WD_SECTION_START.NEW_PAGE)
cols=section._sectPr.find(qn('w:cols'));cols.set(qn('w:num'),'1')
section.left_margin=Mm(16);section.right_margin=Mm(16)
def paragraph(text,style=None,bold=False):
    p=doc.add_paragraph(text,style);p.paragraph_format.first_line_indent=Pt(0)
    p.paragraph_format.space_before=Pt(6);p.paragraph_format.space_after=Pt(4)
    p.paragraph_format.line_spacing=1.1
    if style and style.startswith('Heading'):p.paragraph_format.keep_with_next=True
    for r in p.runs:
        r.font.name='Times New Roman';r.font.size=Pt(9 if not style else 11);r.bold=bold or bool(style)
        f=r._element.get_or_add_rPr().find(qn('w:rFonts'));f.set(qn('w:eastAsia'),'宋体')
    return p
paragraph('补充方法S8 SiDMGF对照与编码器诊断','Heading 1')
paragraph('正文SiDMGF对应已完成的完整多图实验，保留通路活动图与融合结构。移除通路信号图的空间图模型用于受控结构对照，原论文指标作为文献参照。三种来源在本节区分保存；文献值不构造重复实验分布。逐切片结果见表S1，HBC历史训练协议与终点记录见表S2。')
caption=paragraph('表S4 SpaSRD与SiDMGF完整模型、空间图对照及原论文指标。核心数据统计口径同表1；原论文行直接保留发表值，未补造标准差。',bold=True)
caption.paragraph_format.keep_with_next=True
from docx.table import Table
tab=Table(original_main,doc._body)
for row in list(tab.rows)[1:]:
    if not row.cells[0].text.startswith(('SpaSRD','SiDMGF')):tab._tbl.remove(row._tr)
doc._element.body.insert(len(doc._element.body)-1,tab._tbl)
paragraph('HBC的当前SpaSRD-S为组合约束配置，SiDMGF的空间图与多图模型沿用配对训练设置。SiDMGF原论文与本研究的DLPFC汇总及实验协议不同；原论文指标用于来源对照。')
caption=paragraph('表S5 冻结选路外部验证的完整记录。GCN列为同KNN8空间图模型，仅作为受控结构参照。',bold=True);caption.paragraph_format.keep_with_next=True
doc._element.body.insert(len(doc._element.body)-1,original_external)
paragraph('三个组织学数据集等权平均时，ESGR、固定D、固定S和空间图GCN的峰值ARI依次为0.3956、0.3956、0.3678和0.3626；四数据集等权结果依次为0.4490、0.4435、0.4282和0.4076。结肠所选D为0.4296，空间图GCN为0.4354；成年小鼠脑02A的空间图GCN为0.5426。')
paragraph(encoder_heading,'Heading 2')
for text in encoder_text:paragraph(text)
paragraph('解码与结构对照中，D路径及GCN的均值解码通道保留空间聚合；S路径采用逐节点表达解码，相应的局部解码GCN用于考察这一安排。空间图GCN的图损失作用于最终表示。ESGR验证实际完成D、S及空间图GCN共60次运行，正文表4聚焦D/S选择，完整来源及训练设置保留在补充方法S7。')

source=Document(SOURCE)
# Keep compact comparison tables and their captions on one page.
for table in doc.tables:
    if len(table.rows)<=8:
        for ri,row in enumerate(table.rows):
            for cell in row.cells:
                for p in cell.paragraphs:p.paragraph_format.keep_with_next=ri<len(table.rows)-1
math=lambda d:[''.join(x.itertext()) for x in d._element.iter(qn('m:oMath'))]
assert math(source)==math(doc)
for idx in [1,2,4,5,6]:
    assert [[c.text for c in r.cells] for r in source.tables[idx].rows]==[[c.text for c in r.cells] for r in doc.tables[idx].rows]
doc.save(TARGET)
out=ROOT/'results/figures/supplementary_controls';out.mkdir(parents=True,exist_ok=True)
with (out/'sidmgf_reference_comparison.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(control_header);w.writerows(control_rows)
print(TARGET)
