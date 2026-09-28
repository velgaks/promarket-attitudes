"""Reproducible descriptive estimates and fixed-content summary indices.

Run from any directory: python scripts/analyze.py
Original restricted-redistribution microdata and respondent extracts stay local.
"""
from pathlib import Path
import json
import re
import struct
import numpy as np
import pandas as pd
import pyreadstat
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw'
TABLES = ROOT / 'output/tables'
PROCESSED = ROOT / 'data/processed'
AGES = ['18-34', '35-54', '55+']
DIMENSIONS = {
    'E036': ('private_ownership', True),
    'E039': ('competition', True),
    'E037': ('individual_responsibility', True),
    'E035': ('income_incentives', False),
}
COMPONENTS = [v[0] for v in DIMENSIONS.values()]
INDEX = 'pro_market_index'

def add_index(frame):
    """Fixed-endpoint summaries, never wave-standardized or ordinal LiTS means."""
    frame = frame.copy()
    if frame.survey.iloc[0] == 'LiTS':
        frame[INDEX] = frame.market.eq(1).astype(float).mul(100).where(frame.market.notna())
    else:
        # All four items required: every respondent's index has identical content.
        frame[INDEX] = frame[COMPONENTS].mean(axis=1, skipna=False).sub(1).mul(100/9)
    frame['raw_'+INDEX] = frame[INDEX]
    return frame
LITS = [
    (2006, 'LITS-2006-data.dta', 'countryname', 'ageB', 'q310', 'weight_0', 'tabled', 'region', 'serial'),
    (2010, 'lits2.dta', 'countryname', 'respondentage', 'q310', 'weight', 'psu', 'Region1', 'SerialID'),
    (2016, 'lits_iii.dta', 'country', 'age_pr', 'q411', 'weight_population', 'PSU_number', 'region_name', 'ID'),
]

def readable_sav(path):
    """Work around an invalid MR-set dictionary record in official ZA7503 v3 SAV.

    The original is retained. Only an optional multiple-response-set metadata
    extension is omitted from a temporary copy; variable/value labels and the
    complete case-data byte stream are unchanged. Latin-1 decodes mixed-encoding
    legacy metadata losslessly; all analysis fields are numeric.
    """
    if path.name != 'ZA7503_v3-0-0.sav':
        return path, {'user_missing': True}
    target = ROOT/'tmp/ZA7503_dictionary_clean.sav'
    raw=path.read_bytes();at=raw.find(struct.pack('<iii',7,7,1))
    if at != 5311744 or struct.unpack('<i',raw[at+12:at+16])[0] != 2304:
        raise ValueError('Unexpected ZA7503 dictionary; review parser workaround')
    fixed=raw[:at]+raw[at+2320:]
    if not target.exists() or target.stat().st_size!=len(fixed):
        target.parent.mkdir(exist_ok=True);target.write_bytes(fixed)
    return target, {'encoding':'latin1','user_missing':True}

def read_selected(path, wanted):
    reader = pyreadstat.read_dta if path.suffix.lower() == '.dta' else pyreadstat.read_sav
    actual,kwargs=readable_sav(path) if path.suffix.lower()=='.sav' else (path,{})
    _, meta = reader(str(actual), metadataonly=True,**kwargs)
    lookup = {c.upper(): c for c in meta.column_names}
    columns = [lookup[c.upper()] for c in wanted if c.upper() in lookup]
    data, _ = reader(str(actual), usecols=list(dict.fromkeys(columns)),**kwargs)
    return data, meta

def age_groups(age):
    return pd.cut(age, [17, 34, 54, np.inf], labels=AGES)

