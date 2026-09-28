"""Audit the descriptive index, item alignment and sensitivity to its definition."""
import json
import numpy as np
import pandas as pd
from analyze import ROOT, COMPONENTS, INDEX, AGES, estimate, add_index

T=ROOT/'output/tables'

def main():
    h=pd.read_csv(ROOT/'data/processed/ukraine_harmonised.csv')
    e=pd.read_csv(T/'estimates.csv')
    # Endpoint anchoring, equal contribution, and no silent partial-item scores.
    synthetic=pd.DataFrame({'survey':['WVS']*4,**{c:[1.,10.,5.5,5.] for c in COMPONENTS}})
    synthetic.loc[3,COMPONENTS[0]]=np.nan
    x=add_index(synthetic)[INDEX]
    assert np.allclose(x.iloc[:3],[0,100,50]) and pd.isna(x.iloc[3])
    diagnostics=[];correlations=[];sensitivity=[];definitions=[]
    for (survey,year),f in h.groupby(['survey','year']):
        primary=e[(e.survey==survey)&(e.year==year)&(e.item==INDEX)&e.weighted&(e.age_group=='All')&(e.territory=='survey_coverage')].iloc[0]
        valid=f[INDEX].notna()
        assert f.loc[valid,INDEX].between(0,100).all()
        if survey=='LiTS':
            # Every domain, both weight options, and all uncertainty quantities
            # must be precisely the existing binary market outcome scaled by 100.
            a=e[(e.survey==survey)&(e.year==year)&(e.item==INDEX)]
            b=e[(e.survey==survey)&(e.year==year)&(e.item=='market')]
            merged=a.merge(b,on=['year','age_group','territory','weighted'],suffixes=('_index','_market'))
            for col in ['estimate','se','ci_low','ci_high']:
                assert np.allclose(merged[col+'_index'],100*merged[col+'_market'])
            definitions.append(dict(survey=survey,year=year,formula='100 * indicator(market preferable)',missing_rule='Require substantive response; planned and indifferent=0, market=100; nonresponse missing',interpretation='Mean equals market-preference percentage, not a multi-item attitude scale'))
            continue
        definitions.append(dict(survey=survey,year=year,formula='100/9 * (mean of four aligned 1-10 responses - 1)',missing_rule='Require valid answers to all four items; no imputation',interpretation='Equal-weight descriptive summary; not a validated latent scale; programme identity retained'))
        a=f.loc[valid];w=a.weight.to_numpy();x=a[COMPONENTS].to_numpy()
        means=np.average(x,axis=0,weights=w)
        # Independent mean-of-components identity on the identical sample.
        assert np.isclose(primary.estimate,(means.mean()-1)*100/9)
        centered=x-means
        cov=(centered*w[:,None]).T@centered/w.sum()
        sd=np.sqrt(np.diag(cov));corr=cov/np.outer(sd,sd)
        alpha=4/3*(1-np.trace(cov)/cov.sum())
        for j,c1 in enumerate(COMPONENTS):
            for k,c2 in enumerate(COMPONENTS):
                if j<k:correlations.append(dict(survey=survey,year=int(year),item_1=c1,item_2=c2,weighted_correlation=corr[j,k],n_complete=len(a)))
        # Different item-valid samples: point-estimate sensitivity, not the primary estimand.
        available=[np.average(f.loc[f[c].notna(),c],weights=f.loc[f[c].notna(),'weight']) for c in COMPONENTS]
        available_index=(np.mean(available)-1)*100/9
        diagnostics.append(dict(survey=survey,year=int(year),item=INDEX,n_eligible=len(f),n_complete=len(a),
            complete_weighted_pct=100*w.sum()/f.weight.sum(),missing_weighted_pct=100*(1-w.sum()/f.weight.sum()),
            weighted_alpha=alpha,mean_pairwise_correlation=corr[np.triu_indices(4,1)].mean(),
            primary_index=primary.estimate,available_item_means_index=available_index,
            available_minus_complete=available_index-primary.estimate))
        for omitted in COMPONENTS:
            retained=[c for c in COMPONENTS if c!=omitted]
            y=f[retained].mean(axis=1,skipna=False).sub(1).mul(100/9).where(valid)
            for group in ['All']+AGES:
                domain=pd.Series(True,index=f.index) if group=='All' else f.age_group.eq(group)
                r=estimate(f,y,domain,bounds=(0,100))
                sensitivity.append(dict(survey=survey,year=int(year),omitted=omitted,age_group=group,territory='survey_coverage',sample='same four-item complete cases',**r))
    pd.DataFrame(diagnostics).to_csv(T/'index_diagnostics.csv',index=False)
    pd.DataFrame(correlations).to_csv(T/'index_item_correlations.csv',index=False)
    pd.DataFrame(sensitivity).to_csv(T/'index_leave_one_out.csv',index=False)
    pd.DataFrame(definitions).to_csv(ROOT/'docs/index_definitions.csv',index=False)
    e[e.item.eq(INDEX)].to_csv(T/'index_results.csv',index=False)
    result={'status':'passed','endpoint_and_complete_case_checks':'passed','weighted_composite_identity':'passed',
            'lits_binary_rescaling_including_intervals':'passed','definition':'Fixed equal weights and fixed 0-100 endpoints; no within-wave standardisation',
            'interpretation':'Descriptive aggregation only. Inspect weighted alpha/correlations; no reliability cutoff or validated common trait is asserted.'}
    (T/'index_validation.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print(pd.DataFrame(diagnostics).to_string(index=False))

if __name__=='__main__':main()
