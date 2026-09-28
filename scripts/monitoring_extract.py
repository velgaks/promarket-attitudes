"""Extract published monitoring tables with a question/year/source audit trail.

Uses the actual PDF table cells, not manually entered estimates. No microdata,
confidence intervals or composite respondent-level indices are inferred.
Run: python scripts/monitoring_acquire.py; python scripts/monitoring_extract.py
"""
from functools import lru_cache
from pathlib import Path
import json
import hashlib
import re
import pandas as pd
import pymupdf
from acquire import ROOT, download

SOURCE = ROOT / 'data/documentation/monitoring'
OUT = ROOT / 'output/tables'
ALL = []
MISSING = []
SPEC = []


def fix_encoding(text):
    def fix(match):
        try:
            return match.group().encode('latin1').decode('cp1251')
        except UnicodeError:
            return match.group()
    return re.sub(r'[\x80-\xff]+', fix, text)


@lru_cache(None)
def page_text(filename, page):
    with pymupdf.open(SOURCE / filename) as doc:
        return fix_encoding(doc[page - 1].get_text())


def table(filename, page, printed, code, item, categories, priority=1):
    text = page_text(filename, page)
    # Question identifiers use both Cyrillic and Latin a in the originals.
    marker = re.escape(code).replace('a', '[aа]')
    start = re.search(r'(?m)^\s*' + marker + r'\.', text)
    assert start, (filename, page, code)
    block = text[start.end():]
    next_question = re.search(r'(?m)^\s*[aаb][a-z]?\d+[a-z]?\.', block)
    if next_question:
        block = block[:next_question.start()]
    first_value = re.search(r'\d+[.,]\d+', block)
    assert first_value, (filename, page, code)
    # Header years occur before the first decimal-valued response percentage.
    headers = list(re.finditer(r'(?<!\d)(?:19|20)\d{2}(?!\d)', block[:first_value.start()]))
    years = [int(m.group()) for m in headers]
    assert years and len(set(years)) == len(years), (filename, page, years)
    body = block[headers[-1].end():]
    # Some PDF text runs put the first cell on the same line as its row label.
    body = re.sub(r'(?<=[A-Za-zА-Яа-яІіЇїЄєҐґ])\s+(?=\d+[.,]\d+(?:\s|$))', '\n', body)
    rows = []
    values = []
    for line in body.splitlines():
        line = line.strip()
        if not line:
            continue
        if re.fullmatch(r'(?:\d+[.,]\d+|[—–-])(?:\s*(?:\d+[.,]\d+|[—–-]))*', line):
            values.extend(None if token in ['—', '–', '-'] else float(token.replace(',', '.'))
                          for token in re.findall(r'\d+[.,]\d+|[—–-]', line))
        else:
            if values:
                rows.append(values)
                values = []
            if len(rows) >= len(categories):
                break
    if values and len(rows) < len(categories):
        rows.append(values)
    assert len(rows) >= len(categories), (filename, page, code, rows)
    rows = rows[:len(categories)]
    assert all(len(row) == len(years) for row in rows), (filename, page, code, years, rows)
    meta = dict(item=item, source_file=filename, pdf_page=page, printed_page=printed,
                question_code=code, priority=priority)
    SPEC.append({**meta, 'years_in_table': ';'.join(map(str, years))})
    for j, year in enumerate(years):
        if all(row[j] is None for row in rows):
            MISSING.append({**meta, 'year': year, 'status': 'dash_in_published_table'})
            continue
        assert all(row[j] is not None for row in rows), (meta, year)
        for category, row in zip(categories, rows):
            ALL.append({**meta, 'year': year, 'response': category, 'percent': row[j]})


NEG3 = ['negative', 'ambivalent', 'positive', 'no_answer']
APPROVE = ['strongly_disapprove', 'rather_disapprove', 'ambivalent', 'rather_approve', 'strongly_approve', 'no_answer']
YES3 = ['yes', 'no', 'dont_know', 'no_answer']
YES5 = ['no', 'rather_no', 'dont_know', 'rather_yes', 'yes', 'no_answer']
ATT5 = ['negative', 'rather_negative', 'dont_know', 'rather_positive', 'positive', 'no_answer']
REVERSE = ['yes', 'rather_yes', 'dont_know', 'rather_no', 'no', 'no_answer']
ROLE = ['minimal_state_market', 'mixed_state_market', 'planned_economy', 'dont_know', 'no_answer']
POLITICS = ['socialism', 'capitalism', 'both', 'neither', 'other', 'dont_know', 'no_answer']