def estimate(data, y, domain=None, weighted=True, bounds=None):
    """Ratio estimate and ultimate-cluster linearization.

    Preserve every PSU in the eligible survey sample for domain variance, including
    PSUs with no valid responses in the domain. When PSU identifiers are absent,
    individuals are the variance units; those intervals are explicitly approximate.
    No invented strata or finite-population corrections are used.
    """
    y = pd.Series(y, index=data.index, dtype=float)
    domain = pd.Series(True, index=data.index) if domain is None else domain.fillna(False)
    mask = domain & y.notna()
    weight = data.weight if weighted else pd.Series(1., index=data.index)
    w = weight.where(mask, 0.)
    denominator = w.sum()
    if denominator <= 0:
        return None
    mean = (w * y.fillna(0.)).sum() / denominator
    influence = w * (y.fillna(mean) - mean) / denominator
    totals = influence.groupby(data.psu, dropna=False).sum()
    g = len(totals)
    se = np.sqrt(g / (g - 1) * (totals ** 2).sum()) if g > 1 else np.nan
    critical = student_t.ppf(.975, g - 1) if g > 1 else np.nan
    lo, hi = mean - critical * se, mean + critical * se
    if bounds is not None:
        lo, hi = max(bounds[0], lo), min(bounds[1], hi)
    return dict(estimate=float(mean), se=float(se), ci_low=float(lo), ci_high=float(hi),
                n_valid=int(mask.sum()), n_domain=int(domain.sum()), n_psu=g,
                kish_n=float(denominator**2 / (w**2).sum()),
                weight_sum=float(denominator), weighted=weighted,
                variance_method=str(data.variance_method.iloc[0]))

def load_lits():
    output, audit = [], []
    for year, filename, country, age, item, weight, psu, region, respondent in LITS:
        path = RAW / filename
        if not path.exists():
            continue
        d, meta = read_selected(path, [country, age, item, weight, psu, region, respondent])
        d = d[d[country].astype(str).str.lower().eq('ukraine')].copy()
        n_raw = len(d)
        invalid_age = int((d[age].isna() | (d[age] < 18)).sum())
        invalid_weight = int((d[age].ge(18) & (~np.isfinite(d[weight]) | d[weight].le(0))).sum())
        d = d[d[age].ge(18) & np.isfinite(d[weight]) & d[weight].gt(0)].copy()
        assert d[respondent].is_unique, (year, 'duplicate respondent IDs')
        assert d[psu].notna().all(), (year, 'missing PSU identifier')
        z = pd.DataFrame(dict(survey='LiTS', year=year, respondent_id=d[respondent].astype(str),
                             age=d[age], weight=d[weight], psu=d[psu].astype(str),
                             region=d[region].astype(str), raw_market=d[item]))
        z['market'] = z.raw_market.where(z.raw_market.isin([1, 2, 3]))
        z['age_group'] = age_groups(z.age)
        z['variance_method'] = 'PSU linearization; no explicit strata; approximate'
        # The 2006 regional identifiers have no verified oblast mapping in this release.
        z['common_territory'] = np.nan
        if year >= 2010:
            z['common_territory'] = ~z.region.str.contains('crimea|sevast|donetsk|lugansk|luhansk', case=False, regex=True)
        output.append(z)
        audit.append(dict(survey='LiTS', year=year, file=filename, n_raw=n_raw, excluded_age=invalid_age,
                          excluded_weight=invalid_weight, n_eligible=len(z), weight_variable=weight,
                          age_variable=age, item_variable=item, psu_variable=psu,
                          region_variable=region, territory_available=year>=2010))
    return output, audit

