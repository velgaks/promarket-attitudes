"""Package code and aggregate outputs, explicitly excluding respondent data."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import hashlib,json
from analyze import ROOT

def main():
    paths=[ROOT/n for n in ['README.md','requirements.txt','requirements-lock.txt','.gitignore']]
    for folder,pattern in [('scripts','*.py'),('docs','*.csv'),('data/source_manifests','*.json'),
                           ('output/tables','*.csv'),('output/tables','*.json'),('output/figures','*.png'),
                           ('output/figures','*.svg'),('output/pdf','*.pdf'),('output','*.md')]:
        paths.extend((ROOT/folder).glob(pattern))
    if (ROOT/'docs/visual_review.json').exists():paths.append(ROOT/'docs/visual_review.json')
    if (ROOT/'docs/question_trends_visual_review.json').exists():paths.append(ROOT/'docs/question_trends_visual_review.json')
    if all(json.loads((ROOT/'output/tables/coverage_status.json').read_text()).values()):
        paths=[p for p in paths if '_interim' not in p.name]
    current_figures=json.loads((ROOT/'output/tables/figure_manifest.json').read_text())['figures']
    paths=[p for p in paths if p.parent!=ROOT/'output/figures' or p.stem in current_figures]
    question_dir=ROOT/'output/question_trends'
    if (question_dir/'manifest.json').exists():
        question_manifest=json.loads((question_dir/'manifest.json').read_text())
        names=['index.html','README.md','manifest.json','all_chart_data.csv','selection_audit.csv','chart_inventory.csv']
        names += [f'{name}.{ext}' for name in question_manifest['chart_ids'] for ext in ['png','svg','csv']]
        paths.extend(question_dir/name for name in names)
    target=ROOT/'output/reproducibility_package.zip'
    with ZipFile(target,'w',ZIP_DEFLATED) as z:
        for p in paths:z.write(p,p.relative_to(ROOT))
    # Only a positive allowlist enters the archive. Never bundle data/raw,
    # data/processed, source PDFs, downloaded originals, tmp or credentials.
    summary={'file':str(target.relative_to(ROOT)),'files':len(paths),'bytes':target.stat().st_size,
             'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'contains_microdata':False}
    (ROOT/'output/package_manifest.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
    print(json.dumps(summary))

if __name__=='__main__':main()
