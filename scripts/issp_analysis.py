"""Ukraine ISSP: original archives to question-level estimates and audit trails."""
from pathlib import Path
from itertools import combinations
import hashlib
import json
import re
import zipfile
import numpy as np
import pandas as pd
import pyreadstat
from analyze import ROOT, TABLES
from ess_analysis import estimate

RAW=ROOT/'data/raw/issp'
DOC=ROOT/'docs'
FILES={2008:'ZA4950_v2-3-0.sav',2009:'ZA5400_v4-0-0.sav',2019:'ZA7810_v1-0-0.sav'}
ITEMS={}

def item(key,label,old,new,kind='agree',scope='Policy'):
    ITEMS[key]=dict(label=label,fields={2009:old,2019:new},kind=kind,scope=scope)

for key,label,old,new in [
    ('income_gap','Income differences are too large',32,21),
    ('redistribution','Government should reduce income differences',33,22),
    ('unemployed_living','Government should provide a decent living for unemployed people',34,23),
    ('cut_poor_benefits','Government should spend less on benefits for poor people',35,None),
    ('company_pay_gap','Companies should reduce differences in employee pay',None,24),
    ('politicians_indifferent','Politicians do not care about reducing income differences',None,26),
    ('global_gap','Economic differences between rich and poor countries are too large',None,33),
    ('aid_tax','People in wealthy countries should pay additional tax to help poorer countries',None,34),
    ('labour_migration','People from poor countries should be allowed to work in wealthy countries',None,35),
    ('skill_premium','Workers need extra pay to acquire skills and qualifications',None,62),
    ('inequality_prosperity','Large income differences are necessary for prosperity',None,63),
    ('inequality_power','Inequality persists because it benefits the rich and powerful',None,64),
    ('inequality_collective','Inequality persists because ordinary people do not unite against it',None,65),
    ('corrupt_to_top','Getting to the top requires being corrupt',17,None),
    ('elite_school_access','Students from the best secondary schools have the best chances of university education',18,None),
    ('rich_university','Only the rich can afford university',19,None),
    ('equal_university','People have equal chances of entering university regardless of background',20,None),
]: item(key,label,old,new,scope='Related' if key in ['income_gap','politicians_indifferent','global_gap','inequality_power','inequality_collective','corrupt_to_top','elite_school_access','rich_university','equal_university'] else 'Policy')
for key,label,old,new,kind in [
    ('tax_rich','Should richer people pay higher, the same or lower taxes?',36,28,'tax'),
    ('tax_level','Are current taxes on high incomes too high or too low?',37,29,'tax_level'),
    ('buy_health','Is it fair that richer people can buy better healthcare?',38,30,'fair5'),
    ('buy_education','Is it fair that richer people can buy better education for their children?',39,31,'fair5'),
    ('gov_success','Is government successful in reducing income differences?',None,27,'success'),
    ('income_fair','Is the income distribution in Ukraine fair?',None,50,'fair4'),
    ('anger','How angry do differences in wealth between rich and poor make you?',None,32,'numeric'),
    ('responsibility','Who should have the greatest responsibility for reducing income differences?',None,25,'responsibility'),
    ('society_actual','Which diagram best describes the shape of Ukrainian society?',54,48,'society'),
    ('society_ideal','Which shape of society would you prefer for Ukraine?',55,49,'society'),
]: item(key,label,old,new,kind,'Related' if key in ['tax_level','gov_success','income_fair','anger','society_actual'] else 'Policy')
for key,label,old,new in [
    ('wealth','coming from a wealthy family',6,1),('parents','having well-educated parents',7,2),
    ('education','having a good education',8,3),('ambition','having ambition',9,None),
    ('work','hard work',10,4),('connections','knowing the right people',11,5),
    ('political','political connections',12,6),('bribes','giving bribes',13,7),
    ('race','ethnic background (nationality)' ,14,8),('religion','a person’s religion',15,9),('gender','being born a man or woman',16,10),
]:item('ahead_'+key,'Importance for getting ahead: '+label,old,new,'important','Related')
for key,label,old,new in [('responsibility','job responsibility',47,44),('education','education and training',48,45),
    ('family','what is needed to support a family',49,None),('children','children to support',50,46),
    ('performance','how well the job is done',51,47),('effort','how hard the person works',52,None)]:
    item('pay_'+key,'What should determine pay: '+label,old,new,'important')
