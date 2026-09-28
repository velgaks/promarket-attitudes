"""Run each reproducible stage, stopping on errors."""
from pathlib import Path
import subprocess,sys,argparse

parser=argparse.ArgumentParser()
parser.add_argument('--no-note',action='store_true',help='Rebuild data, checks, charts and documentation only')
args=parser.parse_args()
base=Path(__file__).resolve().parent
steps=['analyze.py','index_checks.py','verify.py','document_sources.py','pew_supplement.py',
       'monitoring_extract.py','monitoring_inventory.py','monitoring_analysis.py',
       'extended_attitudes.py','extended_published.py','ess_analysis.py','issp_analysis.py','issp_documentation.py','latest_appendix.py','variable_audit.py','market_coherence.py','figures.py','question_inventory.py','question_trend_data.py','question_trends.py']
if not args.no_note:steps+=['build_note.py','report_qa.py','package.py']
for step in steps:
    print(f'Running {step}',flush=True)
    subprocess.run([sys.executable,str(base/step)],check=True)
