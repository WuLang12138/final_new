"""Descriptive expression panels from observed counts and the frozen omics decoder."""
import numpy as np
import pandas as pd
import scipy.sparse as sp
import matplotlib.pyplot as plt
import torch
from . import workflow as w
from .plot_style import region_style


def generate_markers(run,z,source,dest,save):
    requested=w.configuration()['plotting']['marker_genes'].get(run['dataset'],[])
    a,A,P=w.inputs(run)
    lookup={g.upper():g for g in a.var_names}
    genes=[lookup[g.upper()] for g in requested if g.upper() in lookup]
    missing=[g for g in requested if g.upper() not in lookup]
    meta=dict(requested=requested,available=genes,missing=missing,seed=run['seed'],
              weight=source['weight'],weight_sha256=source['weight_sha256'],
              normalization='log1p(10000 * value / sum across retained genes per cell), separately for observed and reconstructed',
              reconstruction='ZINB expectation (1-pi)*mean, frozen model in inference mode; not an independent denoising test',
              grouping='Ground Truth region; these are spatial observations, not independent biological replicates')
    if not genes or 'counts' not in a.layers:
        meta['status']='missing genes or counts';w.write(dest/'marker_provenance.json',meta);return
    indices=a.var_names.get_indexer(genes)
    counts=a.layers['counts'];counts=counts.toarray() if sp.issparse(counts) else np.asarray(counts)
    if not np.isfinite(counts).all() or counts.min()<0:raise ValueError('Invalid observed counts')
    state=torch.load(w.local(source['weight']),map_location='cpu',weights_only=True)
    w.validate_weight(run,state,source['checkpoint'])
    model=w.build(run['parameters'],a.n_vars);model.load_state_dict(state['model'],strict=True);model.eval()
    # Use the verified saved embedding; avoid computing the dense graph decoder.
    with torch.no_grad():
        pi,disp,mean=model.omics_decoder(torch.as_tensor(z['embedding']),w.sparse_tensor(P,'cpu'))
        reconstructed=((1-pi)*mean).cpu().numpy()
    def norm(x):
        return np.log1p(np.divide(x[:,indices]*10000,x.sum(1,keepdims=True),
            out=np.zeros((len(x),len(indices)),dtype=float),where=x.sum(1,keepdims=True)>0))
    obs=norm(counts);rec=norm(reconstructed);ref=z['reference'].astype(str);xy=z['spatial']
    labels,colors=region_style(run['dataset'],np.unique(ref))
    rows=[]
    for kind,mat in [('Observed',obs),('Reconstructed',rec)]:
        for j,gene in enumerate(genes):
            rows.append(pd.DataFrame(dict(obs_name=z['obs_names'],reference=ref,gene=gene,
                expression=mat[:,j],source=kind)))
    pd.concat(rows,ignore_index=True).to_csv(dest/'marker_expression.csv',index=False)
    for name,mat in [('observed',obs),('reconstructed',rec)]:
        cols=min(3,len(genes));nr=int(np.ceil(len(genes)/cols))
        fig,axes=plt.subplots(nr,cols,figsize=(7.2,2.8*nr),squeeze=False,layout='constrained')
        for ax in axes.flat:ax.set_visible(False)
        for j,(gene,ax) in enumerate(zip(genes,axes.flat)):
            ax.set_visible(True)
            for i,lab in enumerate(labels,1):
                values=mat[ref==lab,j]
                if len(values)>1 and np.ptp(values)>1e-12:
                    parts=ax.violinplot([values],positions=[i],showextrema=False,widths=.85)
                    for body in parts['bodies']:body.set_facecolor(colors[lab]);body.set_alpha(.65)
                ax.plot([i-.18,i+.18],[np.median(values)]*2,color='#333333',lw=1)
            ax.set_xticks(range(1,len(labels)+1),labels,rotation=90,fontsize=5)
            ax.set_title(gene);ax.set_ylabel('log1p normalized expression',fontsize=6)
            # Keep observed and reconstructed axes identical for each gene.
            ax.set_ylim(0,max(obs[:,j].max(),rec[:,j].max())*1.05+1e-6)
        fig.suptitle(f'{run["sample"]}: {name}; Ground Truth regions',fontsize=9)
        save(fig,dest/f'marker_violin_{name}')
    fig,axes=plt.subplots(2,len(genes),figsize=(max(4,len(genes)*1.5),4.1),squeeze=False,layout='constrained')
    for j,gene in enumerate(genes):
        vmax=max(obs[:,j].max(),rec[:,j].max())
        for i,mat in enumerate([obs,rec]):
            ax=axes[i,j];im=ax.scatter(xy[:,0],xy[:,1],c=mat[:,j],s=1,cmap='viridis',vmin=0,vmax=vmax,rasterized=True)
            ax.invert_yaxis();ax.set_aspect('equal');ax.set_axis_off()
            ax.set_title(gene if i==0 else '',fontsize=7)
        fig.colorbar(im,ax=axes[:,j],shrink=.55,location='bottom',label='log1p normalized')
    fig.suptitle('Observed counts (top) / decoder expectation (bottom)',fontsize=9)
    save(fig,dest/'marker_spatial')
    meta['status']='complete';w.write(dest/'marker_provenance.json',meta)
    print(f'Marker panels: {run["sample"]}, {len(genes)} genes; absent: {missing}',flush=True)
