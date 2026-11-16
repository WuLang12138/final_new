"""Render archived ablations and frozen routing evidence. No training or fitting."""
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from src.publication_style import STYLE,export

ROOT=Path(__file__).resolve().parents[1]
def generate(output):
    output=Path(output);data=ROOT/'results/figures/source_data'
    a=pd.read_csv(data/'hbc_structure.csv');b=pd.read_csv(data/'hbc_regularization.csv')
    fig=plt.figure(figsize=(STYLE['width_mm']/25.4,5.6),layout='constrained')
    grid=fig.add_gridspec(2,2,height_ratios=[1.3,1])
    axes=[fig.add_subplot(grid[0,0]),fig.add_subplot(grid[0,1]),fig.add_subplot(grid[1,:])]
    labels=['Unsplit','Unsplit + consistency','Split / fused','Split / fused + combined','Split / common','Split / common + combined']
    for ax,col,title in zip(axes[:2],['峰值ARI','边界F1'],['A  Partition agreement','B  Boundary recovery']):
        values=np.array([[float(x) for x in s.split('±')] for s in a[col]])
        ax.errorbar(values[:,0],np.arange(6),xerr=values[:,1],fmt='o',color='#527F9C',capsize=3)
        ax.set_yticks(range(6),labels,fontsize=6.5);ax.invert_yaxis();ax.set_title(title,loc='left',fontsize=8,fontweight='bold')
        ax.set_xlabel('Peak ARI' if col=='峰值ARI' else 'Boundary F1')
    vals=np.array([[float(x) for x in s.split('±')] for s in b['域内混杂率']])
    axes[2].errorbar(range(4),vals[:,0],yerr=vals[:,1],fmt='o',capsize=3,color='#B7774C')
    axes[2].set_xticks(range(4),['Base','Amplitude','Consistency','Combined'],rotation=40,ha='right')
    axes[2].set_ylabel('Within-region mixing');axes[2].set_title('C  Selective regularization',loc='left',fontsize=8,fontweight='bold')
    export(fig,output,'Fig7_HBC_ablation')
    v=pd.read_csv(data/'v5_validation.csv').set_index('family').loc[['Human_Colon','Human_Small_Intestine','Human_Heart_LV','Adult_Mouse_Brain_02A']]
    fig,axes=plt.subplots(1,2,figsize=(STYLE['width_mm']/25.4,3.3),layout='constrained');x=np.arange(4)
    for offset,col,label,color in [(-.23,'D_peak','Fixed D','#0072B2'),(0,'S_peak','Fixed S','#D55E00'),(.23,'selected_peak','ESGR selected','#009E73')]:
        axes[0].bar(x+offset,v[col],width=.22,label=label,color=color)
    names=['Colon','Small intestine','Heart LV','Brain atlas*']
    axes[0].set_xticks(x,names,rotation=25,ha='right');axes[0].set_ylabel('Five-seed mean peak ARI');axes[0].legend(fontsize=7)
    axes[0].set_title('A  Frozen ESGR decisions',loc='left',fontweight='bold')
    axes[1].axhline(0,color='#aaa',lw=.7)
    axes[1].scatter(x,v.S_peak-v.D_peak,color=['#527F9C']*3+['#B7774C'],s=35)
    for i,(_,r) in enumerate(v.iterrows()):axes[1].annotate('Selected '+r.chosen,(i,r.S_peak-r.D_peak),xytext=(0,10),textcoords='offset points',ha='center',fontsize=7)
    axes[1].set_xticks(x,names,rotation=25,ha='right');axes[1].set_ylabel('S − D mean peak ARI');axes[1].set_title('B  Observed benefit direction',loc='left')
    axes[1].margins(x=.15,y=.25)
    export(fig,output,'Fig8_ESGR_validation')
