"""Publication figures from explicitly selected saved predictions; no training.

Evidence contract: spatial agreement, representation geometry and repeated-run
variation, not a claim of universal superiority. All panels use seed 0 and
label-assisted peak checkpoints; DLPFC distributions aggregate within section.
Python image plates and quantitative grids; PNG/PDF/SVG plus source indices.
"""
from pathlib import Path
import os,json,hashlib,math
from importlib.metadata import version
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import adjusted_rand_score,confusion_matrix
from .figures import align,distribution,draw_framework
from .plot_style import spatial_panel,region_style
from .publication_style import STYLE, STYLE_FILE, configure, export, distributions as plot_distribution
ROOT=Path(__file__).resolve().parents[1]
_cache=ROOT/'results/figures/cache/numba'
_cache.mkdir(parents=True,exist_ok=True)
os.environ['NUMBA_CACHE_DIR']=str(_cache)
CONFIG=ROOT/'config/publication_figures.json'
OUT=ROOT/'results/figures/publication'
SUPPLEMENT=ROOT/'results/figures/supplementary_controls'
OLD=ROOT/'results/figures/source_data'
METHODS=['SpaSRD','STAGATE','MNMST','MAEST','GraphST','SpaGCN','SEDR','Spatial-MGCN','SiDMGF-full','DisConST-RNA','MuCST-RNA','stLearn-RNA','PCA-KMeans','SCANPY-Leiden']
CONTROL=['SpaSRD','SiDMGF-spatial','SiDMGF-full']
NAMES={'SpaSRD':'SpaSRD-D/S','SiDMGF-spatial':'SiDMGF (spatial-only control)','SiDMGF-full':'SiDMGF'}
CACHE={};RECORDS=[]
UMAP_SETTINGS=dict(n_neighbors=15,min_dist=.3,metric='euclidean',random_state=0,n_jobs=1)
SAMPLES_FOR_PLATES=['151507','human_breast_cancer','starmap','osmfish']
FIGURE_STEMS=['Fig2a_distributions','Fig2b_violins','Fig6_mechanism','Fig7_HBC_ablation','Fig8_ESGR_validation'] + [f'{s}_{suffix}' for s in SAMPLES_FOR_PLATES for suffix in ['all_methods_spatial','all_methods_umap_1','all_methods_umap_2','all_methods_umap_3']]
METHOD_COLORS=STYLE['method_colors']
configure()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ds(s):return 'DLPFC' if s.isdigit() else {'human_breast_cancer':'HBC','starmap':'STARmap','osmfish':'osmFISH'}[s]
def name(m,s):return ('SpaSRD-S' if ds(s)=='HBC' else 'SpaSRD-D') if m=='SpaSRD' else NAMES.get(m,m)
def read_object(r):
    p=(ROOT/r['source']).resolve()
    if sha(p)!=r['sha256']:raise ValueError('Prediction changed; re-audit before plotting: '+str(p))
    with np.load(p,allow_pickle=True) as z:o={k:z[k] for k in ['embedding','prediction','reference','obs_names','spatial','epoch']}
    for k in ['reference','prediction','obs_names']:o[k]=o[k].astype(str)
    assert len(set(o['obs_names']))==len(o['obs_names'])
    assert len(o['embedding'])==len(o['obs_names']) and np.isfinite(o['embedding']).all()
    o['ARI']=adjusted_rand_score(o['reference'],o['prediction'])
    if abs(o['ARI']-r['ARI'])>1e-10:raise ValueError('ARI mismatch: '+str(p))
    o['mapped']=align(o['reference'],o['prediction'])[1]
    labels,colors=region_style(r['dataset'],list(o['reference'])+list(o['mapped']))
    colors={lab:STYLE['region_replacements'].get(color,color) for lab,color in colors.items()}
    o.update(labels=labels,colors=colors,source_sha256=r['sha256'])
    return o
