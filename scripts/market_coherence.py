"""Within-wave market-attitude correlations, coherence and principle rankings.

Never correlate national averages or mutually exclusive response dummies.
All directional scales are aligned before measuring associations.
"""
import json
import numpy as np
import pandas as pd
from analyze import ROOT, RAW, TABLES, COMPONENTS, LITS, read_selected, estimate
from extended_attitudes import check_original

BOOTSTRAPS = 2000
SEED = 20260925
COMMON = ['private_ownership', 'competition', 'income_incentives']
LABELS = {
    'private_ownership': 'Private ownership', 'competition': 'Benefits of competition',
    'individual_responsibility': 'Individual responsibility', 'income_incentives': 'Income incentives',
    'market_choice': 'Market economy preferable', 'less_redistribution': 'Oppose reducing the income gap',
}


def covariance(x, w):
    centered = x - np.average(x, axis=0, weights=w)
    return (centered * w[:, None]).T @ centered / w.sum()


def correlation(cov):
    sd = np.sqrt(np.diagonal(cov, axis1=-2, axis2=-1))
    return cov / (sd[..., :, None] * sd[..., None, :])


def weighted_ranks(x, w):
    # Midpoints of the weighted empirical CDF, respecting tied responses.
    values, inverse = np.unique(x, return_inverse=True)
    mass = np.bincount(inverse, weights=w, minlength=len(values))
    return (np.cumsum(mass) - mass / 2)[inverse] / mass.sum()


def metrics(cov):
    k = cov.shape[-1]
    corr = correlation(cov)
    upper = np.triu_indices(k, 1)
    mean_r = corr[..., upper[0], upper[1]].mean(axis=-1)
    eig = np.linalg.eigvalsh(corr)
    return dict(mean_pairwise_correlation=mean_r,
                weighted_alpha=k/(k-1)*(1-np.trace(cov, axis1=-2, axis2=-1)/cov.sum(axis=(-2,-1))),
                standardized_alpha=k*mean_r/(1+(k-1)*mean_r),
                first_pc_variance_pct=100*eig[..., -1]/k)


def bootstrap_covariances(frame, columns, rng):
    valid = frame[columns].notna().all(axis=1).to_numpy()
    x = frame[columns].fillna(0).to_numpy(float)
    w = frame.weight.to_numpy(float) * valid
    # Keep every eligible PSU, including PSUs with no complete-case answers.
    codes, psus = pd.factorize(frame.psu, sort=True)
    g, k = len(psus), len(columns)
    features = np.column_stack([w, w[:, None]*x, (w[:, None, None]*x[:, :, None]*x[:, None, :]).reshape(len(x), -1)])
    sums = np.zeros((g, features.shape[1]))
    np.add.at(sums, codes, features)
    counts = rng.multinomial(g, np.full(g, 1/g), size=BOOTSTRAPS)
    totals = counts @ sums
    mu = totals[:, 1:1+k] / totals[:, :1]
    cov = totals[:, 1+k:].reshape(-1,k,k)/totals[:, :1, None] - mu[:, :, None]*mu[:, None, :]
    assert np.isfinite(cov).all()
    return cov, g


def analyze_battery(frame, survey, year, battery, columns, rng):
    good = frame[columns].notna().all(axis=1)
    complete = frame.loc[good]
    x, w = complete[columns].to_numpy(float), complete.weight.to_numpy(float)
    cov = covariance(x, w)
    corr = correlation(cov)
    boot_cov, n_psu = bootstrap_covariances(frame, columns, rng)
    boot_corr = correlation(boot_cov)
    corr_unweighted = np.corrcoef(x, rowvar=False)
    ranks = np.column_stack([weighted_ranks(x[:, j], w) for j in range(len(columns))])
    rank_corr = correlation(covariance(ranks, w))
    key = dict(survey=survey, year=year, battery=battery)
    pairs = []
    for j, a in enumerate(columns):
        for k, b in enumerate(columns):
            if j >= k:
                continue
            pair = frame[[a,b,'weight']].dropna()
            pcorr = correlation(covariance(pair[[a,b]].to_numpy(float), pair.weight.to_numpy(float)))[0,1]
            lo, hi = np.quantile(boot_corr[:,j,k], [.025,.975])
            pairs.append(dict(**key, item=f'{a}__{b}', item_1=a, item_2=b,
                              estimate=corr[j,k], ci_low=lo, ci_high=hi,
                              spearman_weighted=rank_corr[j,k], unweighted=corr_unweighted[j,k],
                              pairwise_complete=pcorr, n_pairwise=len(pair), n_complete=len(complete),
                              n_psu=n_psu, method='Weighted Pearson; complete cases for named battery',
                              uncertainty=f'{BOOTSTRAPS} PSU bootstrap replicates; approximate'))
    summary = dict(**key, item=battery, n_items=len(columns), n_eligible=len(frame),
                   n_complete=len(complete), n_psu=n_psu,
                   complete_weighted_pct=100*w.sum()/frame.weight.sum(),
                   kish_n=w.sum()**2/(w*w).sum(), **metrics(cov))
    for name, samples in metrics(boot_cov).items():
        summary[name+'_ci_low'], summary[name+'_ci_high'] = np.quantile(samples, [.025,.975])
    summary['mean_correlation_unweighted'] = corr_unweighted[np.triu_indices(len(columns),1)].mean()
    summary['mean_correlation_spearman'] = rank_corr[np.triu_indices(len(columns),1)].mean()
    # Signed loadings show whether the strongest empirical axis follows the
    # market-aligned direction for every item. No arbitrary pass/fail threshold.
    eigenvalues, vectors = np.linalg.eigh(corr)
    loading = vectors[:,-1] * np.sqrt(eigenvalues[-1])
    if loading.sum() < 0:
        loading = -loading
    loads = [dict(**key, item=item, loading=float(value)) for item,value in zip(columns,loading)]
    assert np.allclose(corr,corr.T) and np.allclose(np.diag(corr),1)
    assert np.linalg.eigvalsh(corr).min() >= -1e-10
    assert np.allclose(correlation(covariance(x, w*7)),corr)
    return pairs, summary, loads


