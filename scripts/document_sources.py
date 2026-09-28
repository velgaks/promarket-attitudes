"""Generate machine-readable source inventory and audited question crosswalk."""
from pathlib import Path
import json
import pandas as pd
from analyze import ROOT,DIMENSIONS

def main():
    verify_path=ROOT/'data/source_manifests/values_verification.json'
    verified=json.loads(verify_path.read_text()) if verify_path.exists() else {}
    rows=[];inventory=[]
    endpoints={
        'E036':('more private ownership of business/industry','more state/government ownership of business/industry'),
        'E039':('competition beneficial: hard work and new ideas','competition harmful: brings out the worst in people'),
        'E037':('individuals responsible for providing for themselves','state/government responsible for ensuring provision'),
        'E035':('make incomes more equal','greater incentives for effort (EVS); larger income differences as incentives (WVS)')}
    for survey,years in [('WVS',[1996,2006,2011,2020]),('EVS',[1999,2008,2020])]:
        v=verified.get(survey,{})
        for year in years:
            inventory.append(dict(survey=survey,fieldwork_year=year,microdata_verified=bool(v.get('crosswalk_verified')),
                                  source_file='ZA7503_v3-0-0.sav' if survey=='EVS' else v.get('source_file','WVS TimeSeries, see source manifest'),
                                  age='X003 >=18',weight='S017',survey_identity='S001=1' if survey=='EVS' else 'S001=2',
                                  psu='not supplied in verified trend-file fields; respondent-level intervals approximate',
                                  geography=v.get('regions',{}).get(str(year),'not verified'),
                                  territorial_coverage=v.get('coverage',{}).get(str(year),'See geographic labels and sample audit'),
                                  geographic_limit=v.get('geography_limits',{}).get(str(year),'')))
            for code,(item,rev) in DIMENSIONS.items():
                rule=v.get('items',{}).get(f'{year}:{code}')
                low,high=endpoints[code]
                if survey=='WVS' and year==2020 and code=='E039':
                    low,high='competition is good','competition is harmful'
                rows.append(dict(survey=survey,year=year,item=item,source_variable=code,
                    questionnaire_question=v.get('question_ids',{}).get(str(year),{}).get(code,''),
                    question_wording_summary='Place own views on a ten-point scale between opposite positions',
                    wording_status='Endpoint descriptions paraphrased; see linked source for exact master wording',
                    raw_1=low,raw_10=high,valid_codes='integers 1 through 10',
                    raw_refers_to='Harmonised trend-file variable, not original questionnaire position',
                    questionnaire_low=('government responsibility for provision' if survey=='WVS' and code=='E037' else low),
                    questionnaire_high=('individual responsibility for provision' if survey=='WVS' and code=='E037' else high),
                    questionnaire_source=v.get('questionnaire_sources',{}).get(str(year),'https://access.gesis.org/dbk/71022'),
                    analysis_coding='11 - raw' if rule=='reverse' else 'raw' if rule=='as_is' else 'pending',
                    high_analysis_value_means=item,missing='all values outside 1..10; distinguish -1 DK, -2 no answer, -3 NA, -4 not asked, -5 other',
                    weight='S017',age='X003',psu='unavailable; do not substitute interviewer IDs',
                    geography=v.get('regions',{}).get(str(year),'not verified'),
                    comparability_status='verified within programme' if rule in ['reverse','as_is'] else rule or 'pending microdata and questionnaire',
                    caveat=('WVS wave7 competition endpoints shortened to good/harmful; shared construct, wording continuity qualified. ' if survey=='WVS' and year==2020 and code=='E039' else '')+'Keep survey identity; incentive wording differs across programmes; original country-language forms not all independently verified; translation/mode effects unresolved',
                    source='https://access.gesis.org/dbk/71022' if survey=='EVS' else 'https://www.worldvaluessurvey.org/WVSDocumentationWVL.jsp',
                    evidence=v.get('evidence','pending')))
    for year,item,age,weight,psu,geo,question,file in [
        (2006,'q310','ageB','weight_0','tabled','unlabelled region; sensitivity unavailable','Q3.10','LITS-2006-data.dta'),
        (2010,'q310','respondentage','weight','psu','Region1','Q3.10','lits2.dta'),
        (2016,'q411','age_pr','weight_population','PSU_number','region_name','Q4.11','lits_iii.dta')]:
        inventory.append(dict(survey='LiTS',fieldwork_year=year,microdata_verified=True,source_file=file,
                              age=f'{age} >=18',weight=weight,survey_identity='Ukraine country string',
                              psu=psu,geography=geo))
        rows.append(dict(survey='LiTS',year=year,item='market',source_variable=item,questionnaire_question=question,
            question_wording_summary='Select the economic-system statement closest to own view',
            wording_status='Statements paraphrased; see master questionnaire question reference',
            raw_1='market economy preferable to other economic systems',raw_2='planned economy sometimes preferable to market economy',
            raw_3='for people like me the economic system does not matter',valid_codes='1, 2, 3',
            analysis_coding='category retained; market share = weighted mean of indicator(raw=1)',
            high_analysis_value_means='not ordinal; no mean of categories',missing='system missing (2006); -97 do not know (2010,2016); all other values excluded',
            weight=weight,age=age,psu=psu,geography=geo,
            comparability_status='same response-choice construct; territory changes; 2006 common-territory comparison unresolved',
            caveat='Do not combine with WVS/EVS dimension scores; 2010-16 localities partly revisited but respondents are repeated cross-sections',
            source='https://www.ebrd.com/home/what-we-do/office-of-the-chief-economist/lits/life-in-transition-survey-data.html',
            evidence=f'Official master {question}; original Stata value labels and Ukrainian response frequencies; 2016 published rounded shares reproduced'))
    pd.DataFrame(rows).to_csv(ROOT/'docs/question_crosswalk.csv',index=False)
    pd.DataFrame(inventory).to_csv(ROOT/'docs/survey_inventory.csv',index=False)
    print('Wrote survey inventory and question crosswalk.')

if __name__=='__main__':main()
