"""Question-type-aware estimates for the standalone trend gallery.

Numeric rating scales use means. Verbal ordinal scales pool only adjacent
positive/negative categories. Nominal questions retain all alternatives.
All categorical charts use all respondents, with nonresponse displayed.
"""
import json
import re
import hashlib
import numpy as np
import pandas as pd
from analyze import ROOT, RAW, TABLES, read_selected, estimate
from extended_attitudes import check_original
from extended_published import source_info, pew, mon, ROWS, CELLS
from monitoring_extract import page_text

DEST = TABLES / 'question_trend_estimates.csv'
ROWS_OUT, TRACE, DEFINITIONS = [], [], []
DEMOCRACY = ['E224', 'E227', 'E233A']
NUMERIC = ['E035','E036','E037','E038','E039','E040',*DEMOCRACY,'F114A','F116']
REVERSE = ['E036','E037','E038','E039','E040','F114A','F116']
MAPPED = {
    'state_role_minimal_state_market':'state_market_role',
    'state_role_mixed_state_market':'state_market_role',
    'state_role_planned_economy':'state_market_role',
    'ownership_policy_broad_privatisation':'ownership_policy',
    'ownership_policy_nationalise':'ownership_policy',
    'ownership_policy_privatise_except_efficient_state_firms':'ownership_policy',
    'ownership_policy_retain_state_firms':'ownership_policy',
}


def eligible():
    inv=pd.read_csv(TABLES/'question_year_inventory.csv')
    inv['n_years']=inv.years.str.split(', ').str.len()
    inv['latest_year']=inv.years.str.split(', ').str[-1].astype(int)
    inv['included']=inv.n_years.ge(2)&inv.latest_year.ge(2019)
    inv['chart_item']=inv.item.map(MAPPED).fillna(inv.item)
    inv['chart_id']=inv.survey.str.lower()+'__'+inv.chart_item.str.lower()
    inv['reason']=np.where(inv.included,'',np.where(inv.n_years.lt(2),'Fewer than two observed years; ','')+
                           np.where(inv.latest_year.lt(2019),'Latest observation before 2019',''))
    return inv


def define(survey,item,kind,groups,note='',question=None):
    DEFINITIONS.append(dict(survey=survey,item=item,question_type=kind,
        response_groups=json.dumps(groups,ensure_ascii=False),method_note=note,question_override=question))


def microdata(inv):
    for survey,filename in [('WVS','WVS_Time_Series_1981-2022_spss_v5_0.sav'),('EVS','ZA7503_v3-0-0.sav')]:
        selected=inv[inv.included & inv.survey.eq(survey)]
        check_original(filename)
        d,meta=read_selected(RAW/filename,['S001','S003','S020','S017','X003']+selected.item.tolist())
        d.columns=d.columns.str.upper()
        d=d[d.S003.eq(804)&d.X003.ge(18)&d.S017.gt(0)&np.isfinite(d.S017)].copy()
        assert d.S001.eq(2 if survey=='WVS' else 1).all()
        d['weight']=d.S017;d['psu']=d.index.astype(str)
        d['variance_method']='Weighted respondent linearization; approximate'
        for spec in selected.itertuples():
            item=spec.item
            if item in NUMERIC:
                kind='numeric'
                note='Weighted mean of valid 1–10 responses; approximate 95% confidence intervals.'
                if item in DEMOCRACY:
                    note='Mean of 1–10 ratings; spontaneous “against democracy” answers are outside the numeric scale.'
                groups={'Mean':list(range(1,11))}
            elif item.startswith('E069_'):
                kind='ordinal';note='Positive and negative categories combined; all adults, including nonresponse.'
                groups={'Confidence':[1,2],'No confidence':[3,4],"Don't know":[-1],
                        'No answer / other missing':[-2,-3,-4,-5]}
            else:
                assert item=='B008'
                kind='nominal';note='All response options; all adults, including nonresponse.'
                groups={'Protect the environment':[1],'Growth and jobs':[2],'Other answer':[3],
                        "Don't know":[-1],'No answer / other missing':[-2,-3,-4,-5]}
            define(survey,item,kind,groups,note)
            for year in map(int,spec.years.split(', ')):
                z=d[d.S020.eq(year)].copy();raw=z[item]
                base=dict(survey=survey,item=item,year=year,question_type=kind,
                    source_file=filename,source_field=item,source_table='original microdata',
                    source_sha256=json.loads((ROOT/'data/source_manifests'/(filename+'.json')).read_text())['sha256'])
                if kind=='numeric':
                    y=raw.where(raw.between(1,10));y=11-y if item in REVERSE else y
                    out=estimate(z,y,bounds=(1,10))
                    ROWS_OUT.append(dict(**base,response='Mean',**out,
                        denominator='valid 1–10 ratings',excluded_non_numeric_pct=100*z.loc[~raw.between(1,10),'weight'].sum()/z.weight.sum(),
                        spontaneous_against_democracy_pct=100*z.loc[raw.eq(0),'weight'].sum()/z.weight.sum() if item in DEMOCRACY else np.nan))
                else:
                    assert raw.dropna().isin([v for codes in groups.values() for v in codes]).all(),(survey,item,year,'Unexpected category')
                    for label,codes in groups.items():
                        mask=raw.isin(codes)
                        if label=='No answer / other missing':mask=mask|raw.isna()
                        out=estimate(z,mask.astype(float)*100,bounds=(0,100))
                        ROWS_OUT.append(dict(**base,response=label,**out,denominator='all eligible adults'))
        print(survey,'question-type estimates complete',flush=True)