for key,label,old,new in [('rich_poor','rich and poor',40,36),('class','working and middle classes',41,37),
    ('management','management and workers',42,38),('top_bottom','top and bottom of society',43,None)]:
    item('conflict_'+key,'How much conflict is there between '+label+'?',old,new,'conflict','Related')
for i,(key,label) in enumerate([('doctor','a doctor'),('chairman','a corporate chairman'),('shop','a shop assistant'),('worker','an unskilled factory worker'),('minister','a cabinet minister')]):
    item('earn_actual_'+key,'How much does '+label+' earn per month after taxes?',22+i,11+i,'money','Related')
    item('earn_ideal_'+key,'How much should '+label+' earn per month after taxes?',27+i,16+i,'money','Policy')
ITEMS['business_confidence']=dict(label='Confidence in business and industry',fields={2008:15},kind='confidence',scope='Related')
LABELS={k:v['label'].rstrip('?') for k,v in ITEMS.items()}
POLARITY={k:'Monthly UAH after taxes, nominal prices; means among valid answers.' for k,v in ITEMS.items() if v['kind']=='money'}
POLARITY['anger']='0 = not angry at all; 10 = extremely angry'


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def inputs():
    for year,name in FILES.items():
        if not (RAW/name).exists():
            archives=list(RAW.glob(name[:6]+'*.zip'))+list(ROOT.glob(name[:6]+'*.zip'))
            assert archives, f'Download {name} from GESIS into data/raw/issp'
            with zipfile.ZipFile(archives[0]) as z:
                member=next(n for n in z.namelist() if Path(n).name==name)
                (RAW/name).write_bytes(z.read(member))
        yield year,RAW/name


def groups(kind,year):
    if kind=='numeric':return {'Mean':list(range(11))},list(range(11)),[6,7,8,9,10],'6–10 (above the scale midpoint)'
    if kind=='money':return {'Mean':[]},[],None,''
    if kind=='agree':g={'Agree':[1,2],'Disagree':[4,5],'Neither agree nor disagree':[3]}
    elif kind=='important':g={'Essential / very important':[1,2],'Not very / not at all important':[4,5],'Important':[3]}
    elif kind=='tax':g={'Higher taxes':[1,2],'Lower taxes':[4,5],'The same taxes':[3]}
    elif kind=='tax_level':g={'Too high':[1,2],'Too low':[4,5],'About right':[3]}
    elif kind=='fair5':g={'Fair':[1,2],'Unfair':[4,5],'Mixed feelings':[3]}
    elif kind=='fair4':g={'Fair':[1,2],'Unfair':[3,4]}
    elif kind=='success':g={'Successful':[1,2],'Unsuccessful':[4,5],'Neither':[3]}
    elif kind=='confidence':g={'High confidence':[1,2],'Little / no confidence':[4,5],'Some confidence':[3]}
    elif kind=='conflict':g={'Strong conflicts':[1,2],'Weak / no conflicts':[3,4]}
    elif kind=='responsibility':g={'Private companies':[1],'Government':[2],'Trade unions':[3],'High-income people':[4],'Low-income people':[5],'No reduction needed':[6]}
    elif kind=='society':g={'A: Elite over a large bottom':[1],'B: Pyramid':[2],'C: Pyramid with few at bottom':[3],'D: Most people in the middle':[4],'E: Many near top, few at bottom':[5]}
    else:raise ValueError(kind)
    valid=[v for vs in g.values() for v in vs]
    if kind=='responsibility':pos=[2];rule='Government has greatest responsibility'
    elif kind=='society':pos=[4];rule='Type D: most people in the middle (named preference, not a pro-market score)'
    else:pos=list(g.values())[0];rule=list(g)[0]
    g.update({"Don't know":[-8] if year==2019 else [8],'No answer':[-9] if year==2019 else [9]})
    return g,valid,pos,rule


