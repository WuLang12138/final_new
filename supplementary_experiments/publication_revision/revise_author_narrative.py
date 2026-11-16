"""Revise the author's prose while retaining the exact figures and equations."""
from pathlib import Path
from zipfile import ZipFile
from copy import deepcopy
import hashlib,json,re
from lxml import etree as E

ROOT=Path(__file__).resolve().parents[2]
SOURCE=Path.home()/'Desktop/SpaSRD_ESGR_anti-ai.docx'
TARGET=ROOT/'results/manuscript/SpaSRD_ESGR_双路径主线修订版.docx'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'm':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
W='{'+NS['w']+'}'

edits={
2: 'Spatial transcriptomics links molecular variation to tissue organization, but identifying spatial domains requires both regional coherence and discrimination between neighboring compartments. Neighborhood aggregation can strengthen weak regional signals while attenuating local differences, and the balance between these effects varies with tissue architecture and sampling. We present SpaSRD, a spatial domain identification framework that addresses these competing demands through two complementary representation paths. The diffusion path regulates the spatial extent of information integration independently of feature transformation, allowing regional context to supplement individual observations. The separation path assigns shared tissue context and local variation to distinct representation components, supporting adjacency reconstruction without imposing the same direct spatial constraint on all features. Expression–Spatial Guided Routing (ESGR) uses expression responses to spatial integration and neighborhood geometry to select a path before model training. In comparisons across DLPFC, STARmap, osmFISH and human breast cancer data, SpaSRD achieved the highest aggregate adjusted Rand index (ARI) among the evaluated methods under the study protocol. The diffusion path supported cortical domain recovery, whereas the separation path improved regional coherence and boundary recovery in breast cancer tissue. After its decision rule was frozen, ESGR selected the path with higher mean ARI on each of four new external datasets. These results support coordinating propagation scale and representation decomposition to recover spatial domains across different tissue organizations and measurement conditions.',
5: '空间转录组学将分子差异与组织结构联系起来，但空间域识别既要恢复区域内部的共同表达背景，又要区分相邻组织区室。邻域聚合能够增强较弱的区域信号，也可能削弱局部差异；两者之间的平衡随组织结构与空间采样而变化。针对这一问题，本文提出空间域识别框架SpaSRD，通过两条互补的表示路径协调区域整合与局部区分。可控扩散路径独立调节信息传播范围，使区域背景补充单点观测；表示分离路径将共享组织背景与局部变化分配到不同表示成分，使邻接重建不再对全部特征施加相同的直接空间约束。表达—空间引导选路（Expression–Spatial Guided Routing，ESGR）依据表达对空间整合的响应及邻域几何，在训练前确定表示路径。在DLPFC、STARmap、osmFISH和人乳腺癌数据的比较中，SpaSRD在本研究评价协议下取得了所比较方法中最高的汇总调整兰德指数（ARI）。扩散路径支持皮层区域恢复，分离路径改善乳腺癌组织的区域一致性与边界恢复。选路规则冻结后，ESGR在四个新外部数据集上均选择了平均ARI较高的路径。这些结果支持将传播尺度与表示分工共同纳入空间域建模，以适应不同组织结构和测量条件下的分区需求。',
10: '空间转录组学在组织原位测量基因表达，使皮层层次、肿瘤亚区及组织交界的分子组成能够与其空间位置对应。空间域识别旨在从这些局部观测中恢复具有共同组织背景的区域。空间域并不等同于细胞类型：不同细胞类型可以属于同一组织区室，同一细胞类型也可分布于多个区域[1,2]。因此，分区模型既需要识别邻近观测共享的表达背景，也需要保留区分相邻组织区域的分子变化。如何在同一空间图上协调这两类信息，是空间域表示学习的核心问题。',
11: '直接对表达特征应用K-means、Louvain或Leiden等聚类方法，可以识别转录相似的观测，却未必形成空间连续的组织区域。空间感知方法将邻域关系纳入这一过程：BayesSpace以空间先验改善区域一致性，SpatialPCA在降维中建模空间相关性[3,4]，BANKSY则联合建模观测自身的表达及其邻域背景，并调节邻域信息的贡献[2]。这些工作说明，空间信息参与表示构建的方式，会直接影响组织区域的恢复。',
12: '图神经网络进一步将空间邻接与特征学习相结合。SpaGCN整合表达、空间坐标和组织学信息，STAGATE通过图注意力调整邻居贡献，GraphST利用自监督学习优化空间表示[5–7]。SpatialDG和SiDMGF分别引入表达图或信号图，提供互补的关系信息[8,9]。在基于图重建的表示学习中，仍需处理两个相互关联的问题。其一，常规图卷积将特征变换与邻域传播逐层耦合，扩大信息覆盖范围往往伴随变换深度的增加。其二，从完整嵌入恢复空间邻接，会使同一表示同时承担空间接近关系与表达差异的建模任务。组织交界两侧的观测虽然相邻，其分区依据却可能来自需要保留的表达差异。',
13: '多模态整合、集成学习和外部参考为这一任务提供了其他信息来源。SMART和GATCL利用多模态关联或对比学习，SpatialESD整合多个基础划分，GraphScrDom引入参考数据及弱监督标注[10–13]。这些方法扩展了空间域识别可利用的证据，但可获得的组织学、组学和参考信息随平台与样本而变化。对于仅以转录表达和空间坐标为输入的模型，如何整合区域背景、如何在表示内部保留局部差异，仍是需要直接解决的建模问题。',
14: '组织结构与测量条件使上述问题具有不同侧重。层状皮层的表达背景沿组织区域延伸，但多细胞spot的组成变化、细胞尺度的局部变异及靶向面板有限的基因覆盖，均可能削弱单点观测的区域信号[1,14,15]。这类数据需要利用邻域补充组织背景，同时控制传播跨越区域边界的程度。乳腺癌切片则同时包含健康组织、肿瘤边缘和不同病变亚区，相邻观测可能共享部分微环境，又保留区分亚区的表达变化。此时，仅增强局部一致性不足以处理区域共性与差异的并存，还需要在潜在表示中为两者设置不同的表达空间与重建职责。',
15: '基于这些需求，本文提出SpaSRD（Spatial Scale Regulation and Representation Decomposition），将可控扩散与共同—差异表示分解组织为同一框架内的两条互补路径。SpaSRD-D采用带重启的传播算子[16]，使区域背景的整合范围独立于可训练特征变换的深度，并持续保留节点自身的学习表示。SpaSRD-S通过多通道表示计算[17]区分共享背景与局部变化，由共同表示承担空间邻接重建，使差异表示参与表达恢复和分区，而不直接承担同一图重建约束。表达—空间引导选路（Expression–Spatial Guided Routing，ESGR）进一步将这两种建模方式与样本特征联系起来，依据表达对空间整合的响应及邻域几何，在模型训练前确定路径。',
16: '本文在DLPFC、STARmap、osmFISH和人乳腺癌数据上检验这一设计。在统一空间构图条件下，SpaSRD取得了所比较方法中最高的汇总ARI；空间分区与结构消融进一步检验了传播范围、表示分离及重建职责对区域恢复的作用。对新外部数据的验证则将两条路径的内部配置与选路规则预先固定，考察ESGR能否从未参与规则开发的样本中识别更合适的表示路径。由此，本文将组织结构差异对应的建模需求、模型组件的作用及跨样本选路纳入同一验证过程。',
28: 'SpaSRD以表达矩阵和空间坐标为输入，将训练前选路与重建式表示学习连接起来（图1）。ESGR在对称化KNN8图上测量表达对固定扩散的响应及邻域几何，据此确定采用D路径或S路径。D路径调节区域背景的空间整合范围；S路径将共享背景与局部变化分开表示，并为其分配不同的重建职责。两条路径均联合重建表达与空间邻接，所选路径产生64维节点表示，再通过K-means识别空间域。',
29: '核心数据比较采用供体共享的SpaSRD-D配置和用于HBC的SpaSRD-S配置，以评价传播与表示设计的作用。ESGR外部验证采用跨数据固定的路径内部配置：D路径设为K = 10、α = 0.05，S路径采用共同表示图重建及下文定义的两项局部约束。验证阶段分别运行D和S，以量化训练前所选路径的相对收益；应用阶段由ESGR先确定路径，仅训练所选路径并进行聚类。补充空间图对照见表S5。',
71: 'SpaSRD-S在表示分工之外，对差异通道的贡献和局部一致性施加两项约束，以减少域内无关波动。差异幅度惩罚作用于门控后差异表示的元素均方幅度，限制差异成分的幅度；选择性一致性在KNN8范围内筛选表达相近的邻居，对单位化最终表示施加加权距离约束，增强这些邻居之间的一致性。边筛选与权重在训练前由表达数据确定，空间图重建仍仅作用于共同表示。本文将两项约束同时启用称为组合约束，它们属于SpaSRD-S的训练目标，作用由后文的四组消融分别检验。实现与系数见补充方法S6。',
73: '所有核心空间图采用KNN8。深度模型训练500轮，使用五个随机种子和64维聚类表示；DLPFC在每名供体的四张切片间共享传播配置，STARmap与osmFISH共享同一扩散配置。HBC采用上述SpaSRD-S作为主比较配置。表2在相同训练条件下交叉改变表示架构、图重建输入与新增约束，表3分别检验S路径中的两项局部约束。比较方法采用已记录的受控适配设置，各方法的配置及搜索范围见补充方法。冻结选路的外部验证使用相同KNN8、500轮和五seed预算，D与S的内部参数跨数据保持不变。',
74: '每次参数更新后固定模型参数、关闭随机正则化，提取表示并聚类。对于神经网络，主评价取各随机种子在500轮内相对于参考区域标注取得的最高ARI，再对种子汇总，定义如下。下文结果中的ARI均遵循此评价规则；MNMST和经典聚类采用最终拟合结果。',
76: '单张切片或单个数据集报告五个种子的所选ARI均值及样本标准差。DLPFC先计算各切片的五seed均值，再汇总12张切片的中位数、算术均值及切片间样本标准差。MNMST和经典聚类的最终拟合指标按相同数据层级汇总。',
77: '参考区域用于聚类数设定、ARI计算，以及开发阶段的配置选择和训练轮次选择；训练目标为表达与空间结构重建。因此，主结果采用参考标签辅助的选轮评价，各模型保留逐轮记录和所选检查点的预测，固定终点结果见补充材料。ESGR的选路一致性以训练前决定是否对应五seed平均ARI较高的D/S路径判定。外部主比较对三个组织学标注数据集等权平均，脑图谱参考数据单列，并报告四数据集的附加汇总。',
87: '表1 统一KNN8空间图条件下的核心数据ARI比较。DLPFC为12张切片各自五seed平均ARI的中位数±切片间样本标准差；其余数据为五seed均值±样本标准差。指标选取规则见“实验设计与性能评价”。',
88: '神经网络按主评价规则汇总，MNMST与经典方法使用最终拟合结果。SpaGCN采用DEC输出，MNMST采用亲和矩阵上的Leiden，其余深度方法主表使用K-means。RNA后缀表示限定输入的适配版本，MNMST采用官方无图像方案。† HBC采用SpaSRD-S，SiDMGF使用相应配对训练设置；其他比较方法未进行相同规模的优化搜索。DLPFC采用供体共享传播参数；固定内部参数的ESGR外部验证见表4。',
100: '表2 HBC表示架构与图重建输入的消融。各项为五seed均值±样本标准差，检查点按“实验设计与性能评价”的规则选取，边界F1在同一检查点计算。全部采用局部表达解码、KNN8和500轮；组合约束包含差异幅度惩罚与选择性一致性。非分离架构无差异通道，只能施加一致性约束。',
106: '表3 HBC共同表示图重建配置的约束消融。检查点选取及汇总方式同表2。域内混杂率越低表示同一参考区域内部的预测分裂越少；其余指标越高越好。',
135: 'After freezing the routing rule, ESGR selected the path with higher mean ARI on four new datasets, matching fixed diffusion on three histology-annotated datasets and improving on it in an atlas-reference brain dataset.',
208: 'A，参考分区。B，各方法固定seed 0的保存预测，颜色按参考区域匹配。C，各方法重复实验ARI分布；DLPFC为12切片的五seed均值，其余为五seed结果。各方法的评价与聚类口径同表1。SpaSRD-S的图中ARI为0.7071，五seed平均为0.7105±0.0201。组织学图像仅作为可视化底图。',
}