def published(survey,item,raw,groups,kind='ordinal',note='',question=None):
    define(survey,item,kind,groups,note,question)
    assert set(raw.response.unique())==set(v for values in groups.values() for v in values),(item,'Unmapped responses')
    for year,z in raw.groupby('year'):
        for label,codes in groups.items():
            rows=z[z.response.isin(codes)]
            if rows.empty:continue  # An option not offered in a wave is not a zero.
            value=rows.percent.sum()
            ROWS_OUT.append(dict(survey=survey,item=item,year=int(year),response=label,estimate=value,
                ci_low=np.nan,ci_high=np.nan,question_type=kind,denominator='all respondents as published',
                source_table='question_trend_source_cells.csv',source_file='; '.join(rows.source_file.unique()),
                source_field='; '.join(map(str,rows.source_question.unique()))))
            for r in rows.to_dict('records'):
                TRACE.append(dict(survey=survey,item=item,grouped_response=label,**r))


def monitoring_existing(inv):
    raw=pd.read_csv(TABLES/'monitoring_published_results.csv').rename(columns={'question_code':'source_question'})
    chosen=set(inv.loc[inv.included & inv.survey.eq('Monitoring'),'chart_item'])
    for item in sorted(chosen & set(raw.item)):
        z=raw[raw.item.eq(item)].drop(columns=['item']).copy()
        responses=set(z.response)
        note='Positive and negative responses combined; published percentages of all respondents.'
        kind='ordinal';question=None
        if item.startswith('existing_private_'):
            groups={'Positive':['positive','rather_positive'],'Negative':['negative','rather_negative']}
        elif item.startswith('privatise_'):
            groups={'Positive':['positive'],'Negative':['negative'],'Mixed / ambivalent':['ambivalent']}
        elif item.startswith(('retrospective_','renationalise_')) or item=='work_private_employer':
            groups={'Yes':['yes','rather_yes'],'No':['no','rather_no']}
            if item.startswith('renationalise_'):
                sector={'land':'land','small':'small enterprises','large':'large enterprises'}[item.split('_')[-1]]
                question='Should privately owned '+sector+' be returned to state ownership?'
        elif item=='land_sales_agricultural':
            groups={'Yes':['yes'],'No':['no']}
        elif item=='land_ownership_rights':
            kind='nominal';groups={'Full ownership, including sale':['full_ownership_including_sale'],
                'Inheritable use, no sale':['inheritable_use_no_sale'],'Community ownership':['community_ownership'],
                'State ownership':['state_ownership']}
            question='What rights should people have over land?'
        elif item=='state_market_role':
            kind='nominal';groups={'Minimal state involvement':['minimal_state_market'],
                'State and market combined':['mixed_state_market'],'Planned economy':['planned_economy']}
            question='What should be the relationship between the state and the economy?'
        elif item=='ownership_policy':
            kind='nominal';groups={'Broad privatisation':['broad_privatisation'],
                'Privatise except efficient state firms':['privatise_except_efficient_state_firms'],
                'Retain state enterprises':['retain_state_firms'],'Nationalise private firms':['nationalise'],
                "Don't know / no answer":['dont_know_or_no_answer']}
            question='Which ownership policy should the state pursue?'
        else:raise ValueError(item)
        if 'dont_know' in responses:groups["Don't know"]=['dont_know']
        if 'no_answer' in responses:groups['No answer']=['no_answer']
        if kind=='nominal':note='All named options; published percentages of all respondents.'
        published('Monitoring',item,z,groups,kind,note,question)


