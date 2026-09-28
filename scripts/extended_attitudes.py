"""Audited additional economic attitudes and latest affirmative-response appendix.

Positive means endorsement of the named statement, not an ideological score.
Keep the original fixed-content four-item indices unchanged.
"""
import hashlib,json,re
import numpy as np
import pandas as pd
from analyze import ROOT,RAW,TABLES,read_selected,estimate,LITS,age_groups

DEFS=[]; RESULTS=[]; AVAIL=[]; SCAN=[]
def definition(survey,item,question,field,valid,positive,rule,kind='Policy',reverse=False,mean=False):
    row=dict(survey=survey,item=item,question=question,field=field,valid=list(valid),positive=list(positive),
             positive_definition=rule,kind=kind,reverse=reverse,mean=mean)
    DEFS.append(row);return row

def values_definitions(survey):
    def add(field,label,valid,pos,rule,kind='Policy',reverse=False,mean=False):
        return definition(survey,field,label,field,valid,pos,rule,kind,reverse,mean)
    ten=range(1,11);low=range(1,6);high=range(6,11)
    for field,label,pos in [('E036','Should private ownership of business increase?',low),
        ('E039','Is competition beneficial?',low),('E037','Should individuals take more responsibility for providing for themselves?',low),
        ('E035','Should income differences provide incentives for effort?',high),
        ('E038','Should unemployed people accept any available job?',low),
        ('E042','Should the state give firms more freedom?',low),
        ('E040','Does hard work bring a better life?',low),('E041','Can wealth grow so there is enough for everyone?',high)]:
        add(field,label,ten,pos,'Market-oriented half of the 1–10 scale',
            'Belief' if field in ['E040','E041'] else 'Policy',pos==low,True)
    for field,label in [('B001','Would you give part of your income to protect the environment?'),
        ('B002','Would you accept higher taxes to prevent environmental pollution?'),
        ('B003','Should government reduce pollution without costing you money?'),
        ('B006','Must environmental problems be accepted to combat unemployment?')]:
        add(field,label,range(1,5),[1,2],'Strongly agree / agree')
    add('B008','Should economic growth and jobs take priority over environmental protection?',range(1,4),[2],'Choose economic growth and jobs')
    add('C059','Is higher pay fair for a more efficient and reliable secretary?',[0,1],[1],'Fair','Belief')
    add('C060','Should owners run businesses or appoint their managers?',range(1,5),[1],'Choose owners / appointed managers')
    add('E062','Should foreign goods be freely imported?',range(1,4),[1],'Choose freely imported goods')
    add('E127','Is a free-market economy right for the country’s future?',[1,2],[1],'Right')
    add('E131','Is poverty due to laziness rather than unfair treatment?',range(1,4),[1],'Choose laziness / lack of willpower','Belief')
    add('E132','Do poor people have a chance to escape poverty?',range(1,4),[1],'Have a chance','Belief')
    add('E133','Is the government doing too little to fight poverty?',range(1,5),[3],'Too little')
    add('A209','Do older people receive more than their fair share from government?',range(1,5),[1,2],'Strongly agree / agree')
    add('E057','Does the economic system need fundamental changes?',range(1,6),[1,2],'Agree completely / somewhat')
    # These candidates must be checked even if the Ukrainian waves have no answers.
    add('E066','Should society become more competitive rather than egalitarian?',range(1,6),[4,5],'Second endpoint / somewhat closer to second')
    add('E067','Should society favour lower taxes rather than extensive welfare?',range(1,6),[4,5],'Second endpoint / somewhat closer to second')
    add('E203','Do rapid market reforms harm national stability?',range(1,5),[1,2],'Strongly agree / agree','Belief')
    add('E204','Would market reforms improve most people’s lives?',range(1,4),[2],'Improve lives','Belief')
    for field,label in [('E224','Is taxing the rich to subsidise the poor essential to democracy?'),
        ('E227','Is state aid for unemployment essential to democracy?'),
        ('E233A','Is state equalisation of incomes essential to democracy?')]:
        add(field,label,range(0,11),high,'6–10 on essential-to-democracy scale','Democracy concept')
    for field,label in [('E069_13','Do you have confidence in major companies?'),('E069_41','Do you have confidence in banks?'),
        ('E069_05','Do you have confidence in labour unions?'),('E069_09','Do you have confidence in the social security system?')]:
        add(field,label,range(1,5),[1,2],'A great deal / quite a lot','Institutional trust')
    for field,label in [('F114A','Is claiming benefits to which you are not entitled never justifiable?'),
        ('F116','Is cheating on taxes never justifiable?')]:
        add(field,label,ten,[1],'Never justifiable (1 of 10)','Economic norm')
    if survey=='EVS':add('F114','Is claiming government benefits never justifiable (earlier item)?',ten,[1],'Never justifiable (1 of 10)','Economic norm')

