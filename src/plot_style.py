"""Shared categorical colours and registered histology; presentation only."""
from functools import lru_cache
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.collections import EllipseCollection
from scipy.spatial import cKDTree
from . import workflow as w


def region_style(dataset,labels):
    configured=w.configuration()['plotting']['region_colors'][dataset]
    labels=set(map(str,labels))
    ordered=[lab for lab in configured if lab in labels]+sorted(labels-set(configured))
    # Unexpected categories are explicit gray, never silently reassigned another region's colour.
    colors={lab:configured.get(lab,'#737373') for lab in ordered}
    return ordered,colors


@lru_cache(maxsize=16)
def histology(dataset,sample):
    if dataset not in {'DLPFC','HBC'}:return None
    root=w.ROOT/'data'/dataset/sample/'histology'
    manifest=w.read(root/'registration.json')
    for name,digest in manifest['files'].items():
        if w.sha(root/name)!=digest:raise ValueError('Histology asset changed: '+str(root/name))
    scale=w.read(root/'scalefactors_json.json')['tissue_lowres_scalef']
    positions=pd.read_csv(root/'tissue_positions_list.csv',header=None,
        names=['barcode','in_tissue','row','col','y','x'],index_col=0)
    image=plt.imread(root/'tissue_lowres_image.png')
    xy=positions.loc[positions.in_tissue.eq(1),['x','y']].to_numpy()
    step=float(np.median(cKDTree(xy).query(xy,k=2)[0][:,1]))
    margin=w.configuration()['plotting']['spatial_style']['crop_margin_spacings']*step
    bounds=[max(-.5/scale,xy[:,0].min()-margin),min((image.shape[1]-.5)/scale,xy[:,0].max()+margin),
            max(-.5/scale,xy[:,1].min()-margin),min((image.shape[0]-.5)/scale,xy[:,1].max()+margin)]
    return dict(image=image,scale=scale,positions=positions,step=step,bounds=bounds,
                assets={name:digest for name,digest in manifest['files'].items()})


def spatial_panel(ax,dataset,sample,xy,obs_names,values,colors,*,rasterized=True):
    xy=np.asarray(xy);style=w.configuration()['plotting']['spatial_style'];bg=histology(dataset,sample)
    if bg is None:
        artist=ax.scatter(xy[:,0],xy[:,1],c=[colors[str(v)] for v in values],
            s=style['non_visium_marker_area'],linewidths=0,edgecolors='none',rasterized=rasterized)
        ax.set_aspect('equal');ax.invert_yaxis();ax.axis('off')
        return dict(background='none: no registered histology supplied',point_count=len(xy),
                    palette=colors,point_area=style['non_visium_marker_area'])
    expected=bg['positions'].loc[np.asarray(obs_names,dtype=str),['x','y']].to_numpy()
    if not np.array_equal(expected,xy):raise ValueError('Histology registration mismatch: '+sample)
    im=bg['image'];sc=bg['scale']
    ax.imshow(im,origin='upper',extent=(-.5/sc,(im.shape[1]-.5)/sc,(im.shape[0]-.5)/sc,-.5/sc),
              alpha=style['histology_alpha'],interpolation='nearest',zorder=0)
    diameter=bg['step']*style['marker_diameter_spacing_ratio']
    artist=EllipseCollection(np.full(len(xy),diameter),np.full(len(xy),diameter),np.zeros(len(xy)),
        units='xy',offsets=xy,transOffset=ax.transData,facecolors=[colors[str(v)] for v in values],
        edgecolors='none',linewidths=0,antialiaseds=True,rasterized=rasterized,zorder=1)
    ax.add_collection(artist)
    left,right,top,bottom=bg['bounds'];ax.set_xlim(left,right);ax.set_ylim(bottom,top)
    ax.set_aspect('equal');ax.set_xticks([]);ax.set_yticks([])
    for spine in ax.spines.values():spine.set_visible(True);spine.set_linewidth(.6);spine.set_edgecolor('#444444')
    return dict(background='registered original H&E low-resolution image',assets=bg['assets'],
        scale=sc,coordinate_max_abs_delta=0,point_count=len(xy),palette=colors,crop_bounds_fullres=bg['bounds'],
        histology_alpha=style['histology_alpha'],display_diameter_fullres=diameter,
        diameter_to_spacing=style['marker_diameter_spacing_ratio'],
        note='Display diameter is not physical capture diameter; no new points, interpolation, smoothing, or label changes.')
