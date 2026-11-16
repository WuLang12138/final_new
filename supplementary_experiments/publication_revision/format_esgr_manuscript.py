"""Rename the frozen routing module and prepare an editable two-column draft.

Figures other than the author's framework are intentionally left as SVG slots.
No experiment files, thresholds, numerical results or model settings are changed.
"""
from pathlib import Path
from copy import deepcopy
import json,re,hashlib
from docx import Document
from docx.shared import Mm,Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'results/manuscript/SpaSRD_V5多方法图文统一修订稿.docx'
TARGET=ROOT/'results/manuscript/SpaSRD_ESGR双栏修订稿_待插SVG.docx'
doc=Document(SOURCE)
body=doc._element.body

# Retain text formatting and native Word equations during terminology changes.
for t in doc._element.iter(qn('w:t')):
    if t.text:
        t.text=re.sub(r'\bV5\b','ESGR',t.text).replace('V5','ESGR')
        t.text=t.text.replace('V3的17个对象','后续开发批次的17个对象').replace('V4验证中的CRC','结直肠验证批次中的CRC')
for p in doc.paragraphs:
    if p.text.startswith('Spatial domain identification must integrate'):
        for t in p._p.iter(qn('w:t')):
            t.text=t.text.replace('an expression–spatial routing module','an Expression–Spatial Guided Routing (ESGR) module')
    elif p.text.startswith('空间域识别需要整合区域表达背景'):
        for t in p._p.iter(qn('w:t')):t.text=t.text.replace('ESGR规则','表达—空间引导选路（ESGR）')
    elif p.text.startswith('基于这一问题，本文提出SpaSRD'):
        for t in p._p.iter(qn('w:t')):t.text=t.text.replace('ESGR选路模块','表达—空间引导选路（Expression–Spatial Guided Routing，ESGR）模块')
    elif p.text=='表达与空间统计驱动的ESGR选路':p.text='表达—空间引导选路'

# Remove old result images AND their legends; keep the author framework.
children=list(body)
first=next(i for i,e in enumerate(children) if e.findall('.//'+qn('w:drawing')))
stop=next(i for i,e in enumerate(children) if ''.join(e.itertext()).startswith('补充方法S6'))
anchor=children[stop]
framework=deepcopy(children[first])
for e in children[first:stop]:body.remove(e)

def add_before(text,style=None):
    p=doc.add_paragraph(text,style=style);anchor.addprevious(p._p);return p

figure_start=add_before('图版与图注', 'Heading 1')
add_before('本轮保留框架图；其余图版按以下位置插入重新生成的SVG。当前结果图不使用上一版PNG替代。')
anchor.addprevious(framework)
add_before('图1 SpaSRD模型框架','Heading 2')
add_before('D路径独立控制带重启的特征传播；S路径分解共同表示与门控差异表示，以共同表示恢复邻接。ESGR在训练前选择路径。当前S配置的差异幅度与选择性一致性约束另见图8。')

plans=[
 ('图2 四类核心数据的方法比较',['Fig2a_distributions.svg','Fig2b_violins.svg'],
  '四类数据采用固定方法顺序与配色，箱线和小提琴叠加实际观测。DLPFC每点为一张切片的五seed平均峰值ARI，共12点；其余数据每方法五个seed。报告中位数、四分位区间及1.5倍四分位距内的须。小提琴仅描述这些观测，不增加独立重复。'),
]
for num,s,label in [(3,'151507','DLPFC代表切片151507'),(4,'human_breast_cancer','HBC'),(5,'starmap','STARmap'),(6,'osmfish','osmFISH')]:
    plans.append((f'图{num} {label}空间分区与表示比较',
        [f'{s}_all_methods_spatial.svg']+[f'{s}_all_methods_umap_{k}.svg' for k in range(1,4)],
        '空间套图：A，参考分区；B，各比较方法的预测；C，重复实验ARI分布。展示固定seed 0的保存结果，各方法保持相同观测、坐标范围与点径。UMAP每行对应一种方法，左右为参考标签和预测标签，二者共享该方法的投影坐标；方法间不比较投影距离。颜色匹配只用于展示，不改变预测。'+
        (' HBC使用共同图重建组合S，图中ARI为0.7071，五seed均值为0.7105±0.0201。' if s=='human_breast_cancer' else '')))