def lits_definitions(year):
    def add(item,field,label,valid,pos,rule,kind='Policy',reverse=False,mean=False):
        d=definition('LiTS',item,label,field,valid,pos,rule,kind,reverse,mean);d['only_year']=year
    ten=range(1,11);low=range(1,6);high=range(6,11)
    add('market','q411' if year==2016 else 'q310','Is a market economy preferable to any other economic system?',range(1,4),[1],'Market economy preferable')
    add('reduce_gap',{2006:'q301_10',2010:'q301h',2016:'q401h'}[year],'Should the gap between rich and poor be reduced?',range(1,6),[4,5],'Agree / strongly agree')
    if year>=2010:
        pre='q316' if year==2010 else 'q417'
        for s,item,label,pos in [('a','income_incentives','Should larger income differences reward individual effort?',high),
            ('b','private_ownership','Should private ownership of business increase?',low),('c','competition','Is competition beneficial?',low)]:
            add(item,pre+s,label,ten,pos,'Market-oriented half of the 1–10 scale',reverse=pos==low,mean=True)
        for s,label in [('a','public education'),('b','public health'),('c','combating climate change'),('d','helping people in need')]:
            add('pay_'+s,('q306' if year==2010 else 'q407')+s,'Would you give income or pay more taxes for '+label+'?',[1,2],[1],'Yes')
        for n,label in enumerate(['elderly people','people with disabilities','war veterans','families with children','the working poor','unemployed people','nobody']):
            fld='q408'+chr(97+n) if year==2016 else 'q307a_'+('10' if n==6 else f'{n+1:02d}')
            add('support_'+str(n+1),fld,'Who deserves government support: '+label+'?',[0,1],[1],'Selected; all respondents with recorded checkbox')
    if year==2006:
        for n,label in enumerate(['reduce inequality','guarantee employment','keep electricity and gas prices low','keep basic food prices low','own public utilities','own large companies'],1):
            add('state_'+str(n),'q305_'+str(n),'Should the state '+label+'?',[1,2,3],[2,3],'Moderate or strong state involvement')
        for item,pos,label in [('keep_private',[1,2],'Should privatised firms remain with current owners (possibly after additional payment)?'),
            ('nationalise',[3],'Should privatised firms return permanently to state ownership?'),
            ('reprivatise',[4],'Should privatised firms be nationalised and then re-privatised?')]:
            add(item,'q309',label,range(1,5),pos,'Choose named option(s)')
    if year==2016:
        add('wealth_influence','q417f','Are stricter rules needed against wealthy people’s influence on government?',ten,high,'6–10: stricter-rules half of scale')
        add('corporate_donations','q417g','Should corporate funding of political parties and candidates be banned?',ten,low,'1–5: ban-funding half of scale')
        add('inequality_increased','q421','Has the gap between rich and poor increased?',range(1,4),[2],'Became larger','Belief')
        for suffix,label in [('a','a government job'),('b','a private-sector job'),('d','permits or official papers')]:
            add('connections_'+suffix,'q425'+suffix,'Are connections important for obtaining '+label+'?',range(1,6),[4,5],'Very important / essential','Belief')
    trustfields={2006:['q303_8','q303_9','q303_11'],2010:['q303j','q303k','q303m'],2016:['q404j','q404k','q404m']}[year]
    for item,f,label in zip(['banks','foreign_investors','unions'],trustfields,['banks and the financial system','foreign investors','trade unions']):
        add('trust_'+item,f,'Do you trust '+label+'?',range(1,6),[4,5],'Some / complete trust','Institutional trust')
    success={2006:'q306',2010:'q308',2016:'q409'}[year]
    success_valid=list(range(1,5))+[98]+list(range(101,107)) if year==2006 else list(range(1,6))
    add('success_effort',success,'What matters most for success: effort and hard work?',success_valid,[1],'Choose effort and hard work','Belief')
    add('success_skill',success,'What matters most for success: intelligence and skills?',success_valid,[2],'Choose intelligence and skills','Belief')
    poverty={2006:'q308',2010:'q309',2016:'q410'}[year]
    for n,label in [(1,'bad luck'),(2,'laziness and lack of willpower'),(3,'injustice in society'),(4,'an inevitable part of modern life')]:
        add('poverty_'+str(n),poverty,'Why are some people poor: '+label+'?',range(1,6),[n],'Choose named explanation','Belief')
    priorities=['education','health','housing','pensions']+([] if year==2006 else ['helping the poor'])+['the environment','public infrastructure']
    fld={2006:'q304a',2010:'q305_1',2016:'q406a'}[year]
    for n,label in enumerate(priorities,1):
        valid=list(range(1,7))+[98]+list(range(100,129)) if year==2006 else list(range(1,9))
        add('spend_'+label.replace(' ','_'),fld,'First priority for extra government spending: '+label+'?',valid,[n],'First priority selected','Spending priority')