def load_values(survey, path):
    # Never promote a provisional generic mapping into verified results.
    gate = ROOT / 'data/source_manifests/values_verification.json'
    approval = json.loads(gate.read_text()) if gate.exists() else {}
    import hashlib
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    verified = approval.get(survey, {})
    if verified.get('sha256') != digest or not verified.get('crosswalk_verified', False):
        raise RuntimeError(f'{survey}: microdata/questionnaire audit is pending. '
                           'Verify source identity, wave items, scale directions, weights and '
                           'geography before adding its hash to values_verification.json.')
    wanted = ['S001','S002','S002EVS','S002VS','S003','S007','S007_01','S012','S017','S020',
              'X003','X001','X048WVS','X048ISO','X048EVS','X048_EVS','X048','X048B_N2','X048I_N2','S025','S036'] + list(DIMENSIONS)
    d, meta = read_selected(path, wanted)
    d.columns = d.columns.str.upper()
    required = ['S003','S017','S020','X003'] + list(DIMENSIONS)
    missing = set(required) - set(d.columns)
    if missing:
        raise ValueError(f'{survey}: required fields absent: {sorted(missing)}')
    d = d[d.S003.eq(804)].copy()
    expected_study = 2 if survey == 'WVS' else 1
    if 'S001' not in d or not d.S001.eq(expected_study).all():
        raise ValueError(f'{survey}: wrong or mixed survey identity')
    if 'S036' in d and not d.S036.eq(0).all():
        raise ValueError(f'{survey}: archive duplicate flags require review')
    expected_years = [1996, 2006, 2011, 2020] if survey == 'WVS' else [1999, 2008, 2020]
    if set(d.S020.dropna().astype(int).unique()) != set(expected_years):
        raise ValueError(f'{survey}: unexpected/missing Ukrainian years; review the inventory')
    frames, audits = [], []
    for year, a in d.groupby('S020'):
        n_raw = len(a)
        bad_age = int((a.X003.isna() | a.X003.lt(18)).sum())
        bad_weight = int((a.X003.ge(18) & (~np.isfinite(a.S017) | a.S017.le(0))).sum())
        a = a[a.X003.ge(18) & np.isfinite(a.S017) & a.S017.gt(0)].copy()
        id_col = next((x for x in ['S007','S007_01','S012'] if x in a and a[x].is_unique), None)
        if id_col is None:
            raise ValueError(f'{survey} {year}: cannot verify respondent identifier')
        # S025 is NOT assumed to identify sampling clusters. Public trend-file
        # metadata must explicitly establish a PSU field before it is used.
        z = pd.DataFrame(dict(survey=survey, year=int(year), respondent_id=a[id_col].astype(str),
                             age=a.X003, weight=a.S017, psu=a[id_col].astype(str)))
        z['age_group'] = age_groups(z.age)
        z['variance_method'] = 'Weighted respondent linearization; clustering unavailable; approximate'
        z['common_territory'] = np.nan
        region_col = verified.get('regions',{}).get(str(int(year)))
        lookup = {k.upper(): v for k,v in meta.variable_value_labels.items()}
        if region_col:
            z['region_code'] = a[region_col].astype(str)
            labels = lookup.get(region_col,{})
            z['region'] = a[region_col].map(labels)
            if z.region.isna().any() or a[region_col].isin([-1,-2,-3,-4,-5]).any():
                raise ValueError(f'{survey} {year}: incomplete geographic labels')
            z['common_territory'] = ~z.region.str.contains('crimea|krym|sevast|donetsk|lugansk|luhansk',case=False,regex=True)
        else:
            z['region']='not verified'
        for source, (name, reverse) in DIMENSIONS.items():
            raw = a[source]
            z['raw_'+name] = raw
            v = raw.where(raw.between(1, 10))
            if not v.dropna().isin(range(1,11)).all():
                raise ValueError(f'{survey} {year} {source}: non-integer valid response')
            key = f'{int(year)}:{source}'
            rule = verified.get('items', {}).get(key)
            if rule not in ['reverse', 'as_is', 'not_comparable', 'not_asked']:
                raise ValueError(f'{survey} {key}: explicit item verification required')
            z[name] = (11-v if rule == 'reverse' else v) if rule in ['reverse', 'as_is'] else np.nan
        frames.append(z)
        audits.append(dict(survey=survey, year=int(year), file=path.name, n_raw=n_raw,
                           excluded_age=bad_age, excluded_weight=bad_weight, n_eligible=len(z),
                           weight_variable='S017', age_variable='X003', item_variable='E035/E036/E037/E039',
                           psu_variable='unavailable', region_variable=region_col, territory_available=bool(region_col)))
    return frames, audits

