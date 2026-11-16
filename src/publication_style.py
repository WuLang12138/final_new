"""Publication-only presentation; never changes training, labels or embeddings."""
from pathlib import Path
import json
import xml.etree.ElementTree as ET
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba

ROOT = Path(__file__).resolve().parents[1]
STYLE_FILE = ROOT / 'config/publication_style.json'
STYLE = json.loads(STYLE_FILE.read_text(encoding='utf-8'))

def configure():
    mpl.rcParams.update({
        'font.family':'sans-serif', 'font.sans-serif':['Arial','DejaVu Sans'],
        'font.size':7, 'axes.titlesize':7.5, 'axes.labelsize':7,
        'xtick.labelsize':6.5, 'ytick.labelsize':6.5, 'axes.linewidth':.6,
        'svg.fonttype':'none', 'svg.hashsalt':'SpaSRD-publication',
        'pdf.fonttype':42, 'ps.fonttype':42, 'legend.frameon':False,
        'figure.facecolor':'white', 'savefig.facecolor':'white',
        'axes.spines.top':False, 'axes.spines.right':False,
    })

def distributions(ax, values, labels, colors, violin=False, horizontal=False):
    """Every observation is shown; jitter is deterministic and unpaired."""
    import numpy as np
    for pos, data in enumerate(values,1):
        v=np.asarray(data,dtype=float);v=v[np.isfinite(v)]
        col=colors[pos-1]
        if not len(v):continue
        if violin and len(v)>1 and np.ptp(v)>1e-12:
            parts=ax.violinplot([v],positions=[pos],widths=.8,showextrema=False,vert=not horizontal)
            for body in parts['bodies']:
                body.set_facecolor(col);body.set_edgecolor(col);body.set_alpha(.23)
        bp=ax.boxplot([v],positions=[pos],vert=not horizontal,patch_artist=True,
            widths=.25 if violin else .55,showfliers=False,manage_ticks=False,
            medianprops={'color':'#202020','linewidth':.9},
            whiskerprops={'linewidth':.6},capprops={'linewidth':.6},
            boxprops={'linewidth':.7})
        bp['boxes'][0].set_facecolor(to_rgba(col,.2));bp['boxes'][0].set_edgecolor(col)
        jitter=pos+np.linspace(-.12,.12,len(v))
        ax.scatter(v if horizontal else jitter,jitter if horizontal else v,
            s=10,c=col,edgecolors='white',linewidths=.2,zorder=3)
    if horizontal:
        ax.set_yticks(range(1,len(labels)+1),labels);ax.set_ylim(len(labels)+.65,.35)
        ax.xaxis.grid(True,color='#e5e5e5',linewidth=.45);ax.set_axisbelow(True)
    else:
        ax.set_xticks(range(1,len(labels)+1),labels);ax.set_xlim(.35,len(labels)+.65)
        ax.yaxis.grid(True,color='#e5e5e5',linewidth=.45);ax.set_axisbelow(True)

def export(fig, output, stem):
    """True vector geometry and text; only original microscopy stays raster.

    Temporary files prevent truncating a completed figure on export failure.
    No labels or spatial positions are interpolated for presentation.
    """
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    for artist in fig.findobj():
        if hasattr(artist,'get_rasterized') and artist.get_rasterized():artist.set_rasterized(False)
    pending=[]
    try:
        for ext in ['svg','pdf','png']:
            dest=output/f'{stem}.{ext}';tmp=output/f'.{stem}.pending.{ext}'
            fig.savefig(tmp,format=ext,dpi=STYLE['preview_dpi'],bbox_inches='tight',facecolor='white')
            pending.append((tmp,dest))
        tree=ET.parse(pending[0][0]); ns={'s':'http://www.w3.org/2000/svg'}
        images=len(tree.findall('.//s:image',ns))
        has_histology=stem in {'151507_all_methods_spatial','human_breast_cancer_all_methods_spatial'}
        if images and not has_histology:raise ValueError(f'Unexpected raster image inside vector figure: {stem}')
        if not tree.findall('.//s:text',ns):raise ValueError('SVG text was unexpectedly outlined')
        for tmp,dest in pending:tmp.replace(dest)
    except PermissionError as exc:
        raise PermissionError(f'请关闭正在预览的 {stem} 图件，然后重跑绘图；模型和UMAP缓存不受影响。') from exc
    finally:
        plt.close(fig)
        for tmp,_ in pending:
            if tmp.exists():tmp.unlink()
    return {'stem':stem,'raster_images':images,'vector_text':True}
