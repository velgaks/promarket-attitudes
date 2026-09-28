"""Extract additional published economic-attitude cells from archived PDFs.

Cell coordinates are source question + PDF page + row + year, with source hash.
No unreported uncertainty is invented. Latest means latest verified question-wave.
"""
import hashlib,json,re
import fitz
import numpy as np
import pandas as pd
from analyze import ROOT,TABLES
from acquire import download
from monitoring_extract import page_text

ROWS=[];CELLS=[]
def source_info(filename,monitor=False):
    path=ROOT/'data/documentation'/('monitoring' if monitor else '')/filename
    manifest=ROOT/'data/source_manifests'/(filename+'.json')
    if not monitor:
        m=json.loads(manifest.read_text())
        if not path.exists():download(m['url'],m['path'],m['label'])
        url=m['url'];expected=m['sha256']
    else:
        s=pd.read_csv(ROOT/'docs/monitoring_sources.csv');r=s[s.local_path.str.endswith('/'+filename)].iloc[0]
        url=r.source_url
        if not path.exists():download(r.download_url,r.local_path,r.title)
        expected=json.loads(manifest.read_text())['sha256']
    digest=hashlib.sha256(path.read_bytes()).hexdigest();assert digest==expected,filename
    return dict(source_file=filename,source_url=url,source_sha256=digest)

def add(survey,item,year,question,rule,values,indices,filename,page,code,kind='Policy',monitor=False):
    info=source_info(filename,monitor);value=sum(values[i] for i in indices)
    assert 0<=value<=100,(item,year,value)
    ROWS.append(dict(survey=survey,item=item,year=year,question=question,positive_definition=rule,
        estimate=value,ci_low=np.nan,ci_high=np.nan,kind=kind,field=code,
        denominator='all respondents as published',**info,pdf_page=page,
        estimate_origin='published net' if rule.startswith('Published net') else 'sum of named published response cells'))
    for i in indices:CELLS.append(dict(survey=survey,item=item,year=year,source_question=code,
        response_position=i+1,percent=values[i],coefficient=1,**info,pdf_page=page))

def pew(filename,page,code,item,question,rule,indices,year=2014,kind='Policy',cee=False):
    info=source_info(filename);doc=fitz.open(ROOT/'data/documentation'/filename)
    text=doc[page-1].get_text(sort=True);doc.close()
    # Isolate one question even when two tables share a page.
    hit=re.search(r'\b'+re.escape(code)+r'(?:[. ]|$)',text);assert hit,(filename,page,code)
    block=text[hit.end():];nxt=re.search(r'\bQ\d+[a-z]?\b',block)
    if nxt:block=block[:nxt.start()]
    if cee:
        # Country label is vertically centred on the religion breakdown; use the
        # last General Population row BEFORE the Ukraine label, never Orthodox.
        prefix=block.split('Ukraine',1)[0]
        line=prefix[prefix.rfind('General Population'):].splitlines()[0]
        nums=[float(x) for x in re.findall(r'(?<!\w)\d+(?!\w)',line)]
        add('Pew',item,year,question,rule,nums,indices,filename,page,code,kind)
    else:
        lines=block.splitlines();start=next(i for i,l in enumerate(lines) if 'Ukraine' in l)
        chosen=[]
        for line in lines[start:]:
            m=re.search(r'(Spring|Fall|Summer),\s*(\d{4})\s*(?:--)?\s*(?:Total)?\s+([\d\s]+)$',line)
            if m:
                prefix=line[:m.start()].strip()
                if chosen and prefix and prefix!='Ukraine':break
                yr=int(m.group(2));nums=list(map(float,m.group(3).split()))
                assert nums[-1]==100 and abs(sum(nums[:-1])-100)<=4,(filename,code,nums)
                chosen.append((yr,nums[:-1]))
            elif chosen and re.search(r'[A-Za-z]',line):break
        assert chosen,(filename,page,code)
        for yr,nums in chosen:add('Pew',item,yr,question,rule,nums,indices,filename,page,code,kind)

