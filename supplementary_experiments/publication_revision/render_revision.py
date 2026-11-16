"""Use the packaged DOCX renderer with a PDF exported by Microsoft Word."""
import importlib.util, os, shutil, sys, tempfile
import argparse
from pathlib import Path
HERE=Path(__file__).resolve().parents[2]/'results/manuscript'
parser=argparse.ArgumentParser()
parser.add_argument('--document',default='SpaSRD_V5多方法图文统一修订稿.docx')
parser.add_argument('--qa',default='qa')
args=parser.parse_args()
RUNTIME=Path.home()/'.cache/codex-runtimes/codex-primary-runtime'
renderers=list((Path.home()/'.codex/plugins/cache/openai-primary-runtime/documents').glob('*/skills/documents/render_docx.py'))
if not renderers:raise FileNotFoundError('Install the documents runtime to render the manuscript.')
RENDERER=max(renderers,key=lambda p:p.stat().st_mtime)
os.environ['PATH']=str(RUNTIME/'dependencies/native/poppler/bin')+os.pathsep+os.environ['PATH']
tempfile.tempdir=str(HERE/args.qa)
spec=importlib.util.spec_from_file_location('docx_skill_renderer',RENDERER)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
def native_pdf(doc_path,user_profile,convert_tmp_dir,stem,verbose):
    output=Path(convert_tmp_dir)/(stem+'.pdf')
    shutil.copy2(HERE/args.qa/'word_render.pdf',output)
    return str(output),'Microsoft Word native export; LibreOffice unavailable.'
module.convert_to_pdf=native_pdf
sys.argv=[str(RENDERER),str(HERE/args.document),'--output_dir',str(HERE/args.qa),'--emit_pdf','--dpi','120']
module.main()
