"""Main-method panels: spatial fidelity and five-seed variation, no invented controls.

Python quantitative grid; vector PDF/SVG plus PNG preview and underlying CSV.
Archived label-assisted peaks and fixed-budget predictions are never pooled.
"""
from pathlib import Path
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import confusion_matrix, adjusted_rand_score
from . import workflow as w
from .plot_style import region_style,spatial_panel


def save(fig, stem):
    stem.parent.mkdir(parents=True,exist_ok=True)
    for suffix in ['pdf','svg','png']:
        fig.savefig(stem.with_suffix('.'+suffix),dpi=300,bbox_inches='tight')
    plt.close(fig)


def align(reference, prediction):
    labels=sorted(np.unique(reference)); pred_labels=sorted(np.unique(prediction))
    table=np.array([[np.sum((reference==a)&(prediction==b)) for b in pred_labels] for a in labels])
    ri,ci=linear_sum_assignment(-table)
    mapping={pred_labels[j]:labels[i] for i,j in zip(ri,ci)}
    return labels,np.array([mapping.get(p,'Unmatched '+str(p)) for p in prediction])


def generate(checkpoint='current',dataset=None,samples=None,profile=None):
    from umap import UMAP
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'svg.fonttype':'none',
        'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
    draw_framework(w.ROOT/'results/figures/framework')
    config=w.configuration();seed=config['plotting']['seed']
    current_rows=None
    if checkpoint=='current':
        from .current_results import collect
        current_rows,source_manifest=collect(dataset,profile,samples)
        selected={(r['sample'],r['profile'],r['seed']):r for r in current_rows.to_dict('records')}
        runs=[r for r in config['runs'] if (r['sample'],r['profile'],r['seed']) in selected]
    else:
        runs=[r for r in config['runs'] if r['profile']==(profile or 'paper')
              and (dataset is None or r['dataset']==dataset) and (not samples or r['sample'] in samples)]
    out=w.ROOT/'results/figures'/checkpoint
    rows=[]
    for run in runs:
        if checkpoint=='current':
            source=selected[(run['sample'],run['profile'],run['seed'])]
            file=w.local(source['prediction'])
        else:
            prediction_dir=w.local(run['prediction'])/('best' if checkpoint=='prediction' and w.completed_best(run) else '')
            file=(prediction_dir/'prediction.npz') if checkpoint=='prediction' else (w.local(run['archive'])/f'{checkpoint}.npz')
        if not file.exists():
            raise FileNotFoundError(f'Run the corresponding dataset notebook first: {file}')
        with np.load(file,allow_pickle=False) as obj:
            z={k:obj[k] for k in obj.files}
        ref=z['reference'].astype(str); pred=z['prediction'].astype(str)
        ari=float(adjusted_rand_score(ref,pred))
        rows.append(dict(dataset=run['dataset'],sample=run['sample'],profile=run['profile'],seed=run['seed'],ARI=ari,
                         epoch=int(z['epoch']),source=file.relative_to(w.ROOT).as_posix(),source_sha256=w.sha(file)))
        if run['seed']!=seed: continue
        print(f'Drawing {run["sample"]}, {run["profile"]}, {checkpoint}, seed {seed}',flush=True)
        labels,aligned=align(ref,pred);all_labels=labels+sorted(set(aligned)-set(labels))
        all_labels,colors=region_style(run['dataset'],all_labels)
        xy=z['spatial'];fig,axes=plt.subplots(1,2,figsize=(7.1,3.8),layout='constrained')
        for ax,v,title in zip(axes,[ref,aligned],['Ground Truth',f'SpaSRD: ARI = {ari:.3f}']):
            style_meta=spatial_panel(ax,run['dataset'],run['sample'],xy,z['obs_names'],v,colors)
            ax.set_title(title)
        handles=[plt.Line2D([],[],marker='o',linestyle='',color=colors[l],markersize=3,label=l) for l in all_labels]
        fig.legend(handles=handles,loc='outside lower center',ncol=min(5,len(all_labels)),fontsize=6)
        checkpoint_label=source['checkpoint'] if checkpoint=='current' else checkpoint
        context=f'{run["sample"]} | {run["profile"]} | {checkpoint_label} | epoch {int(z["epoch"])} | seed {seed}'
        fig.suptitle(context,fontsize=9)
        dest=out/run['dataset']/run['profile']/run['sample'];save(fig,dest/'spatial')
        w.write(dest/'spatial_style.json',dict(style_meta,profile=run['profile'],checkpoint=checkpoint,
            epoch=int(z['epoch']),seed=seed,source=file.relative_to(w.ROOT).as_posix(),source_sha256=w.sha(file)))
        cm=confusion_matrix(ref,aligned,labels=all_labels).astype(float)
        cm=np.divide(cm,cm.sum(1,keepdims=True),out=np.zeros_like(cm),where=cm.sum(1,keepdims=True)!=0)
        fig,ax=plt.subplots(figsize=(4.2,3.7),layout='constrained')
        im=ax.imshow(cm,vmin=0,vmax=1,cmap='Blues');fig.colorbar(im,ax=ax,label='Fraction within reference region')
        ax.set_xticks(range(len(all_labels)),all_labels,rotation=90,fontsize=6)
        ax.set_yticks(range(len(all_labels)),all_labels,fontsize=6)
        ax.set_xlabel('SpaSRD region (label-matched for display)');ax.set_ylabel('Reference region')
        ax.set_title(f'{run["profile"]} | epoch {int(z["epoch"])} | seed {seed} | ARI {ari:.3f}',fontsize=8)
        save(fig,dest/'confusion')
        pd.DataFrame(cm,index=all_labels,columns=all_labels).to_csv(dest/'confusion.csv')
        low=UMAP(n_components=2,n_neighbors=config['plotting']['umap_neighbors'],
            min_dist=config['plotting']['umap_min_dist'],random_state=0,n_jobs=1).fit_transform(z['embedding'])
        fig,axes=plt.subplots(1,2,figsize=(7.1,3.2),layout='constrained')
        for ax,v,title in zip(axes,[ref,aligned],['Ground Truth labels','SpaSRD predicted labels']):
            ax.scatter(low[:,0],low[:,1],c=[colors[t] for t in v],s=2,linewidths=0,edgecolors='none',rasterized=True)
            ax.set_title(title);ax.set_xticks([]);ax.set_yticks([]);ax.set_xlabel('UMAP 1');ax.set_ylabel('UMAP 2')
        fig.suptitle(context+'\nSame model UMAP coordinates; two labelings',fontsize=8)
        fig.legend(handles=handles,loc='outside lower center',ncol=min(5,len(all_labels)),fontsize=6)
        save(fig,dest/'umap')
        pd.DataFrame(dict(obs_name=z['obs_names'],x=xy[:,0],y=xy[:,1],umap1=low[:,0],umap2=low[:,1],
            reference=ref,prediction=pred,display_label=aligned)).to_csv(dest/'plot_source.csv',index=False)
        if checkpoint=='current' and run['sample'] in config['plotting'].get('marker_samples',[]):
            from .marker_figures import generate_markers
            generate_markers(run,z,source,dest,save)
    if not rows: raise ValueError('No selected figure inputs')
    df=pd.DataFrame(rows);out.mkdir(parents=True,exist_ok=True);df.to_csv(out/'seed_metrics.csv',index=False)
    for (ds,pr),g in df.groupby(['dataset','profile'],sort=False):
        order=list(g['sample'].unique());fig,ax=plt.subplots(figsize=(max(3.2,len(order)*.5),3),layout='constrained')
        values=[g.loc[g['sample']==sample,'ARI'].to_numpy() for sample in order]
        ax.boxplot(values,tick_labels=order,showfliers=False,widths=.5)
        for i,v in enumerate(values,1):
            ax.scatter(i+np.linspace(-.09,.09,len(v)),v,s=14,color='#4678A4',zorder=3)
        ax.tick_params(axis='x',rotation=45);ax.set_ylabel('ARI');ax.set_ylim(0,1)
        ax.set_title(f'{ds} / {pr}: {checkpoint}; each dot is one seed')
        save(fig,out/ds/pr/'seed_boxplot')
        fig,ax=plt.subplots(figsize=(max(3.2,len(order)*.5),3),layout='constrained')
        distribution(ax,values,order,violin=True)
        ax.set_ylabel('ARI');ax.set_ylim(0,1);ax.tick_params(axis='x',rotation=45)
        ax.set_title(f'{ds} / {pr}: {checkpoint}; five seeds per sample')
        save(fig,out/ds/pr/'seed_violin')
    w.write(out/'figure_provenance.json',dict(checkpoint=checkpoint,seed_for_panels=seed,
        evidence='Spatial agreement and per-seed variation of the main method; not a baseline comparison.',
        peak_is_label_assisted=checkpoint=='peak' or (checkpoint=='current' and 'best' in set(current_rows.checkpoint)),
        sources=rows,archive_fallback=False,
        umap='descriptive projection, not an independent accuracy test',
        umap_labels='Ground Truth and prediction color the same model-derived coordinates; no embedding is constructed from labels',
        distributions='Five technical seeds per sample; box median/IQR/1.5 IQR whiskers with all points; violin KDE is descriptive; no significance test',
        expression='Representative samples only; observed and frozen decoder expectations; see per-sample marker_provenance.json',
        alignment='Hungarian label matching is used only for display; ARI uses original labels.'))
    if checkpoint=='current':w.write(out/'source_manifest.json',source_manifest)
    print('Figures:',out,flush=True)


