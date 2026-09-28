"""Check manuscript traceability and basic delivery constraints after rendering."""
import json,hashlib
import numpy as np
import pandas as pd
from pypdf import PdfReader
from analyze import ROOT

def main():
    t=ROOT/'output/tables'
    coverage=json.loads((t/'coverage_status.json').read_text())
    full=all(coverage.values())
    stem='ukraine_market_attitudes' if full else 'ukraine_market_attitudes_interim'
    pdf=ROOT/'output/pdf'/f'{stem}.pdf'
    reader=PdfReader(pdf)
    # User requested a comprehensive additional appendix after the original note.
    appendix_start=next(i for i,p in enumerate(reader.pages) if 'Appendix: latest affirmative-response shares' in p.extract_text())
    analysis_start=next(i for i,p in enumerate(reader.pages) if 'Attitudes moved differently across dimensions' in p.extract_text())
    assert 5<=appendix_start-analysis_start<=19, 'Core note plus requested principles/coherence, ESS and ISSP extensions'
    assert 'Questions, surveys and available years' in reader.pages[0].extract_text()
    inventory_status=json.loads((t/'question_inventory_validation.json').read_text())
    assert inventory_status['status']=='passed'
    assert json.loads((t/'ess_validation.json').read_text())['status']=='passed'
    assert json.loads((t/'issp_validation.json').read_text())['status']=='passed'
    inventory=pd.read_csv(t/'question_year_inventory.csv')
    latest_items=pd.read_csv(t/'latest_positive_shares.csv')
    money=pd.read_csv(t/'issp_monetary_audit.csv')
    expected=set(zip(latest_items.survey,latest_items.item))|{('ISSP',i) for i in money.item.unique()}
    assert set(zip(inventory.survey,inventory.item))==expected
    text='\n'.join(p.extract_text() for p in reader.pages)
    assert not '\ufffd' in text, 'Unicode replacement character in PDF'
    if not full:assert 'INTERIM' in text and 'Incomplete study' in text
    markdown=(ROOT/'output'/f'{stem}.md').read_text(encoding='utf8')
    assert 'values_full_distributions' not in markdown and 'lits_all_responses' not in markdown
    assert 'national_index_trends' in markdown
    coherence_check=json.loads((t/'coherence_validation.json').read_text())
    assert coherence_check['status']=='passed'
    for name in ['market_principle_ranking','attitude_correlation_matrices','Methods appendix: attitude coherence']:
        assert name in markdown
    assert json.loads((t/'index_validation.json').read_text())['status']=='passed'
    pew_check=json.loads((t/'pew_validation.json').read_text())
    assert pew_check['status']=='passed'
    monitoring_check=json.loads((t/'monitoring_analysis_validation.json').read_text())
    extended_check=json.loads((t/'extended_validation.json').read_text())
    assert extended_check['status']=='passed'
    latest=pd.read_csv(t/'latest_positive_shares.csv')
    assert len(latest)==extended_check['latest_rows']
    for r in latest.itertuples():
        assert r.question in markdown and f'{r.estimate:.1f}%' in markdown
    assert monitoring_check['status']=='passed'
    assert json.loads((t/'monitoring_validation.json').read_text())['status']=='passed'
    assert 'monitoring_business_privatisation' in markdown and '2021–2025' in markdown
    m=pd.read_csv(t/'monitoring_estimates.csv')
    mt=pd.read_csv(t/'monitoring_analysis_trace.csv')
    raw=pd.read_csv(t/'monitoring_published_results.csv')
    assert set(mt.source_item)==set(raw.item), 'All acquired question series enter the analysis'
    joined=mt.merge(raw,on=['year','response'],suffixes=('_trace','_raw'))
    joined=joined[joined.source_item.eq(joined.item_raw)]
    assert len(joined)==len(mt) and np.allclose(joined.percent_trace,joined.percent_raw)
    checks=mt.groupby(['item','year']).contribution.sum()
    actual=m.set_index(['item','year']).estimate
    assert np.allclose(actual,checks.reindex(actual.index))
    assert m[['ci_low','ci_high']].isna().all().all()
    definitions=pd.read_csv(ROOT/'docs/index_definitions.csv')
    sample=pd.read_csv(t/'sample_audit.csv')
    assert set(zip(definitions.survey,definitions.year))==set(zip(sample.survey,sample.year))
    for line in markdown.splitlines():
        if line.startswith('|'):
            assert line.endswith('|'), 'Broken Markdown table row'
    trace=pd.read_csv(t/'note_number_trace.csv')
    tables={n:pd.read_csv(t/n) for n in trace.table.unique()}
    for _,r in trace.iterrows():
        source=tables[r.table]
        for key in ['survey','year','item','age_group','territory','weighted','response','denominator','omitted','battery']:
            if key in source and key in r and pd.notna(r[key]):
                target=r[key]
                # ESS adds text category labels to a ledger that also contains
                # numeric LiTS response codes. Match the source column's dtype.
                if pd.api.types.is_numeric_dtype(source[key]) and not pd.api.types.is_bool_dtype(source[key]):
                    target=pd.to_numeric(target,errors='raise')
                source=source[source[key].eq(target)]
        assert len(source)==1,(r.to_dict(),len(source))
        assert np.isclose(float(source.iloc[0][r.metric]),r.value,rtol=1e-12,atol=1e-12)
    crosswalk=pd.read_csv(ROOT/'docs/question_crosswalk.csv')
    completed=crosswalk[crosswalk.comparability_status.str.startswith('verified') | crosswalk.survey.eq('LiTS')]
    if full:
        assert len(completed)==31 and len(crosswalk)==31, 'Every question-wave requires documented comparability'
        assert 'Incomplete study' not in text and 'WVS pending' not in text
    review_file=ROOT/'docs/visual_review.json'
    review=json.loads(review_file.read_text()) if review_file.exists() else {}
    reviewed=review.get('pdf_sha256')==hashlib.sha256(pdf.read_bytes()).hexdigest()
    result={'study_complete':full,'missing_programmes':[k for k,v in coverage.items() if not v],
            'pdf_pages':len(reader.pages),'main_note_pages':appendix_start-analysis_start,
            'opening_inventory_pages':analysis_start,'question_inventory':inventory_status,
            'attitude_coherence':coherence_check,
            'latest_affirmative_appendix':extended_check,'trace_rows_checked':len(trace),
            'verified_question_wave_rows':len(completed),'required_question_wave_rows':len(crosswalk),
            'numerical_trace_check':'passed','index_checks':'passed','index_survey_waves_checked':len(definitions),
            'supplementary_pew':{'evidence':'published aggregates','national_waves':pew_check['national_waves'],
                'published_age_groups':pew_check['published_age_groups'],'microdata_acquired':False},
            'supplementary_monitoring':monitoring_check,
            'supplementary_ess':json.loads((t/'ess_validation.json').read_text()),
            'supplementary_issp':json.loads((t/'issp_validation.json').read_text()),
            'visual_review':review.get('result') if reviewed else 'This exact PDF build has not yet been visually reviewed.',
            'note':str(pdf.relative_to(ROOT))}
    (t/'delivery_status.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
