"""One-time checked figure import and publication-source index. No training."""
from pathlib import Path
import json,csv,hashlib,shutil,os
ROOT=Path(__file__).resolve().parents[1];PROJECT=ROOT.parent
OUT=ROOT/'results/figures';OUT.mkdir(parents=True,exist_ok=True)
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig')))
def relative(p):return Path(os.path.relpath(p,ROOT)).as_posix()
records=[]
for source,tag in [('manuscript_illustrated_20261026','main'),('manuscript_external_comparison_20261027','external')]:
    folder=PROJECT/'analysis'/source/'figures'
    dest=OUT/'historical_manuscript'/tag;dest.mkdir(parents=True,exist_ok=True)
    for p in folder.iterdir():
        if not p.is_file():continue
        target=dest/p.name
        if target.exists() and sha(target)!=sha(p):raise ValueError('Migration collision: '+str(target))
        if not target.exists():shutil.copy2(p,target)
        assert sha(p)==sha(target)
        records.append(dict(source=relative(p),target=relative(target),sha256=sha(target),image=p.suffix.lower() in {'.png','.pdf','.svg','.jpg','.jpeg','.tif','.tiff'}))
    for name in ['figure_sources.json','figure_seed_metrics.csv']:
        p=folder.parent/name
        if p.exists():shutil.copy2(p,dest/name)
(OUT/'migration_manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
mechanism=OUT/'source_data';mechanism.mkdir(exist_ok=True)
for p in (PROJECT/'analysis/publication_package_20261019/peak/source_data').glob('figure6_*.csv'):shutil.copy2(p,mechanism/p.name)

# Frozen manuscript choices, independent of the last training notebook run.
manifest=read(PROJECT/'analysis/manuscript_revision_20261018/evidence/publication_run_manifest.json')
comp=PROJECT/'sidmgf_paper_support/experiments/comparison_methods'
repro=PROJECT/'sidmgf_paper_support/experiments/reproduction'
cfg=read(ROOT/'config/paper.json');new=[]
def add(method,dataset,sample,seed,p,ari,protocol,expected=None):
    digest=sha(p)
    if expected:assert digest==expected,str(p)
    new.append(dict(method=method,dataset=dataset,sample=sample,seed=int(seed),source=relative(p),sha256=digest,ARI=float(ari),protocol=protocol))
for r in cfg['runs']:
    if r['dataset']=='HBC' or r['profile']!='paper':continue
    p=ROOT/r['prediction']/'best/prediction.npz'
    record=next(x for x in manifest['core'] if x['method']=='SpaSRD' and x['sample']==r['sample'] and x['seed']==r['seed'])
    add('SpaSRD',r['dataset'],r['sample'],r['seed'],p,record['peak'],'paper / donor-shared; peak')
for r in read(ROOT/'config/hbc_combined_figures.json')['runs']:
    if r['arm']!='combined' or r['profile']!='refined':continue
    d=ROOT/r['directory'];report=read(d/'report.json');assert sha(d/'report.json')==r['report_sha256']
    add('SpaSRD','HBC','human_breast_cancer',r['seed'],d/'best.npz',report['reports']['best']['ARI'],'combined / common graph / matched settings; peak',report['files']['best.npz'])
for r in rows(comp/'results/publication_figures/seed_metrics.csv'):
    if r['method'] not in ['SiDMGF-spatial','SiDMGF-full'] or r['dataset']=='HBC':continue
    add(r['method'],r['dataset'],r['sample'],r['seed'],(comp/r['file']).resolve(),r['ARI'],'matched KNN8; peak',r['sha256'])
for r in manifest['hbc_tuned']:
    m={'gcn_spatial_hbc_transfer':'SiDMGF-spatial','gcn_full_hbc_transfer':'SiDMGF-full'}.get(r['method'])
    if m:
        p=repro/r['directory']/'eval_peak.npz';done=read(p.parent/'completed.json')
        add(m,'HBC',r['sample'],r['seed'],p,r['peak'],'HBC matched settings; peak',done['files'][p.name])
for r in rows(PROJECT/'sidmgf_paper_support/experiments/comparison_methods_v2/results/comparison_tables/seed_results.csv'):
    if r['endpoint']=='eval_peak':add(r['method'],r['dataset'],r['sample'],r['seed'],PROJECT/r['source'],r['ARI'],'official-code adapted KNN8 v2; primary readout',r['sha256'])
assert len(new)==1125,len(new)
assert len({(r['method'],r['sample'],r['seed']) for r in new})==len(new)
dest=ROOT/'config/publication_figures.json'
dest.write_text(json.dumps(dict(schema=1,output='results/figures/publication',seed=0,hbc='combined',checkpoint='best',runs=new),ensure_ascii=False,indent=2),encoding='utf-8')
print('Copied',len(records),'files; indexed',len(new),'predictions; old images not deleted yet.')