with ZipFile(SOURCE) as z:
    original=z.read('word/document.xml');root=E.fromstring(original)
    body=root.find('w:body',NS);paras=body.findall('w:p',NS)
    def text(p):return ''.join(p.itertext()) if False else ''.join(p.xpath('.//w:t/text()',namespaces=NS))
    def replace(p,value):
        assert not p.xpath('.//m:oMath|.//w:drawing',namespaces=NS),'Do not flatten formulas or figures'
        rpr=p.find('w:r/w:rPr',NS)
        for child in list(p):
            if child.tag!=W+'pPr':p.remove(child)
        r=E.SubElement(p,W+'r')
        if rpr is not None:r.append(deepcopy(rpr))
        t=E.SubElement(r,W+'t');t.set('{http://www.w3.org/XML/1998/namespace}space','preserve');t.text=value
    changes=[]
    for i,value in edits.items():
        before=text(paras[i]);replace(paras[i],value)
        changes.append({'paragraph':i,'before':before,'after':value})
    # The author supplied two consecutive versions of the same preprocessing paragraph.
    assert text(paras[24]).startswith('本文所称区域') and text(paras[23]).startswith('本文所称区域')
    body.remove(paras[24])
    # Define the selection protocol once; use the metric name consistently in narrative.
    for i,p in enumerate(paras):
        if i in edits or i==24 or i>=252:continue
        before=text(p)
        after=before.replace('平均峰值ARI','平均ARI').replace('峰值ARI','ARI').replace('D/S平均峰值收益','D/S平均ARI收益')
        if before!=after:
            replace(p,after);changes.append({'paragraph':i,'before':before,'after':after})
    tables=root.xpath('./w:body/w:tbl',namespaces=NS)
    for table in tables[:4]:
        for t in table.xpath('.//w:t',namespaces=NS):
            if t.text=='峰值ARI':t.text='ARI'
    updated=E.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True)
    TARGET.parent.mkdir(parents=True,exist_ok=True)
    with ZipFile(TARGET,'w') as out:
        for info in z.infolist():out.writestr(info,updated if info.filename=='word/document.xml' else z.read(info.filename))

