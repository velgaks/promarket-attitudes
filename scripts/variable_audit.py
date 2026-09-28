"""Document the bounded questionnaire audit, including excluded near-matches."""
import re,json
import pandas as pd
import fitz
from analyze import ROOT,TABLES
from monitoring_extract import fix_encoding

def main():
    # Search all pages rather than only appendices; retain original headings.
    hits=[]
    for f in sorted((ROOT/'data/documentation/monitoring').glob('*.pdf')):
        with fitz.open(f) as doc:
            for i,page in enumerate(doc):
                text=fix_encoding(page.get_text())
                for m in re.finditer(r'(?m)^\s*([a-zа]{1,3}\d+(?:\.\d+)?[a-z]?)\.?\s+([^\n]+)',text):
                    rest=text[m.end():];first=re.search(r'\d+[.,]\d+',rest)
                    if not first:continue
                    head=text[m.start():m.end()]+rest[:first.start()]
                    if len(head)>1300:continue
                    if re.search('приват|підприєм|пiдприєм|ринк|бізнес|бiзнес|подат|капітал|капiтал|власн|нерів|нерiв|держав.*економ',head,re.I):
                        hits.append(dict(file=f.name,page=i+1,code=m.group(1),heading=re.sub(r'\s+',' ',head)[:700]))
    mon=pd.DataFrame(hits)
    included={'a2','a3','a4','a5','a6','a7','a8','a9','b2','an11','an12','mm2','dn7','kr1','rs6','r3.9','r5',
              'd6.8','d6.17','d6.20','d6.21','d6.22','dc1','dc3','cnf1','cnf2','cnf3','em1','em2','em3','em4'}
    def mondecision(code):
        code=code.replace('а','a')
        if code in included or re.fullmatch(r'(an[1-9]|a(?:[3-9]|1[012])r)',code):return 'Included topic; latest verified table used'
        if code in ['md2','bn3']:return 'Excluded: general institutional performance / modernisation, not desired economic policy'
        if code in ['n6','n7','n19','n40','k1a','k2','es5','st1m']:return 'Excluded: personal circumstances / reported behaviour'
        return 'Excluded: other social/political topics or keyword near-match; see heading'
    mon['decision']=mon.code.map(mondecision)
    mon.to_csv(ROOT/'docs/monitoring_economic_question_search.csv',index=False,encoding='utf-8-sig')
    micro=pd.read_csv(ROOT/'docs/economic_variable_search_catalogue.csv')
    availability=pd.read_csv(ROOT/'docs/extended_question_availability.csv')
    def decision(r):
        a=availability[availability.survey.eq(r.survey)&availability.source_file.eq(r.source_file)&availability.field.eq(r.field)]
        if len(a):return 'Included' if a.n_valid.gt(0).any() else 'Not available: no valid Ukrainian responses'
        if r.field.startswith('E129') or r.field in ['E069_63','E242','E247']:return 'Excluded: international aid / supranational institution / global policy priority'
        if r.field in ['q305_2','q406b','q408_important']:return 'Excluded duplicate topic: rank detail; first spending priority and support for each beneficiary retained'
        if r.field=='q408_97':return 'Nonresponse indicator, not an attitude'
        if re.search('corrupt|satisf|performance|change/no change',str(r.label),re.I):return 'Excluded: institutional performance, corruption experience or explanation of an observation'
        if re.search('member|voluntary|income from|received|requested|holding|owns|ownership, job|tried|primary respondent|secondary respondent',str(r.label),re.I):return 'Excluded: membership, behaviour or personal circumstances'
        return 'Excluded: general politics, identity, religion, gender, migration or other non-economic attitude; original label retained'
    micro['decision']=micro.apply(decision,axis=1)
    micro.to_csv(ROOT/'docs/economic_variable_search_catalogue.csv',index=False,encoding='utf-8-sig')
    latest=pd.read_csv(TABLES/'latest_positive_shares.csv')
    counts=latest.groupby('survey').size().to_dict()
    text=f'''# Audit of market and state-in-the-economy questions

Completed 28 September 2026. **The original selection was incomplete.** The expanded appendix now contains {len(latest)} indicators or named response options: WVS {counts['WVS']}, EVS {counts['EVS']}, LiTS {counts['LiTS']}, Pew {counts['Pew']} Monitoring {counts['Monitoring']} ESS {counts['ESS']} and ISSP {counts['ISSP']}. Multiple options from one question are separate rows; these counts are not counts of independent questionnaire items.

## Inclusion rule

Include economic-system choice, ownership, competition, redistribution, provision, business regulation, trade/investment, desired state intervention, public-spending priorities, and willingness to finance public provision. Also include related economic beliefs (merit, poverty and inequality), trust in economic institutions, economic moral norms and orientation towards private business. Keep these meanings explicit. A high affirmative percentage is not necessarily pro-market. Questions about what democracy entails are concepts of democracy, not direct policy approval.

Retain the four fixed WVS/EVS index components and the existing separately defined LiTS/Monitoring indicators. Do not add variable-content items to the historical indices. The latest appendix describes each variable at its own latest verified year; it does not restrict all rows to the latest overall wave. Latest dates can therefore differ even within a survey.

## What the review added

| Programme | Reviewed source and years | Additions |
|---|---|---|
| WVS | WVS-only time-series SPSS v5.0; all Ukrainian waves 1996, 2006, 2011, 2020; source labels and questionnaire/codebook definitions | Hard work, wealth creation, pay fairness, management by owners, imports, free-market future, poverty and government response, elderly transfers, environmental funding/trade-offs, economic institutions, benefit/tax morality, welfare-related concepts of democracy. |
| EVS | ZA7503 v3.0.0; Ukraine 1999, 2008, 2020; harmonised codebook | Freedom for firms, unemployment benefit conditionality, pay fairness, environmental funding/trade-offs, companies/unions/social security, benefit/tax morality, welfare-related concepts of democracy. Earlier benefit wording is kept as its own item. |
| LiTS | Original 2006, 2010, 2016 microdata and all three questionnaires | Three economic scales in 2010/2016; inequality reduction; 2006 state involvement and renationalisation; public-service funding; deserving beneficiaries; spending priorities; wealthy influence/corporate political finance; merit/poverty beliefs; connections; trust in banks, foreign investors and unions. |
| Pew | 2009 Europe, 2011 former Soviet Union, 2014 inequality and trade, 2015 CEE and 2019 Europe public toplines, including historical rows | Free-market benefit, state safety net, high/low-tax solutions, trade and foreign investment, merit/failure, inequality, and who benefited from transition. |
| Monitoring | All {len(list((ROOT/'data/documentation/monitoring').glob('*.pdf')))} acquired PDFs searched; cumulative tables and special modules through 2025 | Preferred ownership mix, business intentions/values, respect for owners, business duties, crisis measures (including tax and IMF options), entrepreneurship, market adaptation, class conflict, economic-institution trust and benefit/tax morality. |

## ESS addition

The supplied ESS files were audited separately: 47 economic attitudes and related beliefs across rounds 2–6, 10 and 11, covering actual fieldwork in 2005, 2006–07, 2009, 2011, 2013, 2022 and 2024. See `ess_variable_audit.md` for the question-by-question inventory and `docs/ess_question_crosswalk.csv` for wording, response codes and missingness. The 2022 file is the Ukrainian related study using the ESS10 questionnaire. Six questions meet the HTML rule of at least two observations and a latest observation from 2019 onward.

ESS adds redistribution, welfare responsibilities and consequences, incentives/fairness, taxes and benefit allocation, economic morality and business beliefs, and labour regulation. Immigration's economic effect and assessments of actual government provision are explicitly marked as related beliefs/evaluations, not direct preferences for markets. General satisfaction with the economy, left/right identity, income/employment circumstances, COVID-specific trade-offs and broad personal values are outside this economic-policy selection. No private-ownership/competition series was found in the supplied Ukrainian ESS waves.

## Inclusion and availability files

- `docs/extended_question_availability.csv`: every tested microdata question-wave, including zero-valid-response candidates. A variable existing in a multinational file is not evidence it was asked in Ukraine.
- `docs/extended_question_definitions.csv`: selected response codes, valid codes, scale direction and English question descriptions.
- `docs/economic_variable_search_catalogue.csv`: economic-keyword candidates in the full dictionaries, with inclusion/exclusion decisions. Non-keyword candidates selected by the questionnaire review appear in the definitions/availability files.
- `docs/monitoring_economic_question_search.csv`: {len(mon)} matching question headings and source pages from the acquired archive, including excluded near-matches.
- `output/tables/extended_microdata_shares.csv`: all verified question-waves, valid counts, weighted missingness, weighted/unweighted results and approximate 95% intervals.
- `output/tables/extended_published_shares.csv` and `extended_published_trace.csv`: additional published indicators and every source cell used, with source SHA-256, page, question and URL.
- `output/tables/latest_positive_shares.csv`: one latest row per indicator/survey, including its source table and denominator. The compact copy contains the requested question, survey, year and share plus the affirmative-response definition.

## ISSP addition

ISSP adds 59 questions across Ukraine’s 2008, 2009 and 2019 releases: 49 appear in the latest affirmative appendix and 10 monetary questions in a separate latest-means table. Thirty-six have comparable observations in 2009 and 2019 and enter the HTML. See `issp_variable_audit.md` and `docs/issp_question_crosswalk.csv`. The Ukraine 2019 national file is ZA7810, not the integrated ZA7600 file. All 851 fields in the three acquired releases are catalogued; inclusion requires valid Ukrainian responses.

The ISSP extension includes economic aspects of cross-border redistribution and labour mobility, inequality explanations, and perceived barriers to advancement. It does not treat nationality, religion or gender identity themselves as market preferences. These explicitly named economic extensions broaden the earlier domestic-policy audit; their levels are not added to a universal pro-market index.

## Important coding decisions

1. WVS/EVS ten-point economic items count the five categories on the named side. This is a transparent dichotomisation for the appendix only; charts retain full-scale means. Original positive codes are exported. For LiTS q316/q417, income incentives are 6–10, private ownership and beneficial competition 1–5. Source questionnaire locations: LiTS II PDF p.10 and LiTS III PDF p.24.
2. Agree/strongly agree, trust/complete trust and yes/rather yes are combined only where those response labels exist. The Monitoring emotions item counts **respect**, not interest or sympathy. It is labelled respect rather than general approval.
3. WVS/EVS/LiTS appendix percentages use valid substantive answers and survey weights. ESS/ISSP appendix percentages retain nonresponse in the all-adult denominator. Checkbox variables use all respondents with a recorded 0/1 checkbox, including those choosing a separate don't-know option. Published shares retain their all-respondent denominator. No binomial intervals are reconstructed from rounded tables.
4. Pew CEE uses the **General Population** row, not its nearby Orthodox subgroup row. Its published free-market NET agree is **47%**, although the separately rounded agreement categories sum to 48%. The extractor takes the published net. The Ukrainian fieldwork was **3–29 July 2015**, not the 2017 publication date; see the [report, PDF p.176](https://www.pewresearch.org/wp-content/uploads/sites/20/2017/05/CEUP-FULL-REPORT.pdf#page=176).
5. Monitoring trust in private entrepreneurs ends at the verified 2015 table; banks, unions and tax authority extend to 2021. Starting a business uses yes/rather yes, without adding those already operating a business. The older business approval question remains separate.
6. The LiTS first-priority spending question represents that topic; second-priority rankings and the most-important-beneficiary follow-up are not treated as additional independent attitudes. Historical success-before-1989 questions are not mixed with current success beliefs.

## Exclusions

Personal income, ownership, employment, business starts, banking access and receipt of benefits are circumstances or behaviour. General economic satisfaction, service performance and experienced corruption measure evaluations or experiences rather than desired institutions. General political trust, political identity, demographic identities and religious beliefs remain outside the scope. Specific economic implications of migration, international redistribution and discrimination are retained in the ESS/ISSP extensions where explicitly listed. Monitoring modernisation institutions (md2), government performance (bn3), ideological labels and general life aspirations are not assigned pro-market scores. The search catalogues retain relevant near-matches and their original labels.

## Limitations

The microdata audit covers the acquired WVS/EVS trend files and LiTS I–III. It does not certify every country-specific item outside those releases. The public-table audit covers the listed Pew publications and acquired Monitoring archive; it cannot certify all historical Pew releases or unpublished Monitoring questions. Latest means latest verified observation in that scope. Monitoring header search is text-based and is an aid to the questionnaire review, not proof that an unlocated question never existed.

Territory and methods change across years. In particular Pew CEE 2015 excludes Crimea and all Donetsk/Luhansk; the 2014 survey and later Pew Global Attitudes samples have different coverage. New national means are supplementary comparisons on each wave's survey territory. Published Monitoring/Pew tables cannot supply constant-territory re-estimates or the study's exact age bands. Same-year levels can be compared across surveys with their question and denominator differences explicit.

## Reproduction

Run `python scripts/run.py`. The additional stages are `extended_attitudes.py`, `extended_published.py`, `latest_appendix.py` and `variable_audit.py`. Original microdata remain local. Missing published PDFs are reacquired from their source manifests and checksums checked. Published-net/response-cell arithmetic, unique question-years, valid ranges, interval bounds, availability coverage and every note number are checked by the pipeline.
'''
    (ROOT/'output/variable_audit.md').write_text(text,encoding='utf8')
    print('Wrote variable audit and source search catalogues')

if __name__=='__main__':main()
