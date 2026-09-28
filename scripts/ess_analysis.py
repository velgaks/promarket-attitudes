"""Audit the supplied ESS files and estimate Ukrainian economic attitudes.

Round identifiers are never used as calendar years. Keep the related R10 study
identified in every row. Original files stay unchanged and are not redistributed.
"""
from pathlib import Path
import hashlib
import json
import re
import zipfile
from itertools import combinations
import numpy as np
import pandas as pd
import pyreadstat
from bs4 import BeautifulSoup
from scipy.stats import t
from analyze import ROOT, TABLES

RAW = ROOT / 'data/raw/ess'
DOC = ROOT / 'docs'
YEARS = {2:2005, 3:2007, 4:2009, 5:2011, 6:2013, 10:2022, 11:2024}
PERIODS = {2:'2005',3:'2006–07',4:'2009',5:'2011',6:'2013',10:'2022',11:'2024'}
AGREE = ['gincdif','bsnprft','cmprcti','ctzchtx','frmwktg','mnyacth','scbevts',
         'dfincac','smdfslv','gvprppv','bennent','insfben','lbenent','prtsick',
         'sbbsntx','sbcwkfm','sbenccm','sbeqsoc','sblazy','sblwcoa','sblwlka',
         'sbprvpv','sbstrec','uentrjb']
NUMERIC = ['imbgeco','gvctzpv','grdfinc','gvctzpvc','grdfincc','ditxssp',
           'gvcldcr','gvhlthc','gvjbevn','gvpdlwk','gvslvol','gvslvue','imrccon',
           'tstfnch','tstpboh','tstrprh']
NOMINAL = ['earnpen','earnueb','txearn']
OTHER = ['imsclbn','pyavtxw','fineqpy','eqparlv']
ITEMS = AGREE + NUMERIC + NOMINAL + OTHER
CONTEXT = ['imbgeco','gvctzpvc','grdfincc','cmprcti','bennent','insfben','lbenent',
           'prtsick','imrccon','tstfnch','tstpboh','tstrprh','fineqpy','eqparlv']
QUESTIONS = {
    'gincdif':'Should the government take measures to reduce differences in income levels?',
    'imbgeco':"Is immigration bad or good for Ukraine's economy?",
    'gvctzpv':'How important is government protection against poverty for democracy?',
    'grdfinc':'How important is government reduction of income differences for democracy?',
    'gvctzpvc':'To what extent does the government in Ukraine protect citizens against poverty?',
    'grdfincc':'To what extent does the government in Ukraine reduce income differences?',
}
LABELS = {'gincdif':'Support for government action to reduce income gaps',
          'imbgeco':'Immigration judged good for the economy',
          'gvctzpv':'Protection from poverty as a democratic principle',
          'grdfinc':'Reducing income gaps as a democratic principle',
          'gvctzpvc':'Government protection from poverty in practice',
          'grdfincc':'Government reduction of income gaps in practice'}
POLARITY = {'imbgeco':'0 = bad for the economy; 10 = good for the economy',
            'gvctzpv':'0 = not at all important; 10 = extremely important',
            'grdfinc':'0 = not at all important; 10 = extremely important',
            'gvctzpvc':'0 = does not apply at all; 10 = applies completely',
            'grdfincc':'0 = does not apply at all; 10 = applies completely'}


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def inputs():
    RAW.mkdir(parents=True, exist_ok=True)
    archive = next(iter(sorted(RAW.glob('ESS2*-subset.zip'))), None)
    if archive is None: archive = next(ROOT.glob('ESS2*-subset.zip'))
    with zipfile.ZipFile(archive) as z:
        for member in z.infolist():
            p = RAW / Path(member.filename).name
            if not p.exists():
                p.write_bytes(z.read(member))
    round10 = RAW/'ESS10UAe4.sav'
    if not round10.exists(): round10 = ROOT/'ESS10UAe4.sav'
    return [next(RAW.glob('ESS2*-subset.sav')), round10], archive


