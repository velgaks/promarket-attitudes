"""Validate estimands against independent identities and published EBRD results."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pyreadstat
from analyze import ROOT, estimate, load_lits, AGES

T = ROOT / 'output/tables'

def main():
    # Equal-weight, independent-observation limit equals the standard mean SE.
    sample = pd.DataFrame({'weight': [1.] * 5, 'psu': range(5), 'variance_method': 'test'})
    values = pd.Series([0., 1., 1., 0., 1.])
    result = estimate(sample, values)
    assert np.isclose(result['estimate'], values.mean())
    assert np.isclose(result['se'], values.std(ddof=1) / np.sqrt(len(values)))
    # A rescaling of population weights cannot change either estimate or SE.
    frames, _ = load_lits()
    for frame in frames:
        y = frame.market.eq(1).astype(float).where(frame.market.notna())
        a = estimate(frame, y)
        scaled = frame.copy(); scaled['weight'] *= 100
        b = estimate(scaled, y)
        assert np.isclose(a['estimate'], b['estimate']) and np.isclose(a['se'], b['se'])
    # Real-data respondent-age check: attitudes belong to the selected adult,
    # not necessarily the household head who answered expenditure questions.
    d, _ = pyreadstat.read_dta(str(ROOT/'data/raw/LITS-2006-data.dta'),
        usecols=['countryname','ageB','table2_1'] + [f'age{i}' for i in range(1,13)])
    d = d[d.countryname.eq('ukraine')]
    matched = d.apply(lambda r: r.get(f'age{int(r.table2_1)}') if r.table2_1 > 0 else np.nan, axis=1)
    assert matched.notna().sum() == 999 and matched[matched.notna()].eq(d.loc[matched.notna(),'ageB']).all()
    # The source's derived ageB is retained for the one roster-unverifiable case.
    z, _ = pyreadstat.read_dta(str(ROOT/'data/raw/lits_iii.dta'),usecols=['country','STIME'])
    dates = z.loc[z.country.eq('Ukraine'),'STIME'].astype(str)
    assert dates.str.startswith('2016').all()
    # Explicitly save regional evidence; never silently infer a numeric mapping.
    harmonised=pd.read_csv(ROOT/'data/processed/ukraine_harmonised.csv')
    regions = harmonised.groupby(['survey','year','region']).agg(n=('weight','size'),weight_sum=('weight','sum')).reset_index()
    regions.to_csv(T/'region_audit.csv',index=False)
    # Published 2016 Ukraine profile reports rounded valid-answer shares.
    dist = pd.read_csv(T/'distributions.csv')
    checks = []
    for response, published in [(1,37),(3,27)]:
        row = dist[(dist.survey=='LiTS')&(dist.year==2016)&(dist.age_group=='All')&(dist.territory=='survey_coverage')&(dist.denominator=='valid')&(dist.response==response)].iloc[0]
        checks.append(dict(survey='LiTS',year=2016,response=response,denominator='valid responses 1,2,3',
            generated_pct=row.estimate*100,published_rounded_pct=published,
            matches_rounded=int(round(row.estimate*100))==published,
            source='https://litsonline-ebrd.com/countries/ukraine/index.htm'))
    assert all(c['matches_rounded'] for c in checks)
    est = pd.read_csv(T/'estimates.csv')
    if harmonised.survey.eq('WVS').any():
        # Verify an independently printed mean, then audit published grouped
        # percentages without hiding minor mismatches in this source release.
        source='https://ucep.org.ua/wp-content/uploads/2020/11/WVS_UA_2020_report_ENG_WEB.pdf'
        mean=est[(est.survey=='WVS')&(est.year==2020)&(est.item=='income_incentives')&est.weighted&(est.age_group=='All')&(est.territory=='survey_coverage')].iloc[0].estimate
        assert round(mean,2)==6.16
        checks.append(dict(survey='WVS',year=2020,item='income_incentives',denominator='valid 1-10',generated_value=mean,published_value=6.16,unit='scale points',matches_rounded=True,source=source+'#page=28'))
        for item,low,high,published,precision in [('income_incentives',7,10,47,0),('private_ownership',7,10,21,0),('private_ownership',1,4,42,0),('individual_responsibility',7,10,22.4,1),('individual_responsibility',1,4,49.4,1)]:
            a=dist[(dist.survey=='WVS')&(dist.year==2020)&(dist.item==item)&(dist.age_group=='All')&(dist.territory=='survey_coverage')&(dist.denominator=='valid')&dist.response.between(low,high)]
            calculated=a.estimate.sum()*100
            checks.append(dict(survey='WVS',year=2020,item=item,response=f'{low}-{high} recoded',denominator='valid 1-10',generated_pct=calculated,published_rounded_pct=published,matches_rounded=round(calculated,precision)==published,source=source+'#page=27',note='Grouped thresholds reproduce report only; no general pro-market classification. Small responsibility discrepancies retained; cause unresolved.'))
        # Catch the dangerous Crimea translation alias and 1996 ISO mislabel.
        expected_removed={1996:550,2011:309,2020:87}
        for year,n in expected_removed.items():
            a=harmonised[harmonised.survey.eq('WVS')&harmonised.year.eq(year)]
            assert a.common_territory.eq(0).sum()==n
            assert not a.loc[a.common_territory.eq(1),'region'].str.contains('Crimea|Krym|Sevast|Donetsk|Luhansk',case=False).any()
    pd.DataFrame(checks).to_csv(T/'published_crosschecks.csv',index=False)
    keys=['survey','year','item','age_group','territory']
    comparison=est[est.weighted].merge(est[~est.weighted],on=keys,suffixes=('_weighted','_unweighted'))
    comparison['difference']=np.where(comparison.item.eq('market'),100,1)*(comparison.estimate_weighted-comparison.estimate_unweighted)
    comparison['difference_unit']=np.where(comparison.item.eq('market'),'percentage points','scale points')
    comparison.to_csv(T/'weight_sensitivity.csv',index=False)
    weighted=est[est.weighted].copy()
    weighted[weighted.age_group.eq('All')&weighted.territory.eq('survey_coverage')].merge(
        pd.read_csv(T/'missingness.csv'),on=['survey','year','item']).to_csv(T/'national_results.csv',index=False)
    weighted[~weighted.age_group.eq('All')&weighted.territory.eq('survey_coverage')].to_csv(T/'age_group_results.csv',index=False)
    sensitivity=weighted[weighted.territory.eq('survey_coverage')].merge(
        weighted[weighted.territory.eq('exclude_crimea_donetsk_luhansk')],
        on=['survey','year','item','age_group'],suffixes=('_survey','_restricted'))
    sensitivity.to_csv(T/'territory_sensitivity.csv',index=False)
    diagnostics=[]
    for (survey,year),f in harmonised.groupby(['survey','year']):
        w=f.weight
        diagnostics.append(dict(survey=survey,year=year,n=len(f),weight_min=w.min(),weight_median=w.median(),
                                weight_max=w.max(),weight_sum=w.sum(),kish_n=w.sum()**2/(w*w).sum(),
                                age_min=f.age.min(),age_max=f.age.max()))
    pd.DataFrame(diagnostics).to_csv(T/'weight_diagnostics.csv',index=False)
    by_age=[]
    for (survey,year),frame in harmonised.groupby(['survey','year']):
        for group in ['All']+AGES:
            dom=pd.Series(True,index=frame.index) if group=='All' else frame.age_group.eq(group)
            for item in (['market','pro_market_index'] if survey=='LiTS' else ['private_ownership','competition','individual_responsibility','income_incentives','pro_market_index']):
                r=estimate(frame,frame[item].isna().astype(float),dom,bounds=(0,1))
                by_age.append(dict(survey=survey,year=int(year),item=item,age_group=group,**r))
    pd.DataFrame(by_age).to_csv(T/'missingness_by_age.csv',index=False)
    coverage=json.loads((T/'coverage_status.json').read_text())
    audit={'status':'analytical checks passed for acquired, verified data','coverage':coverage,'published_rounding_checks':len(checks),
           'age_2006_matched_roster':999,'age_2006_roster_unverifiable_retained':1,
           'lits_2016_start_time_year_prefix':2016,
           'published_crosscheck_mismatches':sum(not c['matches_rounded'] for c in checks),
           'unresolved':['LiTS 2006 and WVS 2006 oblast mapping',
                         'WVS 2020 responsibility shares differ from report by about 0.1 percentage point; unresolved source-release/denominator detail',
                         'WVS/EVS sampling clusters and country-language translation equivalence not fully verified',
                         'stratum identifiers unavailable; approximate PSU-based intervals',
                         'cross-wave PSU linkage unavailable; no formal change tests']}
    (T/'validation.json').write_text(json.dumps(audit,indent=2),encoding='utf8')
    print(json.dumps(audit,indent=2))

if __name__=='__main__':main()