def mon(filename,page,code,nrows,item,question,indices,rule,kind='Policy'):
    text=page_text(filename,page)
    marker=re.escape(code).replace('a','[aа]')
    hit=re.search(r'(?m)^\s*'+marker+r'(?:\.|\s)',text);assert hit,(filename,page,code)
    block=text[hit.end():];first=re.search(r'\d+[.,]\d+',block);assert first
    hs=list(re.finditer(r'(?<!\d)(?:19|20)\d{2}(?!\d)',block[:first.start()]));assert hs
    years=[int(h.group()) for h in hs]
    body=block[hs[-1].end():]
    vals=[float(x.replace(',','.')) for x in re.findall(r'(?<!\d)\d+[.,]\d+(?!\d)',body)]
    assert len(vals)>=nrows*len(years),(filename,page,code,len(vals))
    matrix=np.array(vals[:nrows*len(years)]).reshape(nrows,len(years))
    for j,yr in enumerate(years):add('Monitoring',item,yr,question,rule,matrix[:,j],indices,filename,page,code,kind,True)

def main():
    n='pew_2014_inequality.pdf'
    pew(n,36,'Q13a','free_market_better','Are most people better off in a free-market economy despite inequality?','Completely / mostly agree',[0,1])
    pew(n,39,'Q13b','success_outside_control','Is success largely determined by forces outside our control?','Completely / mostly agree',[0,1],kind='Belief')
    pew(n,48,'Q77b','low_tax_growth','Would low taxes on the wealthy and corporations reduce inequality by encouraging growth?','Choose low taxes',[1])
    pew(n,48,'Q77b','high_tax_redistribution','Would higher taxes on the wealthy and corporations reduce inequality by funding help for the poor?','Choose high taxes',[0])
    for page,code,label in [(44,'Q66a','education'),(44,'Q66b','hard work'),(45,'Q66c','knowing the right people'),
            (45,'Q66d','giving bribes'),(46,'Q66f','being from a wealthy family'),(47,'Q66g','luck')]:
        pew(n,page,code,'success_'+code,'Is '+label+' important for getting ahead?','6–10 on importance scale (0–10)',list(range(6,11)),kind='Belief')
    n='pew_2014_trade.pdf'
    for page,code,item,label,indices,rule in [
        (34,'Q27','trade_good','Are growing trade and business ties good for Ukraine?',[0,1],'Very / somewhat good'),
        (37,'Q28','trade_wages','Does trade increase workers’ wages?',[0],'Increase wages'),
        (38,'Q29','trade_jobs','Does trade create jobs?',[0],'Create jobs'),
        (39,'Q30','trade_prices','Does trade reduce prices?',[1],'Decrease prices'),
        (40,'Q31','foreign_acquisitions','Are foreign purchases of domestic companies good for the country?',[0,1],'Very / somewhat good'),
        (41,'Q32','foreign_factories','Are foreign companies building new factories good for the country?',[0,1],'Very / somewhat good')]:
        pew(n,page,code,item,label,rule,indices)
    n='pew_2015_cee_topline.pdf'
    pew(n,33,'Q16a','government_care_poor','Should government care for very poor people unable to care for themselves?','Published net agree',[0],2015,cee=True)
    pew(n,34,'Q16b','free_market_better','Are most people better off in a free-market economy despite inequality?','Published net agree',[0],2015,cee=True)
    pew(n,3,'Q3a','inequality_problem','Is the rich–poor gap a very big problem?','Very big problem',[0],2015,'Belief',True)
    n='pew_2011_soviet_topline.pdf'
    pew(n,4,'Q16a','success_ability','Do people get ahead through ability and ambition rather than at others’ expense?','Ability and ambition',[1],2011,'Belief')
    pew(n,4,'Q16b','failure_individual','Do people fail because of individual rather than societal failures?','Individual failures',[1],2011,'Belief')
    pew(n,11,'Q61','freedom_vs_welfare','Is freedom from state interference more important than guaranteeing nobody is in need?','Freedom from interference',[0],2011)
    pew(n,11,'Q61','welfare_vs_freedom','Is guaranteeing nobody is in need more important than freedom from state interference?','Nobody in need',[1],2011)
    pew('pew_2009_europe_topline.pdf',44,'Q40j','rich_richer','Are the rich getting richer while the poor get poorer?','Completely / mostly agree',[0,1],2009,'Belief')
    for page,code,item,label,inds in [(37,'Q17','better_than_communism','Is the economic situation better than under communism?',[0]),
        (38,'Q20a','transition_ordinary','Have ordinary people benefited from the post-1991 changes?',[0,1]),
        (38,'Q20b','transition_business','Have business people benefited from the post-1991 changes?',[0,1]),
        (39,'Q20c','transition_politicians','Have politicians benefited from the post-1991 changes?',[0,1])]:
        pew('pew_2019_europe_topline.pdf',page,code,item,label,'Better' if code=='Q17' else 'A great deal / a fair amount',inds,2019,'Transition assessment')
    # Monitoring: extract all columns from the latest cumulative table for each item.
    mon('mon2020.pdf',446,'a9',5,'start_business','Would you like to start your own business?',[3,4],'Yes / rather yes','Business orientation')
    mon('monitoring-2021dlya-tipografii.pdf',700,'r5',5,'market_relations_natural','Have you adapted to the new life and found market relations a natural way of living?',[0],'Select this description of adaptation','Business orientation')
    mon('mon2019.pdf',431,'dn7',6,'accept_market_values','Do you accept the post-independence values of private property, enrichment, individualism and personal success?',[2,3],'Definitely / rather yes','Business orientation')
    for item,inds,label in [('ownership_private',[3,4],'mainly or exclusively private ownership'),('ownership_mixed',[2],'a mix of state and private ownership'),('ownership_state',[0,1],'mainly or exclusively state ownership')]:
        mon('us-2015.pdf',10,'mm2',7,item,'Should Ukraine’s economy be based on '+label+'?',inds,'Choose named ownership structure')
    for i,label in enumerate(['small-business owners','large-business owners','landowners farming themselves','landowners hiring workers'],1):
        mon('mon2019.pdf',416,'em'+str(i),10,'respect_owners_'+str(i),'What feeling do '+label+' evoke?',[5],'Respect','Business orientation')
    for code,item,label in [('dc1','benefits_never','Is claiming state support to which one is not entitled never justified?'),('dc3','tax_never','Is not paying taxes when possible never justified?')]:
        mon('mon2019.pdf',446,code,6,item,label,[0],'Never justified','Economic norm')
    mon('mon2020.pdf',534,'r3.9',6,'enterprise_initiative','Is the opportunity for entrepreneurial initiative important?',[3,4],'Rather / very important','Business orientation')
    mon('mon2020.pdf',475,'d6.20',6,'trust_state_managers','Do you trust managers of state enterprises?',[3,4],'Mostly / completely trust','Institutional trust')
    mon('dodatki2015.pdf',25,'d6.21',6,'trust_private_entrepreneurs','Do you trust private entrepreneurs?',[3,4],'Mostly / completely trust','Institutional trust')
    mon('monitoring-2021dlya-tipografii.pdf',642,'d6.8',6,'trust_tax_authority','Do you trust the tax authority?',[3,4],'Mostly / completely trust','Institutional trust')
    mon('monitoring-2021dlya-tipografii.pdf',647,'d6.22',6,'trust_banks','Do you trust banks?',[3,4],'Mostly / completely trust','Institutional trust')
    # Union trust latest cumulative table is verified separately in the audit.
    mon('monitoring-2021dlya-tipografii.pdf',646,'d6.17',6,'trust_unions','Do you trust trade unions?',[3,4],'Mostly / completely trust','Institutional trust')
    for code,item,label in [('cnf1','rich_poor_conflict','rich and poor'),('cnf2','manager_worker_conflict','managers and subordinates'),('cnf3','owner_worker_conflict','employees and owners')]:
        mon('dodatki2017.pdf',39,code,6,item,'Is conflict between '+label+' acute?',[0,1],'Acute / very acute','Belief')
    remedies=['nationalise strategic private firms','privatise strategic state firms','raise taxes on big business',
        'increase economic cooperation with the West','increase economic cooperation with Russia','substantially raise industrial wages',
        'follow IMF reform recommendations','reject IMF reform recommendations','create jobs mainly in small and medium businesses',
        'create jobs mainly in large industrial firms','attract mainly foreign capital','use mainly domestic capital','allow agricultural land sales']
    for i,label in enumerate(remedies):
        mon('dodatki2017.pdf',7,'kr1',16,'crisis_'+str(i+1),'Which measures would end the crisis: '+label+'?',[i],'Selected (multiple answers allowed)')
    responsibilities=['pay taxes, invest and create jobs','improve working conditions','train employees','act responsibly towards the environment',
        'enter politics and govern','provide charity','sponsor culture and sport','finance solutions to regional problems']
    for i,label in enumerate(responsibilities):
        mon('mon2019.pdf',439,'rs6',11,'business_duty_'+str(i+1),'What should socially responsible business do: '+label+'?',[i],'Selected (up to three choices)','Economic norm')
    out=pd.DataFrame(ROWS);assert not out.duplicated(['survey','item','year']).any()
    pd.DataFrame(CELLS).to_csv(TABLES/'extended_published_trace.csv',index=False)
    out.to_csv(TABLES/'extended_published_shares.csv',index=False)
    print('Additional published rows:',len(out))

if __name__=='__main__':main()