def estimate(z, y, domain=None, weighted=True, bounds=None):
    """With-replacement stratified PSU Taylor variance of a domain ratio.

    Retain all sampled PSUs, including those contributing zero to the adult/age
    domain. Older files without design identifiers use respondent linearization.
    No FPC; supplied calibration weights treated as fixed.
    """
    domain = z.agea.ge(18) & z.agea.lt(999) if domain is None else domain
    w = z.pspwght if weighted else pd.Series(1., index=z.index)
    use = domain & y.notna() & w.gt(0) & np.isfinite(w)
    total = w[use].sum()
    assert total > 0
    mean = (w[use]*y[use]).sum()/total
    residual = pd.Series(0.,index=z.index)
    residual[use] = w[use]*(y[use]-mean)/total
    design = z.psu.notna().all() and z.stratum.notna().all()
    if design:
        cluster = pd.DataFrame({'h':z.stratum,'p':z.psu,'e':residual}).groupby(['h','p']).e.sum()
        counts = cluster.groupby(level=0).size()
        assert counts.ge(2).all(), 'Singleton stratum requires explicit treatment'
        variance = sum(len(v)/(len(v)-1)*((v-v.mean())**2).sum() for _,v in cluster.groupby(level=0))
        df = int(len(cluster)-len(counts))
        method = 'Stratified PSU Taylor linearization; fixed supplied weights; no FPC'
        npsu = len(cluster)
    else:
        n = len(z)
        variance = n/(n-1)*(residual**2).sum()
        df = n-1
        method = 'Approximate weighted respondent linearization; PSU/stratum unavailable in supplied file'
        npsu = n
    se = np.sqrt(variance); half = t.ppf(.975,df)*se
    lo,hi = mean-half,mean+half
    if bounds is not None: lo=max(bounds[0],lo);hi=min(bounds[1],hi)
    return dict(estimate=mean,se=se,ci_low=lo,ci_high=hi,n_valid=int(use.sum()),
                n_domain=int(domain.sum()),n_psu=npsu,design_df=df,
                kish_n=total**2/(w[use]**2).sum(),weight_sum=total,
                weighted=weighted,variance_method=method)


def region_excluded(z,r):
    if r<=4:return z.regionua.isin([1,5,12,27])
    if r==10:return z.region.isin(['UA01','UA05','UA12','UA27'])
    return z.region.isin(['UA44','UA45','UA21','UA22'])


def groups(item,labels):
    if item in NUMERIC:return 'numeric',{'Mean':list(range(11))},list(range(11))
    if item in AGREE:
        g={'Agree':[1,2],'Disagree':[4,5],'Neither agree nor disagree':[3]}
    elif item in ['fineqpy','eqparlv']:
        g={'In favour':[1,2],'Against':[4,5],'Neither in favour nor against':[3]}
    elif item=='pyavtxw':
        g={'Wrong / seriously wrong':[3,4],'Not wrong at all':[1],'A bit wrong':[2]}
    else:
        g={v:[int(k)] for k,v in labels.items() if k<7}
    g.update({"Don't know":[8],'Refused / no answer':[7,9]})
    valid=[v for k,vs in g.items() if k not in ["Don't know",'Refused / no answer'] for v in vs]
    return ('nominal' if item in NOMINAL else 'ordinal'),g,valid


