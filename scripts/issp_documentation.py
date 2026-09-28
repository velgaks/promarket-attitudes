"""Verify published ISSP anchors and write the question audit."""
import json,re,hashlib
import fitz
import pandas as pd
import pyreadstat
from analyze import ROOT,TABLES

def main():
    source=ROOT/'data/documentation/issp/2009_variable_report.pdf'
    doc=fitz.open(source)
    d,_=pyreadstat.read_sav(str(ROOT/'data/raw/issp/ZA5400_v4-0-0.sav'),usecols=['V5','V32','V33','V36'])
    d=d[d.V5.eq(804)]
    rows=[]
    for field,page in [('V32',99),('V33',101),('V36',107)]:
        text=doc[page-1].get_text(sort=True)
        assert field+' by C_ALPHAN' in text
        line=next(l for l in text.splitlines() if l.startswith('UA '))
        counts=[int(x) for x in re.findall(r'(\d+) \([\d.]+\)',line)]
        assert len(counts)==5
        reported_pct=[float(x) for x in re.findall(r'\d+ \(([\d.]+)\)',line)]
        valid=d[field].between(1,5).sum()
        tail=list(map(int,line.split(')')[-1].split()))
        assert tail[-2]==len(d)==2012 and tail[-1]==valid
        for code,count,pct in zip(range(1,6),counts,reported_pct):
            actual=int(d[field].eq(code).sum())
            assert actual==count and abs(100*actual/valid-pct)<=.050001
            rows.append(dict(survey='ISSP',year=2009,field=field,response_code=code,
                raw_count=actual,published_count=count,valid_n=int(valid),published_percent=pct,
                reproduced_percent=100*actual/valid,source_pdf=source.name,pdf_page=page,
                source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                denominator='Unweighted valid substantive answers, matching codebook',status='passed'))
    pd.DataFrame(rows).to_csv(TABLES/'issp_published_checks.csv',index=False)
    inv=pd.read_csv(TABLES/'issp_variable_inventory.csv')
    cw=pd.read_csv(ROOT/'docs/issp_question_crosswalk.csv')
    text='''# ISSP question audit

Verified 28 September 2026. Ukraine participates in the 2008 Religion III and 2009/2019 Social Inequality modules in the official [GESIS inventory](https://www.gesis.org/issp/ueberblick). No Ukrainian Role of Government or Work Orientations sample is listed. The acquired releases are ZA4950 v2.3.0, ZA5400 v4.0.0 and ZA7810 v1.0.0. Ukraine 2019 is a separate national release, not part of ZA7600. Original microdata remain local.

## Scope and selection

The catalogue audits all 851 fields in the three files, retaining 59 economic attitudes and related beliefs (95 question-wave observations). Thirty-six questions meet the HTML requirement of two observations and an endpoint from 2019. Forty-nine questions have a named affirmative response; the ten open monetary questions use latest means instead. Single-wave items remain in the note's inventory and appendix, without invented trends.

Included: redistribution, taxes, public provision, unequal access to services, inequality and its explanations, fair rewards, perceived routes to success, class conflict, estimated and desired occupational pay, society shapes, and confidence in business. The international tax-aid and labour-mobility items are explicit economic extensions. General religion, identity, personal income, own-pay satisfaction, family occupation, social position and social contacts are excluded. Optional global-income fairness v66 has no valid Ukrainian 2019 observations and is excluded.

## Question and coding checks

The 2009 Ukrainian questionnaire and 2019 national questionnaire preserve comparable response scales for the replicated economic questions. The official replication crosswalk also maps the repeated modules. The tax item in both Ukrainian forms asks about *higher taxes*, without the English source's explicit income-share qualification. The getting-ahead item uses *nationality* in Ukrainian, rather than the English source's *race*. Labels follow these national wordings. University access in 2009 refers to the best chances of entry among students from the best schools; it does not imply that nobody else can enter.

Ordinal answers combine the two positive and two negative endpoints, retaining middle categories and nonresponse. The middle importance category is labelled “Important” following the national forms. The society-shape options are nominal and all five are retained, plus nonresponse. Earnings are monthly hryvnias after taxes in both national forms; values remain nominal. All nonnegative reported amounts are retained, with missing codes excluded and a winsorisation diagnostic exported.

The published 2009 variable report's Ukraine rows for V32, V33 and V36 (PDF pages 99, 101 and 107) independently reproduce every substantive raw response count and the rounded valid-response percentages. These anchors use the codebook's unweighted valid denominator; analysis charts use the supplied weights and retain nonresponse in categorical denominators. See `issp_published_checks.csv`.

## Estimation and coverage

Adults aged 18+; supplied WEIGHT; age groups 18–34, 35–54 and 55+. All released Ukrainian respondents have eligible ages. Numeric means exclude nonnumeric answers. Categorical shares retain all adults, including don't-know and missing responses. Intervals use approximate weighted respondent linearization because verified cluster/stratum identifiers are not supplied.

The 2019 national technical report identifies occupied Crimea and Donetsk/Luhansk areas as excluded, and its README flags methodological deviations from ISSP sampling standards. Weighting adjusts for sex and age. Common-geography checks exclude region codes 1, 7 and 13 in both inequality waves (Crimea/Sevastopol, Donetsk, Luhansk). They reproduce the broad redistribution and service-access patterns. All estimates also have unweighted checks.

Correlations are weighted Pearson correlations among pairwise-valid answers, aligned so higher means more agreement, importance or perceived fairness. Joint endorsement means either of the two strongest responses to both named propositions, divided by all eligible adults. These are specific pair comparisons, not a broad latent-ideology score.

## Inventory

| Question | Years | Original fields | HTML trend |
|---|---|---|---|
'''
    for r in inv.itertuples():
        fields='; '.join(f'{x.year}: {x.source_field}' for x in cw[cw.item.eq(r.item)].itertuples())
        text+=f'| {r.question} | {r.years} | {fields} | {"Yes" if r.html_eligible else "No: one observation"} |\n'
    text+='''
## Reproduction and provenance

Download the named releases through GESIS into `data/raw/issp`. `acquire_issp_sources.py` retrieves public documentation and inventories downloaded originals. Run `issp_analysis.py`, `issp_documentation.py`, then the appendix, inventory, trend and note stages in `run.py`. The full run also regenerates all earlier surveys. `issp.json` and `issp_acquisition.json` record versions, source URLs and file hashes; `issp_question_crosswalk.csv` records fields, scale labels, missingness and comparability. `issp_variable_catalogue.csv` preserves inclusion/exclusion decisions for every field. Export packages contain code, documentation and aggregates, not licensed respondent records.
'''
    (ROOT/'output/issp_variable_audit.md').write_text(text,encoding='utf8')
    path=TABLES/'issp_validation.json';status=json.loads(path.read_text())
    status['published_anchor_checks']=len(rows)
    status['checks'].append('Three published codebook tables: all 15 substantive counts and rounded percentages reproduced')
    path.write_text(json.dumps(status,indent=2),encoding='utf8')
    print('ISSP: 15 published response-count/percentage anchors passed; audit written')

if __name__=='__main__':main()