def verify():
    global RECORDS
    config=json.loads(CONFIG.read_text(encoding='utf-8'))
    for key,expected in [('hbc','combined'),('checkpoint','best'),('seed',0),('output','results/figures/publication')]:
        if config.get(key)!=expected:
            raise ValueError(f'Publication contract requires {key}={expected!r}; found {config.get(key)!r}')
    RECORDS=config['runs'];CACHE.clear()
    # A correctly hashed old HBC file must not silently become the combined model.
    for r in RECORDS:
        if r['dataset']=='HBC' and r['method']=='SpaSRD':
            expected=f'results/hbc_combined/refined/combined/seed_{r["seed"]}/best.npz'
            if r['source']!=expected:raise ValueError('HBC main figure must use combined/common-graph peak: '+r['source'])
            report=json.loads((ROOT/r['source']).with_name('report.json').read_text(encoding='utf-8'))
            if (report['profile'],report['arm'],report['seed'])!=('refined','combined',r['seed']):
                raise ValueError('HBC combined report/config mismatch')
            if report['files']['best.npz']!=r['sha256']:raise ValueError('HBC report/prediction hash mismatch')
    assert len(RECORDS)==1125
    keys=[(r['method'],r['sample'],r['seed']) for r in RECORDS]
    assert len(set(keys))==1125
    truth={};metrics=[]
    for i,r in enumerate(RECORDS):
        o=read_object(r);s=r['sample']
        canonical=(o['obs_names'],o['reference'],o['spatial'])
        if s in truth:assert all(np.array_equal(a,b) for a,b in zip(truth[s],canonical)),('Observation mismatch',s,r['method'])
        else:truth[s]=canonical
        if r['seed']==0:CACHE[s,r['method']]=o
        metrics.append(dict(r,epoch=int(o['epoch'])))
        if (i+1)%75==0:print('Verified',i+1,'/',len(RECORDS),flush=True)
    frame=pd.DataFrame(metrics)
    for (m,s),g in frame.groupby(['method','sample']):assert sorted(g.seed)==[0,1,2,3,42],(m,s)
    OUT.mkdir(parents=True,exist_ok=True)
    SUPPLEMENT.mkdir(parents=True,exist_ok=True)
    # Keep control experiments traceable, but never merge them into the main roster.
    controls=frame[frame.method.isin(CONTROL)]
    controls.to_csv(SUPPLEMENT/'sidmgf_control_seed_metrics.csv',index=False)
    summary=[]
    for (m,d),g in frame.groupby(['method','dataset'],sort=False):
        v=g.groupby('sample').ARI.mean() if d=='DLPFC' else g.ARI
        summary.append(dict(method=m,dataset=d,value=v.median() if d=='DLPFC' else v.mean(),std=v.std(ddof=1),n=len(v)))
    summary=pd.DataFrame(summary)
    summary[summary.method.isin(CONTROL)].to_csv(SUPPLEMENT/'sidmgf_control_summary.csv',index=False)
    main=frame[frame.method.isin(METHODS)].copy()
    assert len(main)==1050 and main.method.nunique()==14
    main.to_csv(OUT/'seed_metrics.csv',index=False)
    main_summary=summary[summary.method.isin(METHODS)].copy()
    main_summary['method']=main_summary.method.map(lambda m:NAMES.get(m,m))
    main_summary.to_csv(OUT/'method_summary.csv',index=False)
    return main
def selected_source_table(frame):
    """Actual panel seed and five-seed summary, with directly usable source paths."""
    summary=frame.groupby(['dataset','sample','method'],sort=False).ARI.agg(['mean','std']).reset_index()
    selected=frame[frame.seed.eq(0)].merge(summary,on=['dataset','sample','method'],validate='one_to_one')
    selected['source_absolute']=selected.source.map(lambda p:str((ROOT/p).resolve()))
    selected['method']=selected.method.map(lambda m:NAMES.get(m,m))
    return selected[['dataset','sample','method','protocol','seed','epoch','ARI','mean','std','source_absolute']]
def saved(s,m,cohort='common'):
    return CACHE[s,m]