def summarize(frames):
    estimates, distributions, missingness = [], [], []
    for d in frames:
        d = d.reset_index(drop=True)
        survey, year = d.survey.iloc[0], int(d.year.iloc[0])
        items = (['market'] if survey == 'LiTS' else COMPONENTS) + [INDEX]
        for item in items:
            raw = d['raw_'+item]
            missingness.append(dict(survey=survey, year=year, item=item, n_eligible=len(d),
                                    n_valid=int(d[item].notna().sum()),
                                    missing_pct=float(np.average(d[item].isna(),weights=d.weight)*100),
                                    missing_raw_codes=json.dumps(raw[d[item].isna()].value_counts(dropna=False).to_dict())))
            if not d[item].notna().any():
                continue
            territories = [('survey_coverage',pd.Series(True,index=d.index))]
            if d.common_territory.notna().all():
                territories.append(('exclude_crimea_donetsk_luhansk',d.common_territory.astype(bool)))
            for territory, territory_mask in territories:
                for group in ['All'] + AGES:
                    domain = territory_mask & (True if group=='All' else d.age_group.eq(group))
                    base = dict(survey=survey,year=year,item=item,age_group=group,territory=territory)
                    if item == 'market':
                        y=d.market.eq(1).astype(float).where(d.market.notna())
                        bounds=(0,1)
                    else:
                        y=d[item];bounds=(0,100) if item==INDEX else (1,10)
                    for weighted in [True,False]:
                        est=estimate(d,y,domain,weighted,bounds)
                        if est:estimates.append(dict(**base,**est))
                    if item==INDEX:
                        continue  # A composite is not a ten-category response item.
                    for response in (range(1,4) if item=='market' else range(1,11)):
                        y=d[item].eq(response).astype(float).where(d[item].notna())
                        est=estimate(d,y,domain,True,(0,1))
                        if est:distributions.append(dict(**base,response=response,denominator='valid',**est))
                    if item=='market':
                        # All-eligible denominator makes the nonresponse shift explicit.
                        for response in range(0,4):
                            y=d[item].isna() if response==0 else d[item].eq(response)
                            est=estimate(d,y.astype(float),domain,True,(0,1))
                            if est:distributions.append(dict(**base,response=response,denominator='all_eligible',**est))
    return pd.DataFrame(estimates),pd.DataFrame(distributions),pd.DataFrame(missingness)

def main():
    TABLES.mkdir(parents=True,exist_ok=True);PROCESSED.mkdir(parents=True,exist_ok=True)
    frames,audit=load_lits()
    status={'LiTS': {int(f.year.iloc[0]) for f in frames}=={2006,2010,2016}, 'WVS':False,'EVS':False}
    for survey,pattern in [('WVS','*WVS*Time*.*'),('EVS','ZA7503*.*')]:
        matches=[p for p in RAW.glob(pattern) if p.suffix.lower() in ['.dta','.sav']]
        if len(matches)>1:raise ValueError(f'Multiple {survey} sources; choose one version explicitly')
        if matches:
            f,a=load_values(survey,matches[0]);frames+=f;audit+=a;status[survey]=True
    if not frames:raise RuntimeError('No usable input data')
    frames=[add_index(f) for f in frames]
    est,dist,missing=summarize(frames)
    pd.concat(frames,ignore_index=True).to_csv(PROCESSED/'ukraine_harmonised.csv',index=False)
    pd.DataFrame(audit).to_csv(TABLES/'sample_audit.csv',index=False)
    est.to_csv(TABLES/'estimates.csv',index=False)
    dist.to_csv(TABLES/'distributions.csv',index=False)
    missing.to_csv(TABLES/'missingness.csv',index=False)
    (TABLES/'coverage_status.json').write_text(json.dumps(status,indent=2),encoding='utf8')
    print(json.dumps(status));print(est[(est.age_group=='All')&est.weighted&(est.territory=='survey_coverage')].to_string(index=False))
    # Analytical integrity checks rather than implementation-mirroring snapshots.
    assert est.n_valid.le(est.n_domain).all()
    assert est.ci_low.le(est.estimate).all() and est.ci_high.ge(est.estimate).all()
    sums=dist.groupby(['survey','year','item','age_group','territory','denominator']).estimate.sum()
    assert np.allclose(sums,1.),'Distributions do not sum to one'
    for f in frames:
        assert f.respondent_id.is_unique
        assert f.age.ge(18).all() and f.weight.gt(0).all()
    print('Analytical integrity checks passed.')

if __name__=='__main__':main()