def distribution(ax,values,labels,violin=False,colors=None):
    """Missing groups stay empty; constant/singleton groups have no invented density."""
    for pos,v in enumerate(values,1):
        v=np.asarray(v,dtype=float);v=v[np.isfinite(v)]
        color=colors[pos-1] if colors is not None else '#4678A4'
        if not len(v):
            ax.text(pos,.04,'NA',transform=ax.get_xaxis_transform(),ha='center',fontsize=6);continue
        if violin and len(v)>1 and np.ptp(v)>1e-12:
            parts=ax.violinplot([v],positions=[pos],widths=.75,showextrema=False)
            for body in parts['bodies']:body.set_facecolor(color);body.set_alpha(.3)
        ax.boxplot([v],positions=[pos],widths=.18 if violin else .5,showfliers=False,
                   medianprops={'color':'#333333'},manage_ticks=False)
        ax.scatter(pos+np.linspace(-.09,.09,len(v)),v,s=12,color=color,zorder=3)
    ax.set_xticks(range(1,len(labels)+1),labels);ax.set_xlim(.4,len(labels)+.6)


def draw_framework(output=None,combined=False):
    """The author-maintained framework is the only canonical diagram."""
    p=w.ROOT/'results/figures/publication/SpaSRD_framework_preview.png'
    if not p.exists():raise FileNotFoundError('Export the author framework PPTX preview: '+str(p))
    return p