def mon_full(filename,page,code,item,labels):
    """Reuse verified table alignment, expanding extraction to every row."""
    ROWS.clear();CELLS.clear()
    for i in range(len(labels)):
        mon(filename,page,code,len(labels),item,item,[i],'All categories')
    z=pd.DataFrame(CELLS).rename(columns={'response_position':'position'}).drop(columns=['survey','item','coefficient'])
    z['response']=z.position.map(dict(enumerate(labels,1)))
    return z


def monitoring_extra():
    negpos=['negative','rather_negative','rather_positive','positive','dont_know','no_answer']
    specs=[('mon2019.pdf',431,'dn7','accept_market_values',negpos),
           ('mon2020.pdf',534,'r3.9','enterprise_initiative',['negative','rather_negative','undecided','rather_positive','positive','no_answer']),
           ('mon2020.pdf',475,'d6.20','trust_state_managers',['negative','rather_negative','undecided','rather_positive','positive','no_answer']),
           ('monitoring-2021dlya-tipografii.pdf',642,'d6.8','trust_tax_authority',['negative','rather_negative','undecided','rather_positive','positive','no_answer']),
           ('monitoring-2021dlya-tipografii.pdf',647,'d6.22','trust_banks',['negative','rather_negative','undecided','rather_positive','positive','no_answer']),
           ('monitoring-2021dlya-tipografii.pdf',646,'d6.17','trust_unions',['negative','rather_negative','undecided','rather_positive','positive','no_answer'])]
    for f,p,c,item,labels in specs:
        z=mon_full(f,p,c,item,labels)
        positive,negative=('Trust','Distrust') if item.startswith('trust_') else ('Important','Not important') if item=='enterprise_initiative' else ('Accept','Reject')
        groups={positive:['rather_positive','positive'],negative:['negative','rather_negative']}
        if 'undecided' in labels:groups['Undecided']=['undecided']
        if 'dont_know' in labels:groups["Don't know"]=['dont_know']
        groups['No answer']=['no_answer']
        published('Monitoring',item,z,groups,note='Positive and negative categories combined; published percentages of all respondents.')
    z=mon_full('monitoring-2021dlya-tipografii.pdf',700,'r5','market_relations_natural',
               ['adapted','searching','not_adapting','dont_know','no_answer'])
    published('Monitoring','market_relations_natural',z,{
        'Adapted; markets feel natural':['adapted'],'Still finding a place in life':['searching'],
        'Not adapting; waiting for change':['not_adapting'],"Don't know":['dont_know'],'No answer':['no_answer']},
        'nominal','All options; blue highlights the response explicitly referring to market relations.',
        'How have you adapted to the current life situation?')
    # The five ordered answers are followed by a new 2020-only business-owner
    # option, then nonresponse. Preserve its absence in earlier waves as NA.
    f,p,c='mon2020.pdf',446,'a9'
    z=mon_full(f,p,c,'start_business',['no','rather_no','dont_know','rather_yes','yes'])
    text=page_text(f,p);info=source_info(f,True)
    tail=text.split('Вже маю власний бiзнес',1)[1].split('Середній бал',1)[0]
    owner=float(re.search(r'\d+[.,]\d+',tail).group().replace(',','.'))
    vals=[float(x.replace(',','.')) for x in re.findall(r'\d+[.,]\d+',tail.split('Не відповіли',1)[1])]
    years=sorted(z.year.unique());assert len(vals)==len(years)
    extra=[dict(year=y,response='no_answer',percent=v,source_question=c,pdf_page=p,**info) for y,v in zip(years,vals)]
    extra.append(dict(year=2020,response='already_owner',percent=owner,source_question=c,pdf_page=p,**info))
    z=pd.concat([z,pd.DataFrame(extra)],ignore_index=True)
    published('Monitoring','start_business',z,{'Yes':['yes','rather_yes'],'No':['no','rather_no'],
        "Don't know":['dont_know'],'Already owns a business':['already_owner'],'No answer':['no_answer']},
        note='Yes/no categories combined; “already owns a business” was offered only in 2020.')