def lits_frames():
    frames=[];definitions=[]
    for year,filename,country,age,market,weight,psu,region,respondent in LITS:
        check_original(filename)
        gap={2006:'q301_10',2010:'q301h',2016:'q401h'}[year]
        scales={} if year==2006 else dict(zip(COMMON,
            ['q316b','q316c','q316a'] if year==2010 else ['q417b','q417c','q417a']))
        d, meta=read_selected(RAW/filename,[country,age,weight,psu,respondent,market,gap]+list(scales.values()))
        d=d[d[country].astype(str).str.lower().eq('ukraine') & d[age].ge(18) &
            d[weight].gt(0) & np.isfinite(d[weight])].copy()
        assert d[respondent].is_unique and d[psu].notna().all()
        f=pd.DataFrame(index=d.index)
        f['survey']='LiTS';f['year']=year;f['weight']=d[weight];f['psu']=d[psu].astype(str)
        f['variance_method']='PSU linearization; no explicit strata; approximate'
        f['market_choice']=d[market].eq(1).astype(float).where(d[market].isin([1,2,3]))
        f['less_redistribution']=(6-d[gap]).where(d[gap].isin(range(1,6)))
        for item,field in scales.items():
            raw=d[field].where(d[field].isin(range(1,11)))
            f[item]=raw if item=='income_incentives' else 11-raw
        specs=[('market_choice',market,'1 if market preferable; 0 if planned/indifferent; other missing'),
               ('less_redistribution',gap,'6 - raw; valid 1..5; high=oppose reducing rich-poor gap')]
        specs += [(item,field,'raw' if item=='income_incentives' else '11 - raw') for item,field in scales.items()]
        for item,field,coding in specs:
            definitions.append(dict(survey='LiTS',year=year,item=item,source_field=field,coding=coding,
                source_label=meta.column_names_to_labels.get(field,''),
                source_value_labels=json.dumps(meta.variable_value_labels.get(field,{}),ensure_ascii=False),
                source_file=filename,weight=weight,psu=psu))
        frames.append(f)
    pd.DataFrame(definitions).to_csv(ROOT/'docs/coherence_question_definitions.csv',index=False,encoding='utf-8-sig')
    return frames


