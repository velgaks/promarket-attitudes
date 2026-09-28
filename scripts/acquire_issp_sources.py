"""Acquire public ISSP documentation and inventory locally supplied microdata.

GESIS microdata require the user's authenticated download. This script never
substitutes the international 2019 file for the separate Ukrainian study.
"""
import hashlib
import json
from pathlib import Path
import urllib.request
import zipfile

import fitz

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'data/documentation/issp'
RAW = ROOT / 'data/raw/issp'
DOCUMENTS = {
    '2008_source_questionnaire': 16201,
    '2009_variable_report': 48548,
    '2009_ua_questionnaire': 19329,
    '2009_ua_background': 19281,
    '2009_monitoring': 20572,
    '2019_source_questionnaire': 70641,
    'replication_crosswalk': 73907,
}
STUDIES = [
    dict(study='ZA4950', version='2.3.0', module='Religion III', year=2008,
         doi='10.4232/1.13161', ukraine_n=2036, fieldwork='2008-10',
         role='Business and industry confidence; single Ukrainian observation'),
    dict(study='ZA5400', version='4.0.0', module='Social Inequality IV', year=2009,
         doi='10.4232/1.12777', ukraine_n=2012, fieldwork='2009-06',
         role='Ukraine must be selected from the integrated file'),
    dict(study='ZA7810', version='1.0.0', module='Social Inequality V (Ukraine)', year=2019,
         doi='10.4232/1.13853', ukraine_n=2001, fieldwork='2019-08-31/2019-09-14',
         role='Separate Ukrainian study; Ukraine is absent from ZA7600; sampling deviations require review'),
]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    DOC.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    documents = []
    for name, number in DOCUMENTS.items():
        p = DOC / (name + '.pdf')
        url = f'https://access.gesis.org/dbk/{number}'
        if not p.exists():
            payload = urllib.request.urlopen(url, timeout=60).read()
            assert payload.startswith(b'%PDF'), (name, 'Expected PDF')
            p.write_bytes(payload)
        with fitz.open(p) as pdf:
            p.with_suffix('.txt').write_text('\n'.join(x.get_text() for x in pdf), encoding='utf8')
            documents.append(dict(file=str(p.relative_to(ROOT)), source_url=url,
                                  sha256=sha(p), pages=len(pdf)))
    studies = []
    for study in STUDIES:
        study = dict(study)
        candidates = list(ROOT.glob(study['study']+'*')) + list(RAW.glob(study['study']+'*'))
        files = []
        for p in candidates:
            if not p.is_file() or p.suffix.lower() not in ['.zip', '.sav', '.dta']: continue
            record = dict(file=str(p.relative_to(ROOT)), sha256=sha(p), bytes=p.stat().st_size)
            if p.suffix.lower()=='.zip':
                with zipfile.ZipFile(p) as z:
                    record['members'] = z.namelist()
                    assert any(n.lower().endswith(('.sav','.dta')) for n in z.namelist()), (p,'No microdata')
            files.append(record)
        study.update(catalog_url='https://search.gesis.org/research_data/'+study['study'],
                     local_files=files, acquisition_status='acquired; analysis checks recorded in issp_validation.json' if files else 'awaiting authenticated download')
        studies.append(study)
    manifest = dict(checked='2026-09-28', status='documentation and microdata acquired' if all(s['local_files'] for s in studies) else 'microdata acquisition incomplete',
                    participation_source='https://www.gesis.org/issp/ueberblick',
                    studies=studies, documents=documents,
                    instructions='Sign in to GESIS and download the listed study versions as SPSS or Stata. Place original ZIP/SAV/DTA files in the project root or data/raw/issp. Retain supplied documentation. Raw files are not redistributed. Do not use ZA7600 for Ukraine 2019.')
    dest=ROOT/'data/source_manifests/issp_acquisition.json'
    dest.write_text(json.dumps(manifest,indent=2),encoding='utf8')
    print(json.dumps(dict(documentation_files=len(documents), studies=[dict(study=s['study'],status=s['acquisition_status']) for s in studies]),indent=2))


if __name__=='__main__': main()