def umap_xy(s,m,o,cohort='common'):
    p=OUT/'projections'/f'{s}_{m}.npz';p.parent.mkdir(exist_ok=True)
    cache_signature=json.dumps(dict(source=o['source_sha256'],settings=UMAP_SETTINGS,
        implementation=version('umap-learn')),sort_keys=True)
    if p.exists():
        with np.load(p,allow_pickle=False) as z:
            if ('cache_signature' in z and str(z['cache_signature'])==cache_signature
                and np.array_equal(z['obs_names'].astype(str),o['obs_names'])
                and z['xy'].shape==(len(o['obs_names']),2) and np.isfinite(z['xy']).all()):return z['xy']
    from umap import UMAP
    low=UMAP(**UMAP_SETTINGS).fit_transform(o['embedding'])
    np.savez_compressed(p,xy=low,source_sha256=o['source_sha256'],obs_names=o['obs_names'],cache_signature=cache_signature)
    return low
def save(fig,n):
    export(fig,OUT,n);print('Saved vector SVG/PDF + PNG preview:',n,flush=True)
def legend(fig,s,labels,colors):
 hs=[plt.Line2D([],[],ls='',marker='o',ms=3,color=colors[x],label=x) for x in labels]
 fig.legend(handles=hs,loc='outside lower center',ncol=5 if len(labels)>12 else min(7,len(labels)),fontsize=6.5)
def spatial(samples,n,cohort='common',square=False):
 if len(set(ds(s) for s in samples))>1:
  fig=plt.figure(figsize=(7.2,6.2),layout='constrained')
  subfigs=fig.subfigures(len(samples),1)
  for sf,s in zip(subfigs,samples):
   axes=sf.subplots(1,4);base=saved(s,'SpaSRD',cohort)
   for i,(ax,o,label) in enumerate(zip(axes,[base]+[saved(s,m,cohort) for m in CONTROL],['Ground Truth']+CONTROL)):
    spatial_panel(ax,ds(s),s,o['spatial'],o['obs_names'],o['reference'] if i==0 else o['mapped'],o['colors'])
    ax.set_title('Ground Truth' if i==0 else name(label,s)+f'\nARI = {o["ARI"]:.3f}',fontsize=8)
   hs=[plt.Line2D([],[],ls='',marker='o',ms=3,color=base['colors'][x],label=x) for x in base['labels']]
   sf.legend(handles=hs,loc='outside lower center',ncol=3 if ds(s)=='osmFISH' else 7,fontsize=6)
   sf.suptitle(ds(s)+' | seed 0',fontsize=9)
  save(fig,n);return
 shape=(2,2) if square else (len(samples),4)
 fig,axes=plt.subplots(*shape,figsize=(7.2,6.6 if square else 2.25*len(samples)+.55),layout='constrained',squeeze=False)
 for row,s in enumerate(samples):
  base=saved(s,'SpaSRD',cohort);objs=[base]+[saved(s,m,cohort) for m in CONTROL]
  for col,(o,label) in enumerate(zip(objs,['Ground Truth']+CONTROL)):
   ax=axes.flat[col] if square else axes[row,col]
   values=o['reference'] if col==0 else o['mapped']
   spatial_panel(ax,ds(s),s,o['spatial'],o['obs_names'],values,o['colors'])
   title='Ground Truth' if col==0 else name(label,s)+f'\nARI = {o["ARI"]:.3f}'
   ax.set_title((s+'\n' if col==0 and not square else '')+title,fontsize=8)
 if len(set(ds(s) for s in samples))==1:legend(fig,s,base['labels'],base['colors'])
 fig.suptitle(('HBC | '+('combined / matched controls') if square else 'Spatial domains')+' | seed 0',fontsize=9)
 save(fig,n)