# Package-level checks: images, formulas, references, numeric table entries unchanged.
with ZipFile(SOURCE) as old,ZipFile(TARGET) as new:
    for name in old.namelist():
        if name!='word/document.xml':assert old.read(name)==new.read(name),name
before=E.fromstring(original)
math=lambda r:[E.tostring(e) for e in r.xpath('.//m:oMath',namespaces=NS)]
assert math(before)==math(root)
nums=lambda r:[re.findall(r'\d+(?:\.\d+)?',t) for t in r.xpath('./w:body/w:tbl//w:t/text()',namespaces=NS)]
assert nums(before)==nums(root)
assert [text(p) for p in paras[147:174]]==[text(p) for p in before.find('w:body',NS).findall('w:p',NS)[147:174]]
assert not any('peak' in edits[i].lower() or '峰值' in edits[i] for i in [2,5,10,11,12,13,14,15,16])
(TARGET.parent/'narrative_revision_20261115.json').write_text(json.dumps({
    'source':str(SOURCE),'target':str(TARGET),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'changes':changes,'duplicate_paragraph_removed':24,
    'preserved':'All media and non-document XML parts byte-identical; equations, references and table numbers unchanged.',
    'terminology':{'SpaSRD-D':'可控扩散路径','SpaSRD-S':'表示分离路径','ESGR':'表达—空间引导选路','ARI':'按方法部分定义的评价规则汇总'},
},ensure_ascii=False,indent=2),encoding='utf8')
print(TARGET)
print(f'{len(changes)} paragraphs revised; 1 duplicate removed; all figures, equations and table values preserved.')