def main():
    results=[];aff=[];cw=[];catalogue=[];samples=[];robust=[];joint=[];correlations=[];money_audit=[];source=[]
    for year,path in inputs():
        d,m=pyreadstat.read_sav(str(path),user_missing=True)
        if year<2019:d=d[d.V5.eq(804)].copy()
        else:assert d.country.eq(804).all()
        columns={k.lower():k for k in d}
        z=pd.DataFrame(dict(agea=d[columns['age']],pspwght=d.WEIGHT,psu=np.nan,stratum=np.nan),index=d.index)
        adult=z.agea.between(18,110)
        assert np.isfinite(z.pspwght).all() and z.pspwght.gt(0).all()
        assert len(d)=={2008:2036,2009:2012,2019:2001}[year]
        idcol='CASEID' if year==2019 else 'V3';assert not d[idcol].duplicated().any()
        geo=d[columns['ua_reg']];restricted=adult&~geo.isin([1,7,13])
        source.append(dict(file=str(path.relative_to(ROOT)),sha256=digest(path),bytes=path.stat().st_size))
        samples.append(dict(survey='ISSP',year=year,n_raw=len(d),n_adult=int(adult.sum()),n_age_excluded=int((~adult).sum()),
            weight_min=z.pspwght.min(),weight_max=z.pspwght.max(),weight_sum=z.loc[adult,'pspwght'].sum(),
            n_common_geography=int(restricted.sum()),weight='WEIGHT',design='PSU/stratum identifiers unavailable; respondent-based approximate intervals'))
        selected={('v'+str(s['fields'][year])).lower():k for k,s in ITEMS.items() if s['fields'].get(year) is not None}
        for field,label in m.column_names_to_labels.items():
            catalogue.append(dict(year=year,field=field,label=label,selected=field.lower() in selected,
                item=selected.get(field.lower(),''),reason='Economic attitude/belief' if field.lower() in selected else
                'Not a general market/state attitude: demographic, personal circumstance, social relation, general politics or religion; optional v66 unavailable in Ukraine'))
        harmonized={}
        for key,spec in ITEMS.items():
            number=spec['fields'].get(year)
            if number is None:continue
            field=columns['v'+str(number)];raw=d[field];kind=spec['kind'];g,valid,pos,rule=groups(kind,year)
            labs=m.variable_value_labels.get(field,{})
            ok=raw.ge(0) if kind=='money' else raw.isin(valid)
            if not (adult&ok).any():continue
            if kind!='money':assert raw.dropna().isin(list(labs)).all(),(year,key,'Unknown codes')
            qtype='numeric' if kind in ['numeric','money'] else 'nominal' if kind in ['society','responsibility'] else 'ordinal'
            question=spec['label'] if spec['label'].endswith('?') else spec['label']+'?'
            base=dict(survey='ISSP',year=year,item=key,question=question,question_type=qtype,
                source_file=path.name,source_sha256=digest(path),source_field=field,source_table='original microdata')
            missing=100*z.loc[adult&~ok,'pspwght'].sum()/z.loc[adult,'pspwght'].sum()
            comparable='Replicated source item and national wording/scale checked; geography differs in 2019'
            if key=='tax_rich':comparable+='; Ukrainian questionnaires say higher taxes, omitting the source questionnaire’s share-of-income qualification'
            if kind=='money':comparable+='; nominal monthly UAH after tax in both waves; inflation prevents interpreting growth as a change in preferred real pay'
            cw.append(dict(**base,source_label=m.column_names_to_labels[field],response_labels=json.dumps(labs,ensure_ascii=False),
                valid_codes='Nonnegative reported UAH; negative special codes excluded' if kind=='money' else json.dumps(valid),
                response_groups=json.dumps(g,ensure_ascii=False),positive_definition=rule,
                weighted_missing_pct=missing,weight='WEIGHT',reversal='None',comparability=comparable,scope=spec['scope'],
                units='UAH per month after tax, nominal' if kind=='money' else '0–10' if kind=='numeric' else 'percent'))
            for age,domain in [('All',adult),('18-34',adult&z.agea.le(34)),('35-54',adult&z.agea.between(35,54)),('55+',adult&z.agea.ge(55))]:
                for label,codes in g.items():
                    if qtype=='numeric':y=raw.where(ok);bounds=(0,None) if kind=='money' else (0,10)
                    else:
                        yes=raw.isin(codes)
                        if label=='No answer':yes=yes|raw.isna()
                        y=yes.astype(float)*100;bounds=(0,100)
                    if kind=='money':bounds=(0,np.inf)
                    results.append(dict(**base,age_group=age,response=label,**estimate(z,y,domain,bounds=bounds),
                        denominator='valid monetary answers' if kind=='money' else 'valid 0–10 ratings' if kind=='numeric' else 'all eligible adults',
                        excluded_non_numeric_pct=missing if qtype=='numeric' else np.nan))
                    if age=='All':
                        for territory,dom,w in [('survey_coverage',adult,False),('exclude_Crimea_Donetsk_Luhansk',restricted,True)]:
                            robust.append(dict(**base,response=label,territory=territory,**estimate(z,y,dom,w,bounds)))
            if pos is not None:
                aff.append(dict(**base,age_group='All',positive_definition=rule,kind=spec['scope'],denominator='all eligible adults',
                    **estimate(z,raw.isin(pos).astype(float)*100,adult,bounds=(0,100))))
            if kind=='money':
                keep=adult&ok;x=raw[keep];w=z.loc[keep,'pspwght'];cap=x.quantile(.99)
                money_audit.append(dict(year=year,item=key,n_valid=int(keep.sum()),minimum=x.min(),median=x.median(),maximum=x.max(),
                    unweighted_mean=x.mean(),weighted_mean=np.average(x,weights=w),weighted_mean_winsor99=np.average(x.clip(upper=cap),weights=w),
                    weighted_missing_pct=missing,price_basis='Nominal monthly UAH after tax; no inflation adjustment'))
            elif kind in ['agree','important','fair5','tax']:
                harmonized[key]=raw.where(ok)
        # Agreement/importance in the same direction; report named pairs, not a broad ideology index.
        keys=[k for k in ['redistribution','buy_health','buy_education','pay_performance','skill_premium','inequality_prosperity','company_pay_gap'] if k in harmonized]
        for a,b in combinations(keys,2):
            x=6-harmonized[a];y=6-harmonized[b];keep=adult&x.notna()&y.notna();w=z.loc[keep,'pspwght'];x=x[keep];y=y[keep]
            xm=np.average(x,weights=w);ym=np.average(y,weights=w)
            corr=np.sum(w*(x-xm)*(y-ym))/np.sqrt(np.sum(w*(x-xm)**2)*np.sum(w*(y-ym)**2))
            correlations.append(dict(survey='ISSP',year=year,item=a+'__'+b,item_1=a,item_2=b,estimate=corr,n_valid=int(keep.sum()),coding='Higher = stronger agreement, fairness or importance for the stated item'))
            both=harmonized[a].isin([1,2])&harmonized[b].isin([1,2])
            joint.append(dict(survey='ISSP',year=year,item=a+'__'+b,denominator='all eligible adults',**estimate(z,both.astype(float)*100,adult,bounds=(0,100))))
    result=pd.DataFrame(results);cross=pd.DataFrame(cw);affirm=pd.DataFrame(aff)
    sums=result[result.question_type.ne('numeric')].groupby(['year','item','age_group']).estimate.sum()
    assert np.allclose(sums,100),sums[~np.isclose(sums,100)]
    assert (result.ci_low<=result.estimate).all() and (result.estimate<=result.ci_high).all()
    for name,rows in [('estimates',result),('affirmative_shares',affirm),('sensitivity',robust),('sample_audit',samples),
        ('correlations',correlations),('joint_agreement',joint),('monetary_audit',money_audit)]:
        pd.DataFrame(rows).to_csv(TABLES/f'issp_{name}.csv',index=False,encoding='utf-8-sig')
    cross.to_csv(DOC/'issp_question_crosswalk.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(catalogue).to_csv(DOC/'issp_variable_catalogue.csv',index=False,encoding='utf-8-sig')
    inventory=cross.groupby('item',sort=False).agg(question=('question','first'),question_type=('question_type','first'),scope=('scope','first'),
        years=('year',lambda x:', '.join(map(str,sorted(x)))),latest_year=('year','max'),n_waves=('year','nunique')).reset_index()
    inventory['html_eligible']=inventory.n_waves.ge(2)&inventory.latest_year.ge(2019)
    inventory.to_csv(TABLES/'issp_variable_inventory.csv',index=False,encoding='utf-8-sig')
    trend=result[result.age_group.eq('All')&result.item.isin(inventory.loc[inventory.html_eligible,'item'])]
    trend.to_csv(TABLES/'issp_question_trend_estimates.csv',index=False,encoding='utf-8-sig')
    defs=[]
    for key in trend.item.unique():
        row=cross[cross.item.eq(key)].iloc[0];money=ITEMS[key]['kind']=='money'
        defs.append(dict(survey='ISSP',item=key,question_type=row.question_type,response_groups=row.response_groups,
            question_override=row.question,scale_min=0,scale_max=np.nan if money else 10,units=row.units,
            method_note='Adults 18+; weighted means and approximate 95% intervals. Nominal UAH; price levels differ.' if money else
            'Adults 18+; supplied weights. Approximate 95% intervals; see methods for sampling and coverage.'))
    pd.DataFrame(defs).to_csv(DOC/'issp_trend_definitions.csv',index=False,encoding='utf-8-sig')
    manifest=dict(acquired='2026-09-28',files=source,
        archives=[dict(file=str(p.relative_to(ROOT)),sha256=digest(p)) for p in RAW.glob('*.zip')],
        documentation=[dict(file=str(p.relative_to(ROOT)),sha256=digest(p)) for p in (ROOT/'data/documentation/issp').glob('*.pdf')],
        sources=['https://doi.org/10.4232/1.13161','https://doi.org/10.4232/1.12777','https://doi.org/10.4232/1.13853'],
        instructions='Download ZA4950 v2.3.0, ZA5400 v4.0.0 and ZA7810 v1.0.0 through authenticated GESIS academic-research access. Original archives remain in data/raw/issp and are excluded from export packages.')
    (ROOT/'data/source_manifests/issp.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    status=dict(status='passed',included_items=len(inventory),item_waves=len(cross),html_items=int(inventory.html_eligible.sum()),
        microdata_variables_audited=len(catalogue),years=[2008,2009,2019],
        checks=['Unique Ukrainian respondent IDs; official sample sizes matched','Adults 18+; positive finite supplied weights',
        'Known categorical codes; categories total 100','Monetary missing codes excluded; outlier sensitivity exported',
        'Weighted/unweighted and consistent regional exclusion exported','Native tax wording checked in both years'])
    (TABLES/'issp_validation.json').write_text(json.dumps(status,indent=2),encoding='utf8')
    print(json.dumps(status,indent=2))


if __name__=='__main__':main()