plans.extend([
 ('图7 供体结构与传播权重',['Fig6_mechanism.svg'],
  'A，KNN8跨区域边比例；B，参考区域组成；C，有限传播的阶数权重；D，Br8100局部重启比例与12切片汇总中位数的关系。标签仅用于事后结构解释，不进入ESGR输入。'),
 ('图8 HBC表示分离与组合约束消融',['Fig7_HBC_ablation.svg'],
  'A—B，六组架构与约束设置的峰值ARI、对应检查点的边界F1；C，四组正则消融的域内混杂率。点和误差线为五seed均值及样本标准差。各项指标和表2、表3使用相同记录。'),
 ('图9 冻结ESGR的外部验证',['Fig8_ESGR_validation.svg'],
  'A，固定D、固定S与ESGR所选路径的五seed平均峰值ARI；B，S减D的实际平均收益方向及冻结选择。结肠、小肠和左心室为组织学标注主验证；脑图谱为单列的次级验证。四次均值方向一致不等于总体选路准确率为100%。'),
])
for title,files,caption in plans:
    p=add_before(title,'Heading 2');p.paragraph_format.keep_with_next=True
    p=add_before('〔SVG图版预留位置〕');p.runs[0].italic=True
    add_before(caption)
    p=add_before('图件：'+'；'.join(files))
    for r in p.runs:r.font.size=Pt(8)

# A4; 178-mm text block = two 86-mm columns + 6-mm gap.
for sec in doc.sections:
    sec.page_width=Mm(210);sec.page_height=Mm(297)
    sec.left_margin=Mm(16);sec.right_margin=Mm(16)
    sec.top_margin=Mm(18);sec.bottom_margin=Mm(18)
    sec.header_distance=Mm(8);sec.footer_distance=Mm(8)

def font(run,size=10,bold=None):
    run.font.name='Times New Roman';run.font.size=Pt(size)
    rpr=run._element.get_or_add_rPr();f=rpr.find(qn('w:rFonts'))
    if f is None:f=OxmlElement('w:rFonts');rpr.insert(0,f)
    f.set(qn('w:eastAsia'),'宋体')
    if bold is not None:run.bold=bold

for style in doc.styles:
    if style.type==1:
        style.font.name='Times New Roman';style.font.size=Pt(10)
        rpr=style.element.get_or_add_rPr();f=rpr.find(qn('w:rFonts'))
        if f is None:f=OxmlElement('w:rFonts');rpr.insert(0,f)
        f.set(qn('w:eastAsia'),'宋体')
        pf=style.paragraph_format
        pf.page_break_before=False;pf.space_after=Pt(3);pf.line_spacing=1.12
for p in doc.paragraphs:
    f=p.paragraph_format
    f.page_break_before=False;f.space_before=Pt(0);f.space_after=Pt(3)
    f.line_spacing=1.12;f.widow_control=True;f.keep_together=False
    f.left_indent=Pt(0);f.right_indent=Pt(0);f.first_line_indent=Pt(0)
    for br in list(p._p.findall('.//'+qn('w:br'))):
        if br.get(qn('w:type'))=='page':br.getparent().remove(br)
    heading=p.style.name.startswith('Heading')
    size=11 if p.style.name=='Heading 1' else 10
    if p.style.name=='Title':size=15
    if p.style.name in {'Paper Abstract','Paper Label'}:size=9.5
    if p.style.name=='Paper Reference':size=9
    for r in p.runs:font(r,size,True if heading or p.style.name=='Title' else None)
    if heading:
        f.space_before=Pt(7);f.space_after=Pt(4);f.keep_with_next=True
    else:f.keep_with_next=False
    if p.style.name=='Title':p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    elif not p._p.findall('.//'+qn('w:drawing')):p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
    # Display equations remain native Word math with readable column-size glyphs.
    for mr in p._p.findall('.//'+qn('m:r')):
        pr=mr.find(qn('w:rPr'))
        if pr is None:pr=OxmlElement('w:rPr');mr.insert(0,pr)
        sz=pr.find(qn('w:sz'))
        if sz is None:sz=OxmlElement('w:sz');pr.append(sz)
        sz.set(qn('w:val'),'18')

