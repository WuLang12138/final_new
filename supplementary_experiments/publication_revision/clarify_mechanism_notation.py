"""Local manuscript edits; retain all figures, tables and existing equations."""
from pathlib import Path
from zipfile import ZipFile
from copy import deepcopy
from lxml import etree as E
import json

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'results/manuscript/SpaSRD_ESGR_双路径主线修订版.docx'
TARGET=ROOT/'results/manuscript/SpaSRD_ESGR_机制定义与正文精修版.docx'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'm':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
W='{'+NS['w']+'}'; M='{'+NS['m']+'}'
def el(name,*children):
    x=E.Element(M+name)
    for c in children:x.append(r(c) if isinstance(c,str) else c)
    return x
def r(s):
    x=E.Element(M+'r');p=E.SubElement(x,W+'rPr')
    f=E.SubElement(p,W+'rFonts');f.set(W+'ascii','Cambria Math');f.set(W+'hAnsi','Cambria Math')
    t=E.SubElement(x,M+'t');t.text=s;return x
def sub(a,b):return el('sSub',el('e',a),el('sub',b))
def sup(a,b):return el('sSup',el('e',a),el('sup',b))
def norm2(*a):return el('sSubSup',el('e','‖',*a,'‖'),el('sub','F'),el('sup','2'))
def frac(a,b):return el('f',el('num',*a),el('den',*b))
def eq(*nodes):
    p=E.Element(W+'p');pr=E.SubElement(p,W+'pPr')
    sp=E.SubElement(pr,W+'spacing');sp.set(W+'before','70');sp.set(W+'after','70')
    ind=E.SubElement(pr,W+'ind');ind.set(W+'firstLine','0')
    jc=E.SubElement(pr,W+'jc');jc.set(W+'val','center')
    op=E.SubElement(p,M+'oMathPara');mp=E.SubElement(op,M+'oMathParaPr')
    j=E.SubElement(mp,M+'jc');j.set(M+'val','center')
    op.append(el('oMath',*nodes));return p
def txt(p):return ''.join(p.xpath('.//w:t/text()',namespaces=NS))
def replace(p,s):
    assert not p.xpath('.//m:oMath|.//w:drawing',namespaces=NS)
    rp=p.find('w:r/w:rPr',NS)
    for c in list(p):
        if c.tag!=W+'pPr':p.remove(c)
    rr=E.SubElement(p,W+'r')
    if rp is not None:rr.append(deepcopy(rp))
    E.SubElement(rr,W+'t').text=s
def prose(s):
    p=deepcopy(ps[35]);replace(p,s);return p
def after(p,nodes):
    for node in nodes:p.addnext(node);p=node