def diagnostic(samples,n,methods=None,cohort='common'):
 tasks=[(s,m) for s in samples for m in (methods or ['SpaSRD'])]
 fig,axes=plt.subplots(len(tasks),3,figsize=(7.2,2.4*len(tasks)+.4),layout='constrained',squeeze=False)
 for i,(s,m) in enumerate(tasks):
  o=saved(s,m,cohort);xy=umap_xy(s,m,o,cohort)
  for ax,v,t in zip(axes[i,:2],[o['reference'],o['mapped']],['Ground Truth labels','Predicted labels']):
   ax.scatter(*xy.T,c=[o['colors'][x] for x in v],s=1.8,edgecolors='none',linewidths=0,rasterized=True)
   ax.set_title(f'{s if ds(s)!="HBC" else name(m,s)}\n{t}',fontsize=8);ax.set_xticks([]);ax.set_yticks([])
   ax.set_xlabel('UMAP 1');ax.set_ylabel('UMAP 2')
  cm=confusion_matrix(o['reference'],o['mapped'],labels=o['labels']).astype(float)
  cm=np.divide(cm,cm.sum(1,keepdims=True),out=np.zeros_like(cm),where=cm.sum(1,keepdims=True)!=0)
  ax=axes[i,2];im=ax.imshow(cm,vmin=0,vmax=1,cmap='Blues',aspect='equal')
  short={x:x.replace('Tumor_edge_','TE').replace('DCIS/LCIS_','D/L').replace('Healthy_','H').replace('IDC_','I') for x in o['labels']}
  labels=[short[x] for x in o['labels']]
  if ds(s)=='osmFISH':labels=[str(i+1) for i in range(len(labels))]
  ax.set_xticks(range(len(labels)),labels,rotation=90,fontsize=5.8);ax.set_yticks(range(len(labels)),labels,fontsize=5.8)
  ax.set_xlabel('Predicted region');ax.set_ylabel('Reference region');ax.set_title(name(m,s)+' | correspondence',fontsize=8)
  fig.colorbar(im,ax=ax,shrink=.6,ticks=[0,.5,1],label='Row fraction')
 fig.suptitle('Saved embeddings and region correspondence | seed 0',fontsize=9)
 save(fig,n)
def mechanism():
 p=pd.read_csv(OLD/'figure6_actual_graph_profiles.csv');c=pd.read_csv(OLD/'figure6_region_composition.csv');w=pd.read_csv(OLD/'figure6_filter_weights.csv');a=pd.read_csv(OLD/'figure6_alpha_search.csv')
 groups=['Br5292','Br5595','Br8100'];colors=['#4C78A8','#8172A2','#B57649']
 fig,ax=plt.subplots(2,2,figsize=(STYLE['width_mm']/25.4,5.4),layout='constrained')
 for i,(g,col) in enumerate(zip(groups,colors)):
  v=p.loc[p.donor==g,'cross_edge'].to_numpy()*100;ax[0,0].scatter(i+np.linspace(-.1,.1,4),v,c=col,s=18);ax[0,0].plot([i-.2,i+.2],[v.mean()]*2,c='#333333')
 ax[0,0].set_xticks(range(3),groups);ax[0,0].set_ylabel('Cross-region edges (%)');ax[0,0].set_title('A  KNN8 boundary mixing',loc='left',fontweight='bold')
 labs,cmap=region_style('DLPFC',c.region);bottom=np.zeros(3)
 cmap={k:STYLE['region_replacements'].get(v,v) for k,v in cmap.items()}
 for lab in labs:
  v=[c[(c.donor==g)&(c.region==lab)].fraction.iloc[0] for g in groups]
  ax[0,1].bar(groups,v,bottom=bottom,color=cmap[lab],label=lab);bottom+=v
 ax[0,1].set_title('B  Sampled region composition',loc='left',fontweight='bold');ax[0,1].set_ylabel('Fraction of annotated spots');ax[0,1].legend(ncol=3,fontsize=6,loc='upper center',bbox_to_anchor=(.5,-.13))
 for g,col in zip(groups,colors):
  r=w[w.donor==g];q=r.iloc[0];ax[1,0].plot(r.hop,r.weight,'o-',ms=2.5,lw=.8,color=col,label=f'{g}: K={int(q.K)}, α={q.alpha:g}\nExpected order={q.effective_steps:.2f}')
 ax[1,0].set_title('C  Finite propagation weights',loc='left',fontweight='bold');ax[1,0].set_xlabel('Propagation order');ax[1,0].set_ylabel('Weight');ax[1,0].legend(fontsize=6)
 a=a.sort_values('alpha');ax[1,1].plot(a.alpha,a['median'],'o-',c=colors[0],ms=3);ax[1,1].set_xticks(a.alpha,[f'{x:g}' for x in a.alpha],rotation=40)
 ax[1,1].ticklabel_format(axis='y',style='plain',useOffset=False)
 ax[1,1].set_title('D  Restart sensitivity',loc='left',fontweight='bold');ax[1,1].set_xlabel('Br8100 α (K=4)');ax[1,1].set_ylabel('12-section median peak ARI')
 save(fig,'Fig6_mechanism')

