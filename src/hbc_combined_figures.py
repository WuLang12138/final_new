"""Spatial class maps for completed control/combined runs; never train.

Evidence: full tissue maps plus identically cropped reference-region views.
Python image plates, PNG/PDF/SVG, unchanged observations and predictions.
"""
from pathlib import Path
import importlib.util
import json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
from src import workflow as w


def selected_jobs(profile):
    cfg=w.read(ROOT/'config/hbc_combined_figures.json')
    jobs=[j for j in cfg['runs'] if j['profile']==profile]
    if not jobs:raise ValueError('主库未导入该配置：'+profile)
    return jobs


def verify(job):
    dest=w.local(job['directory'])
    if w.sha(dest/'report.json')!=job['report_sha256']:raise ValueError('导入报告校验失败')
    report=w.read(dest/'report.json')
    if any(report[k]!=job[k] for k in ['profile','arm','seed']):raise ValueError('导入配置不一致')
    for name,digest in report['files'].items():
        if w.sha(dest/name)!=digest:raise ValueError('已复制结果缺失或改变：'+str(dest/name))
    return True

from src.plot_style import region_style,spatial_panel,histology
from src.figures import align,save
from sklearn.metrics import adjusted_rand_score,normalized_mutual_info_score
import matplotlib.pyplot as plt


def generate(profile='refined',seeds=(0,1,2,3,42),endpoints=('best',),
             zoom_regions=('DCIS/LCIS_2','DCIS/LCIS_5','IDC_3')):
    """Return generated files and recomputed metrics for notebook display."""
    if not seeds or not endpoints:raise ValueError('Choose at least one seed and endpoint')
    if not set(endpoints)<= {'best','final'}:raise ValueError('Endpoint must be best or final')
    jobs=selected_jobs(profile)
    if not set(seeds)<=set(j['seed'] for j in jobs):raise ValueError('Unknown seed')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'svg.fonttype':'none',
                         'pdf.fonttype':42,'legend.frameon':False})
    output=ROOT/'results/hbc_combined'/profile/'figures';files=[];records=[]
    for seed in seeds:
        objects={}
        for arm in ['control','combined']:
            job=next(j for j in jobs if j['arm']==arm and j['seed']==seed)
            if not verify(job):raise FileNotFoundError('请先完成训练：'+job['directory'])
            dest=ROOT/job['directory'];reports=w.read(dest/'report.json')['reports']
            for endpoint in endpoints:
                source=dest/(endpoint+'.npz')
                with np.load(source,allow_pickle=False) as z:o={k:z[k].copy() for k in z.files}
                o['reference']=o['reference'].astype(str);o['prediction']=o['prediction'].astype(str)
                o['mapped']=align(o['reference'],o['prediction'])[1]
                ari=float(adjusted_rand_score(o['reference'],o['prediction']))
                if abs(ari-reports[endpoint]['ARI'])>1e-10:raise ValueError('ARI report mismatch')
                o['ARI']=ari;objects[arm,endpoint]=o
                records.append(dict(profile=profile,seed=seed,arm=arm,endpoint=endpoint,epoch=int(o['epoch']),ARI=ari,
                    NMI=float(normalized_mutual_info_score(o['reference'],o['prediction'])),
                    source=source.relative_to(ROOT).as_posix(),sha256=w.sha(source)))
        for endpoint in endpoints:
            control=objects['control',endpoint];combined=objects['combined',endpoint]
            for key in ['obs_names','reference','spatial']:
                if not np.array_equal(control[key],combined[key]):raise ValueError('Unmatched observations: '+key)
            labels,colors=region_style('HBC',list(control['reference'])+list(control['mapped'])+list(combined['mapped']))
            handles=[plt.Line2D([],[],marker='o',ls='',ms=4,color=colors[l],label=l) for l in labels]
            panels=[(control,control['reference'],'Ground Truth'),
                    (control,control['mapped'],f'SpaSRD-S control\nARI {control["ARI"]:.4f} | epoch {int(control["epoch"])}'),
                    (combined,combined['mapped'],f'SpaSRD-S combined\nARI {combined["ARI"]:.4f} | epoch {int(combined["epoch"])}')]
            folder=output/endpoint/f'seed_{seed}'
            fig,axes=plt.subplots(1,3,figsize=(11.5,5.4),layout='constrained')
            for ax,(o,val,title) in zip(axes,panels):
                style=spatial_panel(ax,'HBC','human_breast_cancer',o['spatial'],o['obs_names'],val,colors)
                ax.set_title(title)
            fig.suptitle(f'HBC | {profile} | {endpoint} | seed {seed}',fontsize=11)
            fig.legend(handles=handles,loc='outside lower center',ncol=5,fontsize=7)
            save(fig,folder/'spatial_comparison');files.append(folder/'spatial_comparison.png')
            if zoom_regions:
                fig,axes=plt.subplots(len(zoom_regions),3,figsize=(10.5,3.1*len(zoom_regions)+1),squeeze=False,layout='constrained')
                step=histology('HBC','human_breast_cancer')['step']
                for line,region in enumerate(zoom_regions):
                    mask=control['reference']==region
                    if not mask.any():raise ValueError('Unknown reference region: '+region)
                    xy=control['spatial'][mask];pad=step*2
                    lo=xy.min(0)-pad;hi=xy.max(0)+pad
                    for ax,(o,val,title) in zip(axes[line],panels):
                        spatial_panel(ax,'HBC','human_breast_cancer',o['spatial'],o['obs_names'],val,colors)
                        ax.set_xlim(lo[0],hi[0]);ax.set_ylim(hi[1],lo[1])
                        # Reference outlines are annotations only; never reassign a cluster.
                        ax.scatter(xy[:,0],xy[:,1],s=12,facecolors='none',edgecolors='black',linewidths=.35,zorder=3)
                        ax.set_title(region+' | '+title.split('\n')[0],fontsize=8)
                fig.suptitle(f'HBC | {profile} | {endpoint} | seed {seed}\n'
                    'Black outlines: reference-region spots; identical crop across methods',fontsize=10)
                fig.legend(handles=handles,loc='outside lower center',ncol=5,fontsize=6)
                save(fig,folder/'region_zoom');files.append(folder/'region_zoom.png')
            table=pd.DataFrame(dict(obs_name=control['obs_names'],x=control['spatial'][:,0],y=control['spatial'][:,1],
                reference=control['reference'],control_prediction=control['prediction'],combined_prediction=combined['prediction'],
                control_display=control['mapped'],combined_display=combined['mapped']))
            table.to_csv(folder/'plot_source.csv',index=False)
            w.write(folder/'provenance.json',dict(profile=profile,seed=seed,endpoint=endpoint,style=style,
                sources=[x for x in records if x['seed']==seed and x['endpoint']==endpoint],
                interpretation='Hungarian matching provides display colours only; cluster colour is not a validated biological identity.',
                reference_used_for='Evaluation, display colour matching and explicit diagnostic crop selection only.',
                integrity='No smoothing, no interpolation, no prediction editing. Best is annotation-assisted ARI selection.',
                region_zoom=list(zoom_regions),script_sha256=w.sha(__file__)))
            print('Saved:',folder,flush=True)
    frame=pd.DataFrame(records)
    tag='_'.join(endpoints)+'_seeds_'+'_'.join(map(str,seeds))
    frame.to_csv(output/(tag+'_metrics.csv'),index=False)
    return frame,files