# Width-preserving, three-line tables span both columns and repeat headers.
for table in doc.tables:
    table.autofit=False
    cols=len(table.columns); widths=[52]+[(178-52)/(cols-1)]*(cols-1)
    for col,width in zip(table.columns,widths):col.width=Mm(width)
    for row in table.rows:
        pr=row._tr.get_or_add_trPr()
        if pr.find(qn('w:cantSplit')) is None:pr.append(OxmlElement('w:cantSplit'))
        for cell,width in zip(row.cells,widths):
            cell.width=Mm(width)
            for p in cell.paragraphs:
                p.paragraph_format.space_after=Pt(2);p.paragraph_format.space_before=Pt(2)
                p.paragraph_format.line_spacing=1.05
                for r in p.runs:font(r,8.5)
    trpr=table.rows[0]._tr.get_or_add_trPr()
    if trpr.find(qn('w:tblHeader')) is None:trpr.append(OxmlElement('w:tblHeader'))

# Continuous section boundaries carry the layout of the PRECEDING block.
base=deepcopy(body.sectPr)
def section(cols,start='continuous'):
    s=deepcopy(base)
    for old in list(s.findall(qn('w:cols')))+list(s.findall(qn('w:type'))):s.remove(old)
    t=OxmlElement('w:type');t.set(qn('w:val'),start);s.append(t)
    c=OxmlElement('w:cols');c.set(qn('w:num'),str(cols));c.set(qn('w:space'),str(round(6/25.4*1440)));s.append(c)
    return s
def break_before(e,cols,start='continuous'):
    p=OxmlElement('w:p');pr=OxmlElement('w:pPr');p.append(pr)
    spacing=OxmlElement('w:spacing');spacing.set(qn('w:after'),'0');spacing.set(qn('w:before'),'0');pr.append(spacing)
    pr.append(section(cols,start));e.addprevious(p)

intro=next(p for p in doc.paragraphs if p.text=='引言')
break_before(intro._p,1,'continuous')
# Each table caption and any attached notes stay in the full-width block.
for table in doc.tables:
    prev=table._tbl.getprevious()
    if prev is not None and prev.tag==qn('w:p'):
        start=prev
        pr=prev.get_or_add_pPr()
        keep=OxmlElement('w:keepNext');pr.append(keep)
    else:start=table._tbl
    break_before(start,2)
    end=table._tbl.getnext()
    if end is not None and end.tag==qn('w:p'):
        txt=''.join(end.itertext())
        if txt.startswith(('神经网络','* 小鼠','注：','†')):end=end.getnext()
    if end is not None:break_before(end,1)
break_before(figure_start._p,2)
figure_start.paragraph_format.page_break_before=True
break_before(anchor,1)
apr=anchor.get_or_add_pPr();apr.append(OxmlElement('w:pageBreakBefore'))
body.remove(body.sectPr);body.append(section(2))

# Only the original author framework remains embedded until new SVGs are run.
used={e.get(qn('r:embed')) for e in doc._element.iter(qn('a:blip'))}
for rid,rel in list(doc.part.rels.items()):
    if rel.reltype.endswith('/image') and rid not in used:doc.part.drop_rel(rid)
doc.save(TARGET)
(TARGET.parent/'ESGR_figure_slots.json').write_text(json.dumps([
    {'caption':title,'svg_files':files} for title,files,_ in plans],ensure_ascii=False,indent=2),encoding='utf-8')
print(TARGET)