def main():
    paths,archive=inputs()
    soup=BeautifulSoup(next(RAW.glob('*.html')).read_text(encoding='utf8'),'html.parser')
    metadata={};frames=[];source_rows=[]
    for path in paths:
        _,m=pyreadstat.read_sav(str(path),metadataonly=True)
        required=ITEMS+['cntry','essround','idno','agea','pspwght','dweight','anweight','psu','stratum',
                        'region','regionua','inwds','inwde','inwyys','inwmms','inwdds']
        d,_=pyreadstat.read_sav(str(path),usecols=[x for x in required if x in m.column_names],user_missing=True)
        assert d.cntry.eq('UA').all()
        d['source_file']=path.name;d['source_sha256']=digest(path)
        for col in ['psu','stratum','regionua','region']:
            if col not in d:d[col]=np.nan
        frames.append(d)
        for r in d.essround.unique():metadata[int(r)]=m
        source_rows.append(dict(file=str(path.relative_to(ROOT)),sha256=digest(path),bytes=path.stat().st_size))
    d=pd.concat(frames,ignore_index=True)
    assert not d.duplicated(['essround','idno']).any()
    assert set(d.essround.astype(int))==set(YEARS)
    audit=[];crosswalk=[];samples=[];results=[];affirmative=[];robust=[];pairrows=[];jointrows=[];catalogue=[]
    all_labels={k:v for m in metadata.values() for k,v in m.column_names_to_labels.items()}
    for item,label in all_labels.items():
        selected=item in ITEMS
        reason=('Direct economic attitude' if item not in CONTEXT else 'Related economic belief, evaluation or labour regulation') if selected else (
            'Personal values, not a specific economic institution or policy' if item.startswith(('ip','imp')) else
            'Reported experience, circumstances, general politics or other subject; not a selected market/state attitude')
        catalogue.append(dict(variable=item,label=label,included=selected,reason=reason))
    for r,z in d.groupby('essround',sort=True):
        r=int(r);year=YEARS[r];m=metadata[r]
        adult=z.agea.ge(18)&z.agea.lt(999)
        assert z.pspwght.gt(0).all() and np.isfinite(z.pspwght).all()
        if r in [10,11]:
            starts=pd.to_datetime(z.inwds); start=starts.min().isoformat();end=starts.max().isoformat()
        elif r==2:start,end='2005-01-28','2005-03-10'
        else:
            starts=pd.to_datetime(dict(year=z.inwyys,month=z.inwmms,day=z.inwdds),errors='coerce')
            start,end=starts.min().isoformat(),starts.max().isoformat()
        samples.append(dict(survey='ESS',round=r,year=year,fieldwork_period=PERIODS[r],
            interview_start_min=start,interview_start_max=end,n_raw=len(z),n_adult=int(adult.sum()),
            n_age_missing=int(z.agea.isna().sum()+z.agea.eq(999).sum()),
            n_psu=z.psu.nunique(),n_strata=z.stratum.nunique(),weight='pspwght',
            pspwght_equals_dweight=bool(np.allclose(z.pspwght,z.dweight)),
            source_file=z.source_file.iloc[0],source_sha256=z.source_sha256.iloc[0],
            study_status='Related study using ESS10 questionnaire' if r==10 else 'ESS integrated round'))
        for item in ITEMS:
            if item not in z:continue
            raw=z[item];labs=m.variable_value_labels.get(item,{})
            if not labs:continue
            kind,g,valid=groups(item,labs)
            nvalid=int((adult & raw.isin(valid)).sum())
            audit.append(dict(survey='ESS',round=r,year=year,item=item,n_valid=nvalid,n_adult=int(adult.sum())))
            if not nvalid:continue
            assert raw.dropna().isin(list(labs)).all(),(r,item,'Unlabelled code')
            node=soup.find(id=item)
            wording=' '.join(t.get_text(' ',strip=True) for t in node.parent.select('.variable-meta-string')) if node else all_labels[item]
            question=QUESTIONS.get(item,all_labels[item].rstrip('?')+'?')
            base=dict(survey='ESS',round=r,year=year,fieldwork_period=PERIODS[r],item=item,
                question=question,question_type=kind,source_file=z.source_file.iloc[0],
                source_sha256=z.source_sha256.iloc[0],source_field=item,source_table='original microdata',
                study_status='Related study using ESS10 questionnaire' if r==10 else 'ESS integrated round')
            missing=100*z.loc[adult & ~raw.isin(valid),'pspwght'].sum()/z.loc[adult,'pspwght'].sum()
            crosswalk.append(dict(**base,wording=wording,response_labels=json.dumps(labs,ensure_ascii=False),
                valid_codes=json.dumps(valid),response_groups=json.dumps(g,ensure_ascii=False),
                reversal='None: original direction retained',weight='pspwght',weighted_missing_pct=missing,
                comparability='Common variable, question and response scale verified against supplied codebook'+('; R10 Ukrainian questionnaire checked' if r==10 else ''),
                scope='Related belief/evaluation/regulation' if item in CONTEXT else 'Direct economic attitude'))
            for age,domain in [('All',adult),('18-34',adult&z.agea.le(34)),('35-54',adult&z.agea.between(35,54)),('55+',adult&z.agea.ge(55))]:
                for label,codes in g.items():
                    if kind=='numeric': y=raw.where(raw.isin(valid));bounds=(0,10)
                    else:
                        mask=raw.isin(codes)
                        if label=='Refused / no answer':mask=mask|raw.isna()
                        y=mask.astype(float)*100;bounds=(0,100)
                    out=estimate(z,y,domain,bounds=bounds)
                    results.append(dict(**base,age_group=age,response=label,**out,
                        denominator='valid 0–10 ratings' if kind=='numeric' else 'all eligible adults',
                        excluded_non_numeric_pct=missing if kind=='numeric' else np.nan))
                    if age=='All':
                        for territory,dom,w in [('survey_coverage',adult,False),('exclude_Crimea_Donetsk_Luhansk',adult&~region_excluded(z,r),True)]:
                            robust.append(dict(**base,response=label,territory=territory,**estimate(z,y,dom,w,bounds)))
            # Preserve the established latest-affirmative appendix convention.
            # These shares are not used in numeric trend charts.
            if kind=='numeric': pos=raw.between(6,10);rule='6–10 on the original 0–10 scale (above its midpoint)'
            elif item=='txearn':pos=raw.eq(2);rule='Higher earners should pay a higher share of earnings in tax'
            elif item in ['earnpen','earnueb']:pos=raw.eq(2);rule='High and low earners should receive the same amount'
            elif item=='imsclbn':pos=raw.eq(3);rule='After working and paying taxes for at least a year'
            elif item=='pyavtxw':pos=raw.isin([3,4]);rule='Wrong / seriously wrong'
            else:pos=raw.isin([1,2]);rule='In favour / strongly in favour' if item in ['fineqpy','eqparlv'] else 'Agree / agree strongly'
            affirmative.append(dict(**base,age_group='All',positive_definition=rule,kind='Related' if item in CONTEXT else 'Policy',
                denominator='all eligible adults',**estimate(z,pos.astype(float)*100,bounds=(0,100))))
        # Within-person coexistence, without constructing a broad market index.
        if r==4:
            pair=z[['gincdif','dfincac','smdfslv','sblazy','sbstrec']].where(lambda x:x.ge(1)&x.le(5))
            for a,b in combinations(pair.columns,2):
                ok=adult&pair[a].notna()&pair[b].notna();w=z.loc[ok,'pspwght'];x=6-pair.loc[ok,a];y=6-pair.loc[ok,b]
                xm=np.average(x,weights=w);ym=np.average(y,weights=w)
                corr=np.sum(w*(x-xm)*(y-ym))/np.sqrt(np.sum(w*(x-xm)**2)*np.sum(w*(y-ym)**2))
                pairrows.append(dict(survey='ESS',year=year,item=a+'__'+b,item_1=a,item_2=b,estimate=corr,n_valid=int(ok.sum()),coding='Higher = stronger agreement with each stated proposition'))
            for a,b in [('gincdif','dfincac'),('smdfslv','dfincac'),('gincdif','sblazy')]:
                joint=z[a].isin([1,2])&z[b].isin([1,2])
                jointrows.append(dict(survey='ESS',year=year,item=a+'__'+b,denominator='all eligible adults',**estimate(z,joint.astype(float)*100,bounds=(0,100))))
    result=pd.DataFrame(results); aff=pd.DataFrame(affirmative); cw=pd.DataFrame(crosswalk)
    assert result.n_valid.le(result.n_domain).all()
    cats=result[result.question_type.ne('numeric')]
    assert np.allclose(cats.groupby(['round','item','age_group']).estimate.sum(),100)
    assert result[result.question_type.eq('numeric')].estimate.between(0,10).all()
    for name,rows in [('ess_estimates',result),('ess_affirmative_shares',aff),('ess_sensitivity',robust),
        ('ess_sample_audit',samples),('ess_availability',audit),('ess_correlations',pairrows),('ess_joint_agreement',jointrows)]:
        pd.DataFrame(rows).to_csv(TABLES/(name+'.csv'),index=False,encoding='utf-8-sig')
    cw.to_csv(DOC/'ess_question_crosswalk.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(catalogue).to_csv(DOC/'ess_variable_catalogue.csv',index=False,encoding='utf-8-sig')
    inventory=cw.groupby('item',sort=False).agg(question=('question','first'),question_type=('question_type','first'),scope=('scope','first'),
        years=('year',lambda x:', '.join(map(str,sorted(x)))),rounds=('round',lambda x:', '.join(map(str,sorted(x)))),
        latest_year=('year','max'),n_waves=('year','nunique')).reset_index()
    inventory['html_eligible']=inventory.n_waves.ge(2)&inventory.latest_year.ge(2019)
    inventory.to_csv(TABLES/'ess_variable_inventory.csv',index=False,encoding='utf-8-sig')
    trend=result[result.age_group.eq('All')&result.item.isin(inventory.loc[inventory.html_eligible,'item'])]
    trend.to_csv(TABLES/'ess_question_trend_estimates.csv',index=False,encoding='utf-8-sig')
    defs=[]
    for item in trend.item.unique():
        row=cw[cw.item.eq(item)].iloc[0]
        defs.append(dict(survey='ESS',item=item,question_type=row.question_type,response_groups=row.response_groups,
            method_note='Adults 18+; supplied weights and 95% intervals. ESS10 is the related Ukrainian study.',
            question_override=row.question,scale_min=0,scale_max=10))
    pd.DataFrame(defs).to_csv(DOC/'ess_trend_definitions.csv',index=False,encoding='utf-8-sig')
    documents=[dict(file=str(p.relative_to(ROOT)),sha256=digest(p)) for p in (ROOT/'data/documentation/ess').iterdir() if p.suffix in ['.pdf','.md','.log']]
    documents.append(dict(file=str(next(RAW.glob('*.html')).relative_to(ROOT)),sha256=digest(next(RAW.glob('*.html')))))
    manifest=dict(acquired='2026-09-25',files=source_rows,documentation=documents,archive=dict(file=str(archive.relative_to(ROOT)),sha256=digest(archive)),
        sources=['https://www.europeansocialsurvey.org/data-portal','https://github.com/KSE-Sociological-Center/ESS10_Ukraine'],
        instructions='Download Ukraine, all variables, ESS rounds 2–6 and 11 from the ESS data wizard as SPSS plus codebook. Put the supplied subset ZIP and ESS10UAe4.sav in data/raw/ess. R10 is an associated study from the Ukrainian team, not an integrated ESS round. Do not pool duplicate versions.')
    (ROOT/'data/source_manifests/ess.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    status=dict(status='passed',variables_audited=len(catalogue),included_items=len(inventory),item_waves=len(cw),
        html_items=inventory.loc[inventory.html_eligible,'item'].tolist(),rounds=list(YEARS),
        weight='pspwght; includes design weight; R11 supplied pspwght equals dweight',
        checks=['Ukraine only; unique round/respondent keys','Adults 18+; missing ages excluded','All observed codes labelled',
        'All categorical shares sum to 100','Actual interview years','Numeric means retain original 0–10 scale',
        'Weighted/unweighted and common-region sensitivity exported','Full design retained for age domains'])
    (TABLES/'ess_validation.json').write_text(json.dumps(status,indent=2),encoding='utf8')
    print(json.dumps(status,indent=2))


if __name__=='__main__':main()