def pew_full():
    filename='pew_2019_europe_topline.pdf'
    for item,page,code,labels in [
        ('transition_approval',35,'Q16a',['strongly_approve','approve','disapprove','strongly_disapprove','dont_know']),
        ('better_than_communism',37,'Q17',['better','worse','same','dont_know']),
        ('transition_ordinary',38,'Q20a',['great','fair','little','none','dont_know']),
        ('transition_business',38,'Q20b',['great','fair','little','none','dont_know']),
        ('transition_politicians',39,'Q20c',['great','fair','little','none','dont_know'])]:
        ROWS.clear();CELLS.clear()
        for i in range(len(labels)):
            pew(filename,page,code,item,item,'All categories',[i])
        z=pd.DataFrame(CELLS).drop(columns=['survey','item','coefficient'])
        z['response']=z.response_position.map(dict(enumerate(labels,1)))
        if item=='transition_approval':groups={'Approve':['strongly_approve','approve'],'Disapprove':['disapprove','strongly_disapprove']}
        elif item=='better_than_communism':groups={'Better':['better'],'Worse':['worse'],'About the same':['same']}
        else:groups={'Benefited substantially':['great','fair'],'Benefited little or not at all':['little','none']}
        groups["Don't know / refused"]=['dont_know']
        published('Pew',item,z,groups,note='Adjacent positive/negative categories combined; published percentages may round to 99–101%.')


def main():
    inv=eligible();microdata(inv);monitoring_existing(inv);monitoring_extra();pew_full()
    out=pd.concat([pd.DataFrame(ROWS_OUT),pd.read_csv(TABLES/'ess_question_trend_estimates.csv')],ignore_index=True)
    DEFINITIONS.extend(pd.read_csv(ROOT/'docs/ess_trend_definitions.csv').to_dict('records'))
    out=pd.concat([out,pd.read_csv(TABLES/'issp_question_trend_estimates.csv')],ignore_index=True)
    DEFINITIONS.extend(pd.read_csv(ROOT/'docs/issp_trend_definitions.csv').to_dict('records'))
    assert not out.duplicated(['survey','item','year','response']).any()
    expected=set(zip(inv.loc[inv.included,'survey'],inv.loc[inv.included,'chart_item']))
    assert set(zip(out.survey,out.item))==expected
    assert out[out.question_type.eq('numeric') & out.survey.isin(['WVS','EVS'])].estimate.between(1,10).all()
    assert out[out.question_type.eq('numeric') & out.survey.eq('ESS')].estimate.between(0,10).all()
    categories=out[~out.question_type.eq('numeric')]
    sums=categories.groupby(['survey','item','year']).estimate.sum()
    assert sums.between(98.5,101.5).all(),sums[~sums.between(98.5,101.5)]
    # Rounding tolerances reflect the source's displayed decimal precision.
    assert np.allclose(sums.loc[['WVS','EVS','ESS','ISSP']],100)
    means=pd.read_csv(TABLES/'extended_mean_estimates.csv');means=means[means.age_group.eq('All')]
    joined=out[out.response.eq('Mean')].merge(means,on=['survey','item','year'],suffixes=('_new','_old'))
    assert len(joined)>0 and np.allclose(joined.estimate_new,joined.estimate_old)
    out.to_csv(DEST,index=False,encoding='utf-8-sig')
    pd.DataFrame(TRACE).to_csv(TABLES/'question_trend_source_cells.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(DEFINITIONS).to_csv(ROOT/'docs/question_trend_definitions.csv',index=False,encoding='utf-8-sig')
    inv.to_csv(TABLES/'question_trend_selection.csv',index=False,encoding='utf-8-sig')
    counts=out[['survey','item','question_type']].drop_duplicates().question_type.value_counts().to_dict()
    status=dict(status='passed',charts=len(expected),question_types=counts,plotted_estimates=len(out),
        maximum_category_sum_rounding_error=float((sums-100).abs().max()),
        checks=['All eligible indicators mapped to complete questions','Every source option assigned exactly once',
                'Category shares sum to 100 within publication rounding','Existing numeric means reproduced',
                'Numeric special codes excluded and quantified','Unasked options remain absent, never zero'],
        multiple_answer_questions='None in the audited inventory meet both >=2 years and latest >=2019; crisis choices end in 2017 and business duties have only 2019.')
    (TABLES/'question_trend_validation.json').write_text(json.dumps(status,indent=2),encoding='utf8')
    print(json.dumps(status,indent=2))


if __name__=='__main__':main()