def process(d,defs,survey,year,meta,source,weight):
    for spec in defs:
        f=spec['field'];raw=d[f] if f in d else pd.Series(np.nan,index=d.index)
        valid=raw.isin(spec['valid']);n=int(valid.sum())
        available=dict(survey=survey,year=year,item=spec['item'],field=f,n_valid=n,
            status='included' if n else 'no valid Ukrainian responses',source_file=source,
            question=spec['question'],source_label=meta.column_names_to_labels.get(f,''))
        AVAIL.append(available)
        if not n:continue
        z=raw.isin(spec['positive']).astype(float).mul(100).where(valid)
        res=estimate(d,z,bounds=(0,100));unw=estimate(d,z,weighted=False,bounds=(0,100))
        RESULTS.append(dict(survey=survey,year=year,item=spec['item'],question=spec['question'],
            positive_definition=spec['positive_definition'],kind=spec['kind'],field=f,
            valid_codes=json.dumps(spec['valid']),positive_codes=json.dumps(spec['positive']),
            source_label=meta.column_names_to_labels.get(f,''),
            source_value_labels=json.dumps(meta.variable_value_labels.get(f,{}),ensure_ascii=False),
            source_file=source,weight_variable=weight,denominator='valid substantive responses',
            missing_weighted_pct=100*(1-d.loc[valid,'weight'].sum()/d.weight.sum()),
            unweighted_estimate=unw['estimate'],**res))
        if spec['mean']:
            y=raw.where(valid);y=11-y if spec['reverse'] else y
            for group,domain in [('All',None)]+[(g,d.age_group.eq(g)) for g in ['18-34','35-54','55+']]:
                mean=estimate(d,y,domain=domain,bounds=(1,10))
                if mean:MEANS.append(dict(survey=survey,year=year,item=spec['item'],age_group=group,**mean))

MEANS=[]
def check_original(filename):
    expected=json.loads((ROOT/'data/source_manifests'/(filename+'.json')).read_text())['sha256']
    with (RAW/filename).open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
    assert actual==expected,'Source version changed: '+filename

def main():
    for survey,filename in [('WVS','WVS_Time_Series_1981-2022_spss_v5_0.sav'),('EVS','ZA7503_v3-0-0.sav')]:
        check_original(filename)
        values_definitions(survey);defs=[x for x in DEFS if x['survey']==survey]
        fields=['S001','S003','S020','S017','X003']+[x['field'] for x in defs]
        d,meta=read_selected(RAW/filename,fields);d.columns=d.columns.str.upper()
        d=d[d.S003.eq(804)&d.X003.ge(18)&d.S017.gt(0)&np.isfinite(d.S017)].copy()
        assert d.S001.eq(2 if survey=='WVS' else 1).all()
        d['weight']=d.S017;d['psu']=d.index.astype(str);d['age_group']=age_groups(d.X003)
        d['variance_method']='Weighted respondent linearization; approximate'
        for year,z in d.groupby('S020'):process(z,defs,survey,int(year),meta,filename,'S017')
        included={x['field'] for x in defs}
        for f,label in meta.column_names_to_labels.items():
            if re.search(r'privat|state|govern|market|competi|equal|wealth|poor|poverty|tax|firms|business|unemploy|benefit|bank|union|social security',str(label),re.I):
                SCAN.append(dict(survey=survey,field=f,label=label,decision='audited availability' if f in included else 'outside defined scope / review catalogue',source_file=filename))
        print(survey,'extended estimates done',flush=True)
    for year,filename,country,age,item,weight,psu,region,respondent in LITS:
        check_original(filename)
        lits_definitions(year);defs=[x for x in DEFS if x.get('only_year')==year]
        d,meta=read_selected(RAW/filename,[country,age,weight,psu]+[x['field'] for x in defs])
        d=d[d[country].astype(str).str.lower().eq('ukraine')&d[age].ge(18)&d[weight].gt(0)&np.isfinite(d[weight])].copy()
        d['weight']=d[weight];d['psu']=d[psu].astype(str);d['age_group']=age_groups(d[age])
        d['variance_method']='PSU linearization; no explicit strata; approximate'
        process(d,defs,'LiTS',year,meta,filename,weight)
        for f,label in meta.column_names_to_labels.items():
            if re.search(r'privat|state|govern|market|competi|equal|wealth|poor|poverty|tax|firms|business|unemploy|benefit|bank|union',str(label),re.I):
                SCAN.append(dict(survey='LiTS',field=f,label=label,decision='audited availability' if f in {x['field'] for x in defs} else 'outside defined scope / review catalogue',source_file=filename))
    pd.DataFrame(RESULTS).to_csv(TABLES/'extended_microdata_shares.csv',index=False)
    pd.DataFrame(MEANS).to_csv(TABLES/'extended_mean_estimates.csv',index=False)
    pd.DataFrame(AVAIL).to_csv(ROOT/'docs/extended_question_availability.csv',index=False)
    pd.DataFrame(DEFS).to_csv(ROOT/'docs/extended_question_definitions.csv',index=False)
    pd.DataFrame(SCAN).to_csv(ROOT/'docs/economic_variable_search_catalogue.csv',index=False)
    print('Extended microdata share rows:',len(RESULTS))

if __name__=='__main__':main()