with ZipFile(SOURCE) as z:
    original=z.read('word/document.xml');root=E.fromstring(original)
    ps=root.findall('w:body/w:p',NS)
    changes={
    34:'ESGR通过固定扩散过程测量区域整合对表达结构的影响，并在模型训练前选择表示路径。预处理表达投影至最多32个主成分并逐维中心化，得到诊断表示Z₀。诊断表示按照下式在空间传播矩阵P上迭代，初值为H₀=Z₀，重启比例α₀=0.05，传播步数K₀=10；以下H表示诊断过程的最终输出。该过程不包含可训练参数，为不同样本提供相同的测量尺度。',
    35:'诊断采用四项无量纲统计。设eᵢ为节点i的扩散残差能量，Qₚ表示经验p分位数，E为空间无向图中每条非自环边仅计一次的边集，B为等量随机非自身节点对。令dᵢⱼ为Z₀中节点对的表达平方距离，ℓᵢⱼ为空间欧氏距离，则残差集中度R、近邻距离比N、空间边长变异系数C及方差保留率V定义为：',
    36:'残差集中度R衡量高残差节点相对于典型节点的偏离程度，近邻距离比N描述局部表达差异在全局变异中的相对大小。空间边长变异系数C刻画固定近邻数下的几何覆盖差异，方差保留率V反映诊断扩散保留的总体变异。ESGR将特征向量φ=(R,N,C,V)映射至预先确定的路径判别区域：φ属于S路径判别区域ΩS时采用表示分离，其余采用可控扩散。ΩS由开发集的D/S平均ARI收益确定；完整判别条件及参数见补充方法S7。',
    38:'ESGR的判别区域在开发阶段依据43个对象的D/S平均ARI收益确定，并在外部验证前固定。四个新验证样本仅根据表达和空间坐标生成训练前路径决定，其区域标签用于后续性能评价。规则开发、训练前决定及外部验证的记录见补充方法S7。',
    70:'SpaSRD-S进一步约束差异表示的幅度与表达相近邻居的一致性，以减少域内无关波动。令U=G⊙R为门控后差异表示，dᵣ为其维数，ẑᵢ为最终表示Z的第i行经单位范数归一化后的向量。两项约束及完整训练目标为：',
    }
    for i,s in changes.items():replace(ps[i],s)
    after(ps[34],[eq(sub('H','t+1'),'=(1−',sub('α','0'),')P',sub('H','t'),'+',sub('α','0'),sub('Z','0'),',  H=',sub('H',sub('K','0')),'.')])
    after(ps[35],[
        eq(sub('e','i'),'=‖',sub('z','0,i'),'−',sub('h','i'),'‖²,  R=',frac([sub('Q','0.90'),'(e)'],[sub('Q','0.50'),'(e)']),','),
        eq('N=',frac([sup('|E|','−1'),sub('∑','(i,j)∈E'),sub('d','ij')],[sup('|B|','−1'),sub('∑','(i,j)∈B'),sub('d','ij')]),',  ',sub('d','ij'),'=‖',sub('z','0,i'),'−',sub('z','0,j'),'‖²,'),
        eq('C=',frac(['SD(ℓ)'],['Mean(ℓ)']),',  V=',frac([norm2('H−1',sup('h̄','T'))],[norm2(sub('Z','0'))]),'.'),
        prose('其中h̄为H的逐列均值，ℓ的统计量在E上计算，SD采用总体标准差；比值分母均设10⁻¹²的下限。这里的R和C为标量统计，与S路径中的同名表示矩阵区分。随机节点对的构造见补充方法S7。')
    ])
    after(ps[70],[
        eq(sub('ℒ','amp'),'=',frac([norm2('U')],['n',sub('d','r')]),',  ',sub('ℒ','sel'),'=',frac([sub('∑','(i,j)∈E'),sub('w','ij'),'‖',sub('ẑ','i'),'−',sub('ẑ','j'),'‖²'],[sub('∑','(i,j)∈E'),sub('w','ij')]),','),
        eq(sub('ℒ','S'),'=',sub('ℒ','expr'),'+β',sub('ℒ','graph'),'+',sub('λ','amp'),sub('ℒ','amp'),'+',sub('λ','sel'),sub('ℒ','sel'),'.'),
        prose('权重wᵢⱼ在训练前由表达数据确定：仅对KNN8范围内表达相近的邻居赋予正权重，其他边的权重为零。幅度项限制差异成分的贡献，一致性项约束单位化最终表示，空间图重建仍仅作用于共同表示C。两项系数λamp与λsel分别控制约束强度；同时启用时称为组合约束，其独立作用与联合效果由四组消融检验。边权计算及系数见补充方法S6。')
    ])
    newxml=E.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True)
    with ZipFile(TARGET,'w') as o:
        for info in z.infolist():o.writestr(info,newxml if info.filename=='word/document.xml' else z.read(info.filename))
before=E.fromstring(original)
assert [E.tostring(t) for t in before.findall('w:body/w:tbl',NS)]==[E.tostring(t) for t in root.findall('w:body/w:tbl',NS)]
oldmath=[E.tostring(t) for t in before.xpath('.//m:oMath',namespaces=NS)]
newmath=[E.tostring(t) for t in root.xpath('.//m:oMath',namespaces=NS)]
assert all(t in newmath for t in oldmath)
with ZipFile(SOURCE) as a,ZipFile(TARGET) as b:
    assert all(a.read(n)==b.read(n) for n in a.namelist() if n!='word/document.xml')
print(TARGET)
print('Existing tables, equations, media and relationships retained; 6 editable math blocks added.')
