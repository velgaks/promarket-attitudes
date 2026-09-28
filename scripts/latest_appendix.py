"""Unify latest question-specific affirmative shares; validate full traceability."""
import json
import numpy as np
import pandas as pd
from analyze import ROOT,TABLES

def main():
    micro=pd.read_csv(TABLES/'extended_microdata_shares.csv')
    pub=pd.read_csv(TABLES/'extended_published_shares.csv')
    mon=pd.read_csv(TABLES/'monitoring_estimates.csv')
    mon=mon[~mon.item.isin(['privatisation_support_index','ownership_policy_any_privatisation'])].copy()
    defs=pd.read_csv(ROOT/'docs/monitoring_indicator_definitions.csv').set_index('item')
    mon['question']=mon.item.map(defs.label)+'?'
    mon['positive_definition']=mon.item.map(defs.formula).str.replace(r'1 \* [^:]+:', '',regex=True).str.replace('_',' ')
    mon['kind']='Policy';mon['source_table']='monitoring_estimates.csv'
    # Readers see natural-language categories; exact original formula stays in definitions.
    mon['positive_definition']=mon.positive_definition.str.replace(' + ',' / ',regex=False)
    for sector,label in [('small','small enterprises'),('large','large enterprises'),('land','land')]:
        for prefix,question,rule in [
            ('privatise_','Do you favour privatisation of '+label+'?','Positive'),
            ('retrospective_','Was privatisation of '+label+' worth doing?','Yes / rather yes'),
            ('existing_private_','Do you favour existing private ownership of '+label+'?','Positive / rather positive'),
            ('renationalise_','Do you oppose returning privately owned '+label+' to the state?','No / rather no to renationalisation')]:
            mask=mon.item.eq(prefix+sector);mon.loc[mask,'question']=question;mon.loc[mask,'positive_definition']=rule
    pew=pd.read_csv(TABLES/'pew_published_results.csv');pew=pew[pew.age_group.eq('All')].copy()
    pew['question']='Do you approve of the move from a state-controlled to a market economy?'
    pew['positive_definition']='Strongly / somewhat approve';pew['kind']='Policy'
    pew['source_table']='pew_published_results.csv'
    micro['source_table']='extended_microdata_shares.csv';pub['source_table']='extended_published_shares.csv'
    ess=pd.read_csv(TABLES/'ess_affirmative_shares.csv')
    ess['source_table']='ess_affirmative_shares.csv'
    issp=pd.read_csv(TABLES/'issp_affirmative_shares.csv')
    issp['source_table']='issp_affirmative_shares.csv'
    combined=pd.concat([micro,pub,mon,pew,ess,issp],ignore_index=True)
    assert not combined.duplicated(['survey','item','year']).any()
    assert combined.estimate.between(0,100).all()
    latest=combined.sort_values('year').groupby(['survey','item'],sort=False).tail(1).copy()
    # Stable survey and substantive ordering; preserve all named policy alternatives.
    surveyorder={x:i for i,x in enumerate(['WVS','EVS','LiTS','Pew','Monitoring','ESS','ISSP'])}
    latest['survey_order']=latest.survey.map(surveyorder)
    latest=latest.sort_values(['survey_order','kind','item']).drop(columns='survey_order')
    latest['latest_scope']='Latest verified Ukrainian observation for this question in audited sources'
    latest.to_csv(TABLES/'latest_positive_shares.csv',index=False,encoding='utf-8-sig')
    # Compact copy for easy external reuse; the detailed table retains design/denominator metadata.
    latest[['question','survey','year','estimate','positive_definition','kind']].rename(columns={'estimate':'positive_pct'}).to_csv(TABLES/'latest_positive_shares_compact.csv',index=False,encoding='utf-8-sig')
    cell=pd.read_csv(TABLES/'extended_published_trace.csv')
    sums=cell.assign(contribution=cell.percent*cell.coefficient).groupby(['survey','item','year']).contribution.sum()
    p=pub.set_index(['survey','item','year']).estimate
    assert np.allclose(p,sums.reindex(p.index))
    # Selected independent manual reads of original PDF cells check row alignment,
    # net/category choice and country selection as well as the arithmetic above.
    anchors=[('Pew','free_market_better',2015,47),('Pew','government_care_poor',2015,92),
        ('Pew','trade_wages',2014,50),('Pew','trade_jobs',2014,61),
        ('Pew','low_tax_growth',2014,14),('Pew','high_tax_redistribution',2014,48),
        ('Monitoring','start_business',2020,37.1),('Monitoring','trust_tax_authority',2021,20.7),
        ('Monitoring','ownership_private',2015,11.3),('Monitoring','market_relations_natural',2021,23.3)]
    for survey,item,year,value in anchors:assert np.isclose(p.loc[(survey,item,year)],value),(survey,item,year)
    assert pub[['ci_low','ci_high']].isna().all().all()
    assert (micro.ci_low<=micro.estimate).all() and (micro.ci_high>=micro.estimate).all()
    assert micro.n_valid.le(micro.n_domain).all()
    avail=pd.read_csv(ROOT/'docs/extended_question_availability.csv')
    assert set(map(tuple,avail[avail.n_valid.gt(0)][['survey','item','year']].values))==set(map(tuple,micro[['survey','item','year']].values))
    # The new proportional measure must reproduce existing means after the binary LiTS coding.
    old=pd.read_csv(TABLES/'estimates.csv')
    old=old[old.survey.eq('LiTS')&old.item.eq('market')&old.age_group.eq('All')&old.weighted&old.territory.eq('survey_coverage')]
    new=micro[micro.survey.eq('LiTS')&micro.item.eq('market')]
    assert np.allclose(old.sort_values('year').estimate*100,new.sort_values('year').estimate)
    status=dict(status='passed',latest_rows=len(latest),latest_rows_by_survey=latest.groupby('survey').size().to_dict(),
        microdata_question_years=len(micro)+len(ess)+len(issp),ess_question_years=len(ess),issp_question_years=len(issp),additional_published_indicator_years=len(pub),
        published_source_cells=len(cell),ci='Microdata: 95% intervals; ESS 2022/2024 use strata/PSUs, others approximate as documented. Published aggregates: unavailable.',
        scope='See output/variable_audit.md; no claim of an exhaustive search of all historical Pew releases or unpublished Monitoring items.')
    (TABLES/'extended_validation.json').write_text(json.dumps(status,indent=2),encoding='utf8')
    print(json.dumps(status,indent=2))

if __name__=='__main__':main()
