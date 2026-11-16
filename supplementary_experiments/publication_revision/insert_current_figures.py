"""Embed verified current SVG figures with Office-compatible PNG fallbacks."""
from pathlib import Path
from copy import deepcopy
import json,hashlib
from zipfile import ZipFile
from lxml import etree
from PIL import Image
from docx import Document
from docx.shared import Mm,Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.part import Part
from docx.opc.packuri import PackURI
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from word_svg_compat import normalize,spatial_tiles,pad_left

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'results/manuscript/SpaSRD_ESGR正文统一SiDMGF对照版.docx'
TARGET=ROOT/'results/manuscript/SpaSRD_ESGR最新结果插图版.docx'
FIG=ROOT/'results/figures/publication'
manifest=json.loads((FIG/'figure_manifest.json').read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert manifest['sidmgf_main']=='SiDMGF-full'
assert len(manifest['methods'])==14 and manifest['methods'].count('SiDMGF')==1
assert len(manifest['sources'])==1050
assert not any(r['method']=='SiDMGF-spatial' for r in manifest['sources'])
verified={r['path']:r['sha256'] for r in manifest['files']}
for p,h in verified.items():assert sha(ROOT/p)==h,p

figures=[
 ('SpaSRD_framework_preview','图1 SpaSRD模型框架',
  'D路径通过带重启传播调节区域背景的整合范围；S路径组织共同表示与门控差异表示，由共同表示承担邻接重建。ESGR在训练前选择路径。当前S配置采用差异幅度与选择性一致性约束，其作用见图8。作者框架图按提供版本保留。',False),
 ('Fig2a_distributions','图2 各方法在四类核心数据上的ARI分布',
  '箱线表示中位数、四分位区间及1.5倍四分位距内的须，散点展示全部观测。DLPFC每点为一张切片的五seed平均峰值ARI，共12点；其余数据每方法五个seed。SiDMGF为保留通路图及融合结构的完整模型。',True),
 ('Fig2b_violins','图2（续）ARI分布的小提琴展示',
  '与图2使用相同观测、方法顺序和配色。小提琴为描述性核密度估计，箱线与散点分别显示分位信息和实际观测。DLPFC按切片汇总，其余数据展示随机初始化间的变化。',True),
]
for number,s,label in [(3,'151507','DLPFC代表切片151507'),(4,'human_breast_cancer','HBC'),(5,'starmap','STARmap'),(6,'osmfish','osmFISH')]:
    text='A，参考分区。B，各方法固定seed 0的保存预测，颜色按参考区域匹配。C，各方法重复实验ARI分布；DLPFC为12切片的五seed均值，其余为五seed结果。各方法的评价与聚类口径同表1。'
    if s=='human_breast_cancer':text+=' SpaSRD-S使用组合约束配置，图中ARI为0.7071，五seed平均为0.7105±0.0201。'
    if s in ['151507','human_breast_cancer']:text+=' 组织学图像仅作为可视化底图。'
    figures.append((s+'_all_methods_spatial',f'图{number} {label}多方法空间域恢复',text,True))
    for page in range(1,4):
        methods=manifest['methods'][(page-1)*5:page*5]
        figures.append((f'{s}_all_methods_umap_{page}',f'图{number}（续{page}）{label}潜在表示比较',
            '本页方法依次为'+ '、'.join(methods)+'。每行左、右分别按参考区域和预测标签着色，共享该方法的UMAP投影；不同方法独立计算投影。ARI来自对应保存预测，检查点与空间分区图一致。',True))
figures.extend([
 ('Fig6_mechanism','图7 供体结构与传播权重',
  'A，KNN8跨参考区域边比例，每点为一张切片。B，各供体参考区域组成。C，供体共享配置的传播阶数权重。D，Br8100局部重启比例变化与12切片ARI中位数的关系。参考标签用于事后结构分析。',True),
 ('Fig7_HBC_ablation','图8 HBC表示分离与组合约束的作用',
  'A—B，六组架构及约束配置的峰值ARI、对应检查点边界F1。C，共同表示图重建配置下四组正则消融的域内混杂率。点及误差线为五seed均值和样本标准差，指标与表2—3一致。',True),
 ('Fig8_ESGR_validation','图9 冻结ESGR的外部选路验证',
  'A，固定D、固定S和ESGR所选路径的五seed平均峰值ARI。B，S相对于D的平均收益及训练前决定。结肠、小肠和左心室为组织学标注主验证集，带星号的脑图谱对象单列分析。',True),
])

doc=Document(SOURCE);body=doc._element.body
children=list(body)
start=next(i for i,e in enumerate(children) if e.tag==qn('w:p') and ''.join(e.itertext())=='图版与图注图版与图注') if False else next(i for i,e in enumerate(children) if e.tag==qn('w:p') and '图版与图注' in ''.join(e.itertext()))
stop=next(i for i,e in enumerate(children) if e.tag==qn('w:p') and ''.join(e.itertext()).startswith('补充方法S6'))
# Preserve the full-width section terminator immediately before S6.
anchor=children[stop-1]
assert anchor.find('.//'+qn('w:sectPr')) is not None
for e in children[start:stop-1]:body.remove(e)

def para(text='',size=9,bold=False):
    p=doc.add_paragraph(text);anchor.addprevious(p._p)
    f=p.paragraph_format;f.first_line_indent=Pt(0);f.space_before=Pt(0);f.space_after=Pt(3);f.line_spacing=1.05
    f.keep_with_next=False;f.keep_together=True;f.widow_control=True
    for r in p.runs:
        r.font.name='Times New Roman';r.font.size=Pt(size);r.bold=bold
        r._element.get_or_add_rPr().find(qn('w:rFonts')).set(qn('w:eastAsia'),'宋体')
    return p

sources=[]
ASVG='http://schemas.microsoft.com/office/drawing/2016/SVG/main'
for n,(stem,title,caption,vector) in enumerate(figures,1):
    png=FIG/(stem+'.png');svg=FIG/(stem+'.svg')
    with Image.open(png) as im:ratio=im.height/im.width
    tiled=stem in {'151507_all_methods_spatial','human_breast_cancer_all_methods_spatial'}
    width=min(178,(210 if tiled else 220)/ratio);height=width*ratio
    parts=[]
    if vector:
        assert str(svg.relative_to(ROOT)).replace('\\','/') in verified
        compatible=TARGET.parent/'qa_svg_inserted/word_svg'/svg.name
        if not compatible.exists() or compatible.stat().st_mtime < svg.stat().st_mtime:normalize(svg,compatible)
        pieces=spatial_tiles(compatible,png) if tiled else [(compatible,png,1)]
        if stem=='Fig7_HBC_ablation':
            padded,padded_png=pad_left(compatible,png)
            pieces=[(padded,padded_png,1)]
            with Image.open(padded_png) as im:ratio=im.height/im.width
            width=min(178,220/ratio);height=width*ratio
    else:pieces=[(None,png,1)]
    for k,(piece,preview,fraction) in enumerate(pieces):
        p=para();p.paragraph_format.page_break_before=(k==0);p.paragraph_format.keep_with_next=True
        p.paragraph_format.space_after=Pt(0);p.paragraph_format.line_spacing=1
        p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        run=p.add_run();run.font.size=Pt(1)
        shape=run.add_picture(str(preview),width=Mm(width),height=Mm(height*fraction))
        shape._inline.docPr.set('descr',title);shape._inline.docPr.set('title',title)
        if vector:
            partname=f'/word/media/spasrd_vector_{n:02}_{k+1}.svg'
            svgpart=Part(PackURI(partname),'image/svg+xml',piece.read_bytes(),doc.part.package)
            rid=doc.part.relate_to(svgpart,RT.IMAGE)
            blip=shape._inline.find('.//'+qn('a:blip'))
            extlist=OxmlElement('a:extLst');blip.append(extlist)
            ext=OxmlElement('a:ext');ext.set('uri','{96DAC541-7B7A-43D3-8B79-37D633B846F1}')
            svgblip=etree.Element('{'+ASVG+'}svgBlip',nsmap={'asvg':ASVG});svgblip.set(qn('r:embed'),rid)
            ext.append(svgblip);extlist.append(ext)
            parts.append(dict(embedded_part=partname.lstrip('/'),embedded_sha256=sha(piece)))
    t=para(title,size=10.5,bold=True);t.paragraph_format.keep_with_next=True
    para(caption)
    sources.append(dict(figure=title,source=str((svg if vector else png).relative_to(ROOT)).replace('\\','/'),
        sha256=sha(svg if vector else png),fallback=str(png.relative_to(ROOT)).replace('\\','/'),
        fallback_sha256=sha(png),format='SVG+PNG fallback' if vector else 'author framework PNG',
        embedded_parts=parts))

# Remove replaced images, but retain both fallback and SVG relationships.
used={e.get(qn('r:embed')) for e in doc._element.iter() if e.get(qn('r:embed'))}
for rid,rel in list(doc.part.rels.items()):
    if rel.reltype==RT.IMAGE and rid not in used:doc.part.drop_rel(rid)
base=Document(SOURCE)
tables=lambda d:[[[c.text for c in r.cells] for r in t.rows] for t in d.tables]
math=lambda d:[''.join(e.itertext()) for e in d._element.iter(qn('m:oMath'))]
assert tables(base)==tables(doc) and math(base)==math(doc)
doc.save(TARGET)
with ZipFile(TARGET) as z:
    assert sum(n.endswith('.svg') for n in z.namelist())==31
    for r in sources:
        for part in r['embedded_parts']:
            assert hashlib.sha256(z.read(part['embedded_part'])).hexdigest()==part['embedded_sha256']
(TARGET.parent/'inserted_figure_sources.json').write_text(json.dumps(dict(
    manuscript=str(TARGET.relative_to(ROOT)),source_document=str(SOURCE.relative_to(ROOT)),
    figure_manifest_sha256=sha(FIG/'figure_manifest.json'),figures=sources),ensure_ascii=False,indent=2),encoding='utf8')
print(TARGET)
print(f'Embedded {len(sources)} figure plates, including 31 Word-compatible SVG parts; {TARGET.stat().st_size/1024**2:.1f} MiB')