def extract():
    p = 'panina-1994-2005.pdf'
    table(p, 20, 20, 'a2', 'private_business', APPROVE)
    for code, item in [('a3','privatise_large'), ('a4','privatise_small'), ('a5','privatise_land')]:
        table(p,21,21,code,item,NEG3)
    table(p,21,21,'a6','land_sales_general',YES3)
    table(p,22,22,'a7','state_market_role',ROLE)
    table(p,22,22,'a8','work_private_employer',YES5)
    table(p,25,25,'b2','socialism_capitalism_political_support',POLITICS)

    p = 'soc-mon-2012.pdf'
    table(p,529,529,'a2','private_business',APPROVE,2)
    table(p,533,533,'b2','socialism_capitalism_political_support',POLITICS,2)
    table('dodatki2016.pdf',6,430,'b2','socialism_capitalism_political_support',POLITICS,3)
    table('soc-mon-2013.pdf',447,447,'a7','state_market_role',ROLE,2)
    table('dodatki2018.pdf',4,418,'a6','land_sales_general',YES3,3)
    p = 'monitoring-2021dlya-tipografii.pdf'
    for code, item in [('a3','privatise_large'), ('a4','privatise_small'), ('a5','privatise_land')]:
        table(p,624,624,code,item,NEG3,4)
    table(p,624,624,'an11','land_sales_agricultural',YES3,4)
    table(p,625,625,'a7','state_market_role',ROLE,4)
    table(p,625,625,'a8','work_private_employer',YES5,4)

    items = ['retrospective_small','retrospective_large','retrospective_land',
             'existing_private_small','existing_private_large','existing_private_land',
             'renationalise_small','renationalise_large','renationalise_land']
    pages_2013 = [447,448,448,448,449,449,449,450,450]
    pages_2017 = [3,3,4,4,4,5,5,5,6]
    pages_2020 = [443,444,444,445,445,445,445,446,446]
    for i,item in enumerate(items):
        cats = YES5 if i<3 else ATT5 if i<6 else REVERSE
        table('soc-mon-2013.pdf',pages_2013[i],pages_2013[i],f'an{i+1}',item,cats,1)
        table('dodatki2017.pdf',pages_2017[i],pages_2017[i]+486,f'an{i+1}',item,cats,2)
        table('mon2020.pdf',pages_2020[i],pages_2020[i],f'a{i+3}r',item,cats,3)
    table('mon2020.pdf',447,447,'a12r','land_ownership_rights',
          ['full_ownership_including_sale','inheritable_use_no_sale','community_ownership','state_ownership','dont_know','no_answer'],3)
    table('monitoring-2024.pdf',416,416,'a2','ownership_policy',
          ['nationalise','retain_state_firms','privatise_except_efficient_state_firms','broad_privatisation','dont_know_or_no_answer'],3)
    table('monitoring-2025.pdf',394,394,'a2','ownership_policy',
          ['nationalise','retain_state_firms','privatise_except_efficient_state_firms','broad_privatisation','dont_know_or_no_answer'],4)
    # The 2014 table uses columns: count, % of all, % of answers.
    # Read the all-respondent column; derive nonresponse only from printed Ns.
    raw=page_text('us-2014.pdf',1).split('a2.')[1].split('Признак')[0]
    n,valid=map(int,re.search(r'Всего\s+(\d+)\.\s+Ответили\s+(\d+)',raw).groups())
    assert n==1800 and valid==1764
    cells=re.findall(r'(?<!\d)(\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)(?!\d)',raw.split('Частота')[1])
    assert len(cells)==5 and sum(int(x[0]) for x in cells)==valid
    meta=dict(item='private_business',source_file='us-2014.pdf',pdf_page=1,printed_page='unpaginated',question_code='a2',priority=4)
    SPEC.append({**meta,'years_in_table':'2014'})
    for category,(_,all_pct,valid_pct) in zip(APPROVE[:-1],cells):
        ALL.append({**meta,'year':2014,'response':category,'percent':float(all_pct)})
    ALL.append({**meta,'year':2014,'response':'no_answer','percent':round(100*(n-valid)/n,1)})