def distributions(frame):
    colors=[METHOD_COLORS[m] for m in METHODS]
    for kind in ['box','violin']:
        fig,axes=plt.subplots(2,2,figsize=(STYLE['width_mm']/25.4,7.1),layout='constrained')
        for letter,ax,dataset in zip('ABCD',axes.flat,['DLPFC','HBC','STARmap','osmFISH']):
            g=frame[frame.dataset==dataset];values=[]
            for method in METHODS:
                f=g[g.method==method]
                values.append(f.groupby('sample').ARI.mean().to_numpy() if dataset=='DLPFC' else f.ARI.to_numpy())
            plot_distribution(ax,values,[NAMES.get(m,m) for m in METHODS],colors,kind=='violin',horizontal=True)
            ax.set_xlabel('Section mean ARI' if dataset=='DLPFC' else 'ARI')
            ax.set_xlim(0,1);ax.set_title(letter+'  '+dataset,loc='left',fontweight='bold')
            ax.tick_params(axis='y',labelsize=6.5)
        save(fig,'Fig2a_distributions' if kind=='box' else 'Fig2b_violins')
def all_methods(s):
    objs=[saved(s,m) for m in METHODS];base=objs[0]
    ncols=3;nrows=math.ceil((len(METHODS)+1)/ncols)
    fig=plt.figure(figsize=(STYLE['width_mm']/25.4,10.8),layout='constrained')
    grid=fig.add_gridspec(nrows+1,ncols,height_ratios=[1]*nrows+[.90])
    axes=np.array([fig.add_subplot(grid[i//ncols,i%ncols]) for i in range(len(METHODS)+1)])
    for i,(o,label) in enumerate(zip([base]+objs,['Ground Truth']+METHODS)):
        spatial_panel(axes.flat[i],ds(s),s,o['spatial'],o['obs_names'],o['reference'] if i==0 else o['mapped'],o['colors'],rasterized=False)
        axes.flat[i].set_title('A  Ground Truth' if i==0 else ('B  ' if i==1 else '')+name(label,s)+f'\nARI = {o["ARI"]:.3f}',fontsize=7)
    legend(fig,s,base['labels'],base['colors'])
    ax=fig.add_subplot(grid[nrows,:])
    f=pd.read_csv(OUT/'seed_metrics.csv');f=f[f.dataset==ds(s)]
    values=[(f[f.method==m].groupby('sample').ARI.mean().to_numpy() if ds(s)=='DLPFC' else f[f.method==m].ARI.to_numpy()) for m in METHODS]
    plot_distribution(ax,values,[NAMES.get(m,m) for m in METHODS],[METHOD_COLORS[m] for m in METHODS])
    ax.tick_params(axis='x',labelrotation=65,labelsize=6)
    ax.set_ylabel('ARI');ax.set_title('C  Repeated-run comparison',loc='left',fontweight='bold')
    fig.suptitle(ds(s) if ds(s)!='DLPFC' else 'DLPFC '+s)
    save(fig,f'{s}_all_methods_spatial')
    for page in range(math.ceil(len(METHODS)/5)):
        subset=list(zip(METHODS,objs))[page*5:(page+1)*5]
        fig=plt.figure(figsize=(STYLE['width_mm']/25.4,1.7*len(subset)+.5),layout='constrained')
        subfigs=np.atleast_1d(fig.subfigures(len(subset),1))
        for letter,sf,(m,o) in zip('ABCDE',subfigs.flat,subset):
            xy=umap_xy(s,m,o);axes=sf.subplots(1,2)
            for ax,values,title in zip(axes,[o['reference'],o['mapped']],['Ground Truth','Prediction']):
                ax.scatter(*xy.T,c=[o['colors'][v] for v in values],s=1.8,linewidths=0,rasterized=False)
                ax.set_title(title,fontsize=6.5);ax.set_xticks([]);ax.set_yticks([])
                ax.set_aspect('equal',adjustable='datalim')
                for spine in ax.spines.values():spine.set_visible(False)
            sf.suptitle(letter+'  '+name(m,s)+f'  (ARI = {o["ARI"]:.3f})',fontsize=7.5,x=.02,ha='left',fontweight='bold')
        legend(fig,s,base['labels'],base['colors'])
        fig.suptitle(ds(s)+' — latent representations')
        save(fig,f'{s}_all_methods_umap_{page+1}')
def signature():
    paths=[STYLE_FILE,ROOT/'src/publication_style.py',ROOT/'supplementary_experiments/mechanism_evidence.py',OUT/'SpaSRD_framework_editable.svg',OUT/'SpaSRD_framework_editable.pptx',OUT/'SpaSRD_framework_preview.png',OLD/'hbc_structure.csv',OLD/'hbc_regularization.csv',OLD/'v5_validation.csv',CONFIG,Path(__file__),ROOT/'src/figures.py',ROOT/'src/plot_style.py',ROOT/'config/paper.json']
    paths += [OLD/n for n in ['figure6_actual_graph_profiles.csv','figure6_region_composition.csv',
                             'figure6_filter_weights.csv','figure6_alpha_search.csv']]
    for sample in ['151507','151669','151673','human_breast_cancer']:
        folder=ROOT/'data'/ds(sample)/sample/'histology'
        registration=folder/'registration.json'
        paths.append(registration)
        paths.extend(folder/n for n in json.loads(registration.read_text(encoding='utf-8'))['files'])
    return {str(p.relative_to(ROOT)):sha(p) for p in paths}
def expected_files():
    return [OUT/f'{stem}.{ext}' for stem in FIGURE_STEMS for ext in ['png','pdf','svg']] + [OUT/'SpaSRD_framework_editable.svg',OUT/'SpaSRD_framework_editable.pptx',OUT/'SpaSRD_framework_preview.png']
def reusable_manifest(old,sig):
    expected={p.relative_to(ROOT).as_posix() for p in expected_files()}
    actual=[r['path'] for r in old.get('files',[])]
    return (old.get('signature')==sig and len(actual)==len(expected) and set(actual)==expected
            and all((ROOT/r['path']).is_file() and sha(ROOT/r['path'])==r['sha256'] for r in old['files']))
def generate(force=False):
    """Verify every source; reuse only a complete, matching rendered figure set."""
    frame=verify();stamp=OUT/'figure_manifest.json';sig=signature()
    if stamp.exists() and not force:
        old=json.loads(stamp.read_text(encoding='utf-8'))
        if reusable_manifest(old,sig):
            print('Reusing verified publication figures; no retraining or replotting.',flush=True)
            return frame,[ROOT/r['path'] for r in old['files'] if r['path'].endswith('.png')]
    distributions(frame)
    mechanism()
    from supplementary_experiments.mechanism_evidence import generate as evidence
    evidence(OUT)
    for s in SAMPLES_FOR_PLATES:all_methods(s)
    # Only this run's defined figures enter the manuscript list; ignore loose old images.
    files=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in expected_files()]
    stamp.write_text(json.dumps(dict(signature=sig,files=files,sources=[r for r in RECORDS if r['method'] in METHODS],
        methods=[NAMES.get(m,m) for m in METHODS],sidmgf_main='SiDMGF-full',
        supplementary_controls=str(SUPPLEMENT.relative_to(ROOT)),
        hbc='combined, common graph reconstruction',external='v2, 12 methods',seed=0),ensure_ascii=False,indent=2),encoding='utf-8')
    return frame,[ROOT/r['path'] for r in files if r['path'].endswith('.png')]