def main():
    rng=np.random.default_rng(SEED)
    h=pd.read_csv(ROOT/'data/processed/ukraine_harmonised.csv')
    pairs=[];summaries=[];loads=[];conditional=[]
    def add(f,survey,year,battery,columns):
        a,b,c=analyze_battery(f,survey,int(year),battery,columns,rng)
        pairs.extend(a);summaries.append(b);loads.extend(c)
    for (survey,year),f in h[h.survey.isin(['WVS','EVS'])].groupby(['survey','year']):
        add(f,survey,year,'core',COMPONENTS)
        # Identical content across all three microdata programmes.
        add(f,survey,year,'common_three',COMMON)
    for f in lits_frames():
        year=int(f.year.iloc[0])
        add(f,'LiTS',year,'market_redistribution',['market_choice','less_redistribution'])
        if year==2006:
            continue
        add(f,'LiTS',year,'core',COMMON)
        add(f,'LiTS',year,'extended',COMMON+['market_choice','less_redistribution'])
        for item in COMMON+['reduce_gap']:
            x=(f.less_redistribution.le(2).astype(float).where(f.less_redistribution.notna())
               if item=='reduce_gap' else f[item].ge(6).astype(float).where(f[item].notna()))
            result=estimate(f,x*100,domain=f.market_choice.eq(1),bounds=(0,100))
            conditional.append(dict(survey='LiTS',year=year,item=item,condition='market economy preferable',**result))
    pairs=pd.DataFrame(pairs);summary=pd.DataFrame(summaries)
    pairs.to_csv(TABLES/'attitude_correlations.csv',index=False)
    summary.to_csv(TABLES/'ideological_coherence.csv',index=False)
    pd.DataFrame(loads).to_csv(TABLES/'coherence_pc_loadings.csv',index=False)
    pd.DataFrame(conditional).to_csv(TABLES/'market_supporter_attitudes.csv',index=False)
    # Latest-wave ranking uses identical ten-point direction/thresholds and keeps
    # programmes separate; the original shares and their design intervals remain.
    ext=pd.read_csv(TABLES/'extended_microdata_shares.csv')
    means=pd.read_csv(TABLES/'extended_mean_estimates.csv')
    mapping={'E036':'private_ownership','E039':'competition','E037':'individual_responsibility','E035':'income_incentives'}
    ranks=[]
    for survey,year in [('WVS',2020),('EVS',2020),('LiTS',2016)]:
        items=COMPONENTS if survey!='LiTS' else COMMON
        z=ext[ext.survey.eq(survey)&ext.year.eq(year)].copy()
        z['analysis_item']=z.item.map(mapping) if survey!='LiTS' else z.item
        z=z[z.analysis_item.isin(items)].sort_values('estimate',ascending=False)
        assert len(z)==len(items)
        z['rank']=range(1,len(z)+1)
        m=means[means.survey.eq(survey)&means.year.eq(year)&means.age_group.eq('All')].copy()
        m['analysis_item']=m.item.map(mapping) if survey!='LiTS' else m.item
        m=m[m.analysis_item.isin(items)].rename(columns={'estimate':'mean_estimate','ci_low':'mean_ci_low','ci_high':'mean_ci_high'})
        z=z.merge(m[['analysis_item','mean_estimate','mean_ci_low','mean_ci_high']],on='analysis_item',validate='one_to_one')
        assert len(z)==len(items) and z.mean_estimate.notna().all()
        z['mean_rank']=z.mean_estimate.rank(ascending=False,method='min').astype(int)
        ranks.append(z[['survey','year','analysis_item','rank','estimate','ci_low','ci_high','n_valid','positive_definition',
                        'mean_estimate','mean_ci_low','mean_ci_high','mean_rank']])
    ranking=pd.concat(ranks,ignore_index=True).rename(columns={'analysis_item':'item'})
    ranking.to_csv(TABLES/'market_principle_rankings.csv',index=False)
    # Independent reconciliation to the already validated four-item diagnostics.
    old=pd.read_csv(TABLES/'index_item_correlations.csv')
    check=pairs[pairs.battery.eq('core')&pairs.survey.ne('LiTS')].merge(old,on=['survey','year','item_1','item_2'])
    assert len(check)==len(old) and np.allclose(check.estimate,check.weighted_correlation)
    old_diag=pd.read_csv(TABLES/'index_diagnostics.csv')
    check=summary[summary.battery.eq('core')&summary.survey.ne('LiTS')].merge(old_diag,on=['survey','year'],suffixes=('_new','_old'))
    assert np.allclose(check.weighted_alpha_new,check.weighted_alpha_old)
    assert pairs.estimate.between(-1,1).all() and not pairs.duplicated(['survey','year','battery','item']).any()
    assert not summary.duplicated(['survey','year','battery']).any()
    # Weighted covariance also agrees with the library calculation under equal weights.
    toy=np.array([[1,3,2],[3,2,6],[2,1,5],[7,4,9]],float)
    assert np.allclose(correlation(covariance(toy,np.ones(4))),np.corrcoef(toy,rowvar=False))
    status=dict(status='passed',correlation_rows=len(pairs),battery_waves=len(summary),
                bootstrap_replicates=BOOTSTRAPS,seed=SEED,ranked_principles=len(ranking),
                checks=['Existing WVS/EVS correlations and alpha reproduced',
                        'Scale/weight invariance and positive-semidefinite matrices',
                        'Original LiTS codes and weights verified',
                        'Rank, unweighted and pairwise-complete sensitivity exported',
                        'Affirmative-share rankings compared with continuous means'],
                scope='Within each survey and wave; national adult samples; no pooling of years or aggregate correlations')
    (TABLES/'coherence_validation.json').write_text(json.dumps(status,indent=2),encoding='utf8')
    print(summary[summary.battery.eq('core')][['survey','year','n_complete','mean_pairwise_correlation','weighted_alpha','first_pc_variance_pct','mean_correlation_spearman','mean_correlation_unweighted']].to_string(index=False))
    print(pd.DataFrame(conditional).to_string(index=False))
    print(json.dumps(status))


if __name__=='__main__':
    main()