def main():
    # Reproduction uses the recorded archive, not a new crawl of a changing site.
    for r in pd.read_csv(ROOT/'docs/monitoring_sources.csv').itertuples():
        path=ROOT/r.local_path
        manifest_path=ROOT/'data/source_manifests'/f'{path.name}.json'
        expected=json.loads(manifest_path.read_text(encoding='utf8'))['sha256']
        if not path.exists():
            download(r.download_url,r.local_path,r.title)
        assert hashlib.sha256(path.read_bytes()).hexdigest()==expected, (
            'Monitoring source version changed; review before extraction',path.name)
    extract()
    data=pd.DataFrame(ALL)
    keys=['item','year','response']
    preferred=data.sort_values('priority',kind='stable').drop_duplicates(keys,keep='last').copy()
    preferred['within_note_period']=preferred.year.le(2020)
    preferred['unit']='percent_of_all_respondents_as_published'
    preferred['uncertainty']='not_published'
    preferred['cell_method']='extracted_published_percentage'
    preferred.loc[preferred.item.eq('private_business') & preferred.year.eq(2014) & preferred.response.eq('no_answer'),'cell_method']='derived_from_published_total_and_answered_counts'
    preferred['source_url'] = preferred.source_file.map(source_urls())
    assert preferred.source_url.notna().all()
    for filename in preferred.source_file.unique():
        manifest=json.loads((ROOT/'data/source_manifests'/f'{filename}.json').read_text(encoding='utf8'))
        assert hashlib.sha256((SOURCE/filename).read_bytes()).hexdigest()==manifest['sha256'], filename
    preferred=preferred.sort_values(keys)
    totals=preferred.groupby(['item','year']).percent.sum()
    assert (totals.between(99.65,100.35)).all(), totals[~totals.between(99.65,100.35)]
    assert preferred.percent.between(0,100).all()
    data.to_csv(OUT/'monitoring_source_cells.csv',index=False,encoding='utf-8-sig')
    preferred.to_csv(OUT/'monitoring_published_results.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(SPEC).to_csv(ROOT/'docs/monitoring_table_locations.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(MISSING).to_csv(OUT/'monitoring_explicit_table_gaps.csv',index=False,encoding='utf-8-sig')
    discrepancies=data.groupby(keys).percent.agg(['min','max']).reset_index()
    discrepancies=discrepancies[(discrepancies['max']-discrepancies['min']).abs()>1e-8]
    discrepancies.to_csv(OUT/'monitoring_duplicate_discrepancies.csv',index=False)
    inventory=preferred.groupby(['item','year'],as_index=False).agg(
        source_file=('source_file','first'),pdf_page=('pdf_page','first'),printed_page=('printed_page','first'),
        question_code=('question_code','first'),source_url=('source_url','first'),categories=('response','size'),
        response_percent_sum=('percent','sum'))
    inventory['status']='verified_published_response_table'
    inventory.to_csv(OUT/'monitoring_wave_inventory.csv',index=False,encoding='utf-8-sig')
    validation=dict(status='passed',source_cells=len(data),canonical_cells=len(preferred),
                    item_waves=len(inventory),items=int(preferred.item.nunique()),
                    years=sorted(map(int,preferred.year.unique())),
                    duplicate_discrepancies=len(discrepancies),
                    checks=['Unique item/year/response keys','All percentages in 0-100',
                            'Full response sums within 0.35 percentage points of 100',
                            'Each PDF row has exactly one cell per header year',
                            'Explicit table dashes retained as missing, never zero'])
    (OUT/'monitoring_validation.json').write_text(json.dumps(validation,indent=2),encoding='utf8')
    print(json.dumps(validation,indent=2))
    print(inventory.groupby('item').year.apply(list).to_string())


def source_urls():
    result={}
    for f in (ROOT/'data/source_manifests').glob('*.json'):
        record=json.loads(f.read_text(encoding='utf8'))
        if 'path' in record and 'url' in record:
            result[Path(record['path']).name]=record['url']
    return result


if __name__=='__main__':
    main()
