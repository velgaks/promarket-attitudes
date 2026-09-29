"""Source-backed wording for the trend gallery, separate from statistical coding.

Chart headings are English summaries/translations, never represented as verbatim
national questionnaires. The audit retains source wording, original categories,
the plotted grouping, and the precise limits of national-language verification.
Run this file to rebuild docs/chart_wording_audit.csv from the source documents.
"""
import hashlib
import json
import re
from functools import lru_cache

import pandas as pd
import pymupdf

from analyze import ROOT

AUDIT = ROOT / 'docs/chart_wording_audit.csv'
SOURCE_LINK = 'https://github.com/velgaks/promarket-attitudes/blob/main/docs/SOURCES.md'
WVS_UA = 'https://ucep.org.ua/wp-content/uploads/2020/11/WVS_UA_2020_report_WEB.pdf'
PEW = 'https://www.pewresearch.org/global/wp-content/uploads/sites/2/2019/10/Pew-Research-Center-Value-of-Europe-Topline-for-Release-FINAL.pdf'


def norm(s):
    return ' '.join(str(s).split())


@lru_cache(None)
def pdf_pages(relative):
    with pymupdf.open(ROOT / relative) as d:
        return [p.get_text() for p in d]


def reference(path, pages, years, url, level, excerpt=''):
    p = ROOT / path
    return dict(file=path, pdf_pages=pages, years=years, url=url,
                verification=level, excerpt=norm(excerpt),
                sha256=hashlib.sha256(p.read_bytes()).hexdigest())


def source_url(filename):
    p = ROOT / 'data/source_manifests' / (filename + '.json')
    return json.loads(p.read_text())['url'] if p.exists() else SOURCE_LINK


def rename(groups, mapping):
    return {mapping.get(label, label): codes for label, codes in groups.items()}


VALUES = {
    'E035': ('Income equality versus incentives for individual effort',
             'Income equality versus incentives',
             '1 = incomes more equal; 10 = greater incentives for individual effort'),
    'E036': ('Should private or state ownership of business and industry be increased?',
             'Preference for increasing private ownership',
             '1 = increase state ownership; 10 = increase private ownership (business and industry)'),
    'E037': ('Should government ensure everyone is provided for, or should people provide for themselves?',
             'Individual versus government responsibility for provision',
             '1 = government ensures everyone is provided for; 10 = people provide for themselves'),
    'E038': ('Must unemployed people accept any available job or lose benefits, or may they refuse unwanted jobs?',
             'Accept any job or lose unemployment benefits',
             '1 = right to refuse an unwanted job; 10 = take any available job or lose unemployment benefits'),
    'E039': ('Is competition good because it encourages hard work and new ideas, or harmful because it brings out the worst?',
             'Competition: good versus harmful',
             '1 = harmful: brings out the worst; 10 = good: encourages hard work and new ideas'),
    'E040': ('Does hard work bring a better life in the long run, or does success depend more on luck and connections?',
             'Hard work versus luck and connections',
             '1 = success depends more on luck and connections; 10 = hard work brings a better life in the long run'),
    'E224': ('How essential to democracy is it that governments tax the rich and subsidise the poor?',
             'Taxing the rich and subsidising the poor as a feature of democracy',
             '1 = not an essential characteristic of democracy; 10 = an essential characteristic'),
    'E227': ('How essential to democracy is it that people receive state aid for unemployment?',
             'Unemployment aid as a feature of democracy',
             '1 = not an essential characteristic of democracy; 10 = an essential characteristic'),
    'E233A': ('How essential to democracy is it that the state makes people’s incomes equal?',
             'Equalising incomes as a feature of democracy',
             '1 = not an essential characteristic of democracy; 10 = an essential characteristic'),
    'F116': ('How justifiable is cheating on taxes if you have the chance?',
             'Rejection of cheating on taxes',
             '1 = always justifiable; 10 = never justifiable (original scale reversed)'),
    'F114A': ('How justifiable is claiming government benefits to which you are not entitled?',
             'Rejection of unjustified benefit claims',
             '1 = always justifiable; 10 = never justifiable (original scale reversed)'),
}

# These are questionnaire endpoints. Trend-file E037 is already harmonised in
# the opposite direction to the WVS master, before the chart's 11-x reversal.
ENDPOINTS = {
    'E035': ['Incomes should be made more equal', 'There should be greater incentives for individual effort'],
    'E036': ['Private ownership of business and industry should be increased', 'Government ownership of business and industry should be increased'],
    'E037': ['People should take more responsibility for providing for themselves', 'The government should take more responsibility to ensure that everyone is provided for'],
    'E038': ['People who are unemployed should have to take any job available or lose their unemployment benefits', 'People who are unemployed should have the right to refuse a job they do not want'],
    'E039': ['Competition is good. It stimulates people to work hard and develop new ideas', 'Competition is harmful. It brings out the worst in people'],
    'E040': ['In the long run, hard work usually brings a better life', 'Hard work doesn’t generally bring success—it’s more a matter of luck and connections'],
}
CONFIDENCE = {'1':'A great deal', '2':'Quite a lot', '3':'Not very much', '4':'None at all',
              '-1':"Don't know", '-2':'No answer', '-3':'Not applicable', '-4':'Not asked', '-5':'Other missing'}
REVERSE = {'E036','E037','E038','E039','E040','F114A','F116'}


def values_wording(survey, item, years, groups):
    refs = []
    notes = []
    if survey == 'EVS':
        path = 'docs/evs_trend_codebook_v3.pdf'
        pages = pdf_pages(path)
        n = next(i+1 for i,t in enumerate(pages) if item+' -' in t)
        excerpt = pages[n-1].split(item+' -',1)[1].split('Survey:')[0]
        refs.append(reference(path,[n],years,source_url('evs_trend_codebook_v3.pdf'),
                              'English master wording and harmonised codebook; supplemented by the actual Ukrainian forms below.',excerpt))
        for year in years:
            pages_by_year={1999:([28],'Q58') if item.startswith('E069_') else ([31],'Q65') if item=='F116' else ([25],'Q54'),
                           2008:([20],'Q63') if item.startswith('E069_') else ([22],'Q68') if item=='F116' else ([19,85],'Q58'),
                           2020:([14],'Q38') if item.startswith('E069_') else ([16],'Q44') if item=='F116' else ([12,58],'Q32')}
            ns,code=pages_by_year[year]
            path=f'data/documentation/evs_ukraine_{year}_questionnaires.pdf'
            refs.append(reference(path,ns,[year],source_url(path.split('/')[-1]),
                                  'Ukrainian national field questionnaire, '+code+('; visually checked because PDF text encoding is damaged.' if year==1999 else '.')))
        notes.append('Ukrainian national questionnaires checked for all three waves (1999, 2008, 2020). The English master is a reference, not a substitute for the local text. Russian forms are in the linked files but are not all independently compared here.')
    else:
        terms = {
            'E035':['Incomes should','incomes should'], 'E036':['Private ownership','private ownership'],
            'E037':['Government should','government should','People should'],
            'E039':['Competition is','competition is'], 'E040':['hard work','Hard work'],
            'E224':['tax the rich'], 'E227':['aid for unemployment'], 'E233A':['incomes equal'],
            'F116':['Cheating on tax','cheating on tax'], 'F114A':['benefits to which'],
            'B008':['slower economic growth'],
        }
        if item.startswith('E069_'): terms[item]=['confidence you have','confidence in','how much confidence']
        for y in years:
            wave={1996:3,2006:5,2011:6,2020:7}[y]
            path=f'docs/wvs_questionnaire_{wave}.pdf'
            pages=pdf_pages(path)
            matched=[i+1 for i,t in enumerate(pages) if any(x.lower() in norm(t).lower() for x in terms[item])]
            assert matched,(item,y)
            refs.append(reference(path,matched,[y],source_url(f'wvs_questionnaire_{wave}.pdf'),
                                  'English master questionnaire; national-language form not independently checked.'))
        notes.append('English master questionnaires checked for each plotted wave. National-language forms have not been independently verified for every wave.')
        if 2020 in years:
            # The Ukrainian report reproduces the locally worded questions and scales.
            p='data/documentation/wvs_ukraine_2020_uk.pdf'
            if item in ['E035','E036','E037','E039','E040']:
                ns=[83] if item in ['E035','E036'] else [83,84] if item=='E037' else [84]
                refs.append(reference(p,ns,[2020],WVS_UA,'Ukrainian national report, Table 7.1; local wording reproduced.'))
                notes.append('For 2020, also checked the Ukrainian national report, Table 7.1 (PDF pp. 83–84).')
    if item in VALUES:
        question,label,polarity=VALUES[item]
        if item in ENDPOINTS:
            source_question='Place your views on a 1–10 scale between the two opposing statements (shared-stem summary; exact wording in linked source).'
            options={'1':ENDPOINTS[item][0],'2–9':'Intermediate positions','10':ENDPOINTS[item][1]}
        elif item.startswith('F'):
            source_question=('Please tell me for each of the following actions whether you think it can always be justified, never be justified, or something in between. '+
                             ('Cheating on taxes if you have a chance.' if item=='F116' else 'Claiming government benefits to which you are not entitled.'))
            options={'1':'Never justifiable','2–9':'Intermediate positions','10':'Always justifiable'}
        else:
            source_question='How essential do you think the following things are as characteristics of democracy? '+{
                'E224':'Governments tax the rich and subsidize the poor.',
                'E227':'People receive state aid for unemployment.',
                'E233A':'The state makes people’s incomes equal.'}[item]
            options={'1':'Not an essential characteristic of democracy','2–9':'Intermediate positions','10':'An essential characteristic of democracy',
                     '0':'Against democracy (spontaneous; excluded from the numeric mean)'}
        notes.append('Plotted score = 11 − harmonised archive value.' if item in REVERSE else 'Original numeric direction retained.')
        if item=='E037' and survey=='WVS':
            notes.append('WVS master forms put government responsibility at 1 and personal responsibility at 10; the harmonised E037 archive uses the opposite order. Chart endpoints follow the plotted score.')
            if survey=='WVS':options['1'],options['10']=options['10'],options['1']
        if item=='E035' and survey=='WVS':
            question='Income equality versus higher income as a reward for greater individual effort'
            label='Income equality versus rewards for individual effort'
            polarity='1 = incomes more equal; 10 = greater income rewards for individual effort'
            options['10 (1996–2011 English masters)']='We need larger income differences as incentives for individual effort'
            options['10 (2020 English master)']=options.pop('10')
            options['1 (2020 Ukrainian report)']='Доходи повинні бути більш рівними'
            options['10 (2020 Ukrainian report)']='Дохід повинен бути значно вищим у випадку більш істотних індивідуальних зусиль'
            notes.append('The 2020 English master omits an explicit reference to income differences, but the Ukrainian report explicitly says income should be considerably higher for greater individual effort. Do not substitute the English master for the local wording.')
        chart_note=''
        if survey=='EVS':
            source_question='На цій картці – декілька протилежних тверджень з різних питань. Як Ви визначили б Вашу точку зору на цій шкалі? (2020, Q32; endpoints below.)'
            native={
                'E035':['Різниця в прибутках не повинна бути дуже великою','Той, хто більше працює, повинен отримувати більше'],
                'E036':['Частка приватної власності в бізнесі та виробництві повинна бути збільшена','Частка державної власності в бізнесі та виробництві повинна бути збільшена'],
                'E037':['Люди більшою мірою самі повинні нести відповідальність за те, щоб себе забезпечити','Держава більшою мірою повинна нести відповідальність за те, щоб всі громадяни були забезпечені'],
                'E038':['Безробітні повинні погоджуватися на будь-яку роботу, яку їм пропонують, або позбавлятися допомоги по безробіттю','Безробітні повинні мати право відмовитися від роботи, яка їм не подобається'],
                'E039':['Конкуренція – це добре','Конкуренція шкідлива'],
            }
            if item in native:
                options={'1 (Ukrainian 2020)':native[item][0],'2–9':'Intermediate positions','10 (Ukrainian 2020)':native[item][1]}
            if item=='E035':
                question='Should income differences be smaller, or should those who work more receive more?'
                label='Smaller income differences versus greater rewards for work'
                polarity='1 = income differences should not be very large; 10 = those who work more should receive more'
                options['1 (Ukrainian 1999)']='Різниця в доходах не повинна бути дуже великою'
                notes.append('The Ukrainian 1999, 2008 and 2020 endpoint is “Той, хто більше працює, повинен отримувати більше”. The opposite endpoint refers to income differences in 1999 and uses “прибутках” in 2008/2020. Do not substitute the English master’s more abstract “greater incentives” wording.')
            elif item=='E039':
                question='Is competition good or harmful?';polarity='1 = competition is harmful; 10 = competition is good'
                options['1 (Ukrainian 1999)']='Конкуренція це добре. Вона стимулює людей напружено працювати та розвивати нові ідеї'
                options['1 (Ukrainian 2008)']='Конкуренція це добре. Вона стимулює людей наполегливо працювати та розвивати нові ідеї'
                options['10 (Ukrainian 1999/2008)']='Конкуренція шкідлива. Вона пробуджує в людях їх найгірші якості'
                chart_note='1999/2008 give reasons why competition is good or harmful; 2020 omits those explanations.'
                notes.append('Both the 2020 field form and showcard shorten the earlier explanatory endpoints to “Конкуренція – це добре” / “Конкуренція шкідлива”. This wording difference remains a comparability limitation.')
            elif item=='F116':
                question='How justifiable is not paying taxes if there is an opportunity?';label='Rejection of not paying taxes'
                source_question='Використовуючи шкалу на цій картці, скажіть мені стосовно кожного твердження, чи може це бути завжди виправдано, ніколи не може бути виправдано або Ваша думка перебуває між цими оцінками? Несплата податків, якщо є така можливість. (2020 Q44; stem and item joined.)'
                options={'1':'Ніколи НЕ виправдано','2–9':'Intermediate positions','10':'Завжди виправдано'}
                notes.append('1999/2008: “Невиплата податків, якщо є така можливість”; 2020: “Несплата податків, якщо є така можливість”. The chart follows national wording (nonpayment), rather than the master’s “cheating”.')
        options['Archive special codes (excluded from means)']='−1: don’t know; −2: no answer; −3: not applicable; −4: not asked; −5: other missing; system missing also excluded'
        return dict(question=question,label=label,polarity=polarity,source_question=source_question,source_options=options,
                    display_groups=groups,references=refs,wording_notes=notes,wording_type='English question summary; source endpoints and wave differences below',chart_note=chart_note)
    if item.startswith('E069_'):
        institution={'E069_05':'labour unions','E069_09':'the social security system','E069_13':'major companies','E069_41':'banks / the banking system'}[item]
        options=dict(CONFIDENCE)
        source_question=f'For each organisation, how much confidence do you have in it: a great deal, quite a lot, not very much, or none at all? Item: {institution}. (English master shared-stem summary.)'
        if survey=='EVS':
            source_question='Я назву Вам деякі організації та громадські інститути. Скажіть, наскільки Ви довіряєте кожній (ому) з них: повністю довіряєте, деякою мірою довіряєте, не дуже довіряєте або зовсім не довіряєте? (2020 Q38.)'
            source_question+=' Пункт: '+{'E069_05':'Профспілки','E069_09':'Система соціального забезпечення','E069_13':'Великі компанії'}[item]+'.'
            options.update({'1':'Повністю довіряю (trust completely)','2':'Деякою мірою довіряю (trust to some extent)',
                            '3':'Не дуже довіряю (do not trust very much)','4':'Зовсім не довіряю (do not trust at all)'})
        else:
            refs.append(reference('data/documentation/wvs_ukraine_2020_uk.pdf',[60,61],[2020],WVS_UA,
                                  'Ukrainian national report, Table 6.3, confidence wording and options.'))
            options['1–4 (2020 Ukrainian report)']='Повністю довіряєте / Деякою мірою довіряєте / Не дуже довіряєте / Зовсім не довіряєте'
            notes.append('The Ukrainian 2020 report says completely / to some extent / not very much / not at all. The English master labels are a great deal / quite a lot / not very much / none at all. Group labels therefore describe the grouped confidence levels rather than quoting one language version.')
        return dict(question=f'How much confidence do you have in {institution}?',label='Confidence in '+institution,polarity='',
                    source_question=source_question,
                    source_options=options,display_groups=rename(groups,{'Confidence':'Confidence (two positive options)','No confidence':'Little or no confidence'}),
                    references=refs,wording_notes=notes,wording_type='English summary of the confidence battery')
    assert item=='B008'
    return dict(question='Which takes priority: environmental protection or economic growth and jobs, accepting the stated trade-offs?',
                label='Environment versus growth and jobs',polarity='',
                source_question='Here are two statements people sometimes make when discussing the environment and economic growth. Which of them comes closer to your own point of view?',
                source_options={'1':'Protecting the environment should be given priority, even if it causes slower economic growth and some loss of jobs.',
                                '2':'Economic growth and creating jobs should be the top priority, even if the environment suffers to some extent.',
                                '3':'Other answer (volunteered only)', '-1':"Don't know",'-2 to -5':'No answer / other missing'},
                display_groups=rename(groups,{'Protect the environment':'Environment, even at cost to growth/jobs','Growth and jobs':'Growth/jobs, even at cost to environment','Other answer':'Other answer (volunteered)'}),
                references=refs,wording_notes=notes,wording_type='English master question; chart labels abbreviate the complete alternatives')


def monitoring_excerpt(file, page, code):
    from monitoring_extract import page_text
    t=page_text(file,int(page))
    marker=re.escape(str(code)).replace('a','[aа]')
    start=re.search(r'(?m)^\s*'+marker+r'\.?(?=\s)',t)
    assert start,(file,page,code)
    t=t[start.end():]
    end=re.search(r'(?m)^\s*[a-zа-я]{1,3}\d+[a-z]?(?:\.\d+)?\.?\s',t)
    if end:t=t[:end.start()]
    t=t.split('Середній бал')[0]
    t=re.sub(r'(?m)^\s*[\d., —–-]+\s*$','',t)
    t=re.sub(r'\d+[.,]\d+','',t)
    return norm(t)


def monitoring_wording(item,years,groups,trace):
    refs=[]
    z=trace[trace.survey.eq('Monitoring') & trace['item'].eq(item)]
    for (file,page,code),v in z.groupby(['source_file','pdf_page','source_question'],sort=False):
        excerpt=monitoring_excerpt(file,page,code)
        refs.append(reference('data/documentation/monitoring/'+file,[int(page)],sorted(v.year.astype(int).unique().tolist()),source_url(file),
                              'Original Ukrainian published question and response table; percentages removed from the excerpt.',excerpt))
    assert refs,item
    mapping={"Don't know":'Hard to say','Undecided':'Hard to say'}
    notes=['English chart text is a translation/summary of the Ukrainian published tables. Full original wording appears in the source excerpts.']
    question=label=''
    opt={'no_answer':'Не відповіли'}
    if item.startswith(('privatise_','existing_private_','retrospective_','renationalise_')):
        sector={'small':'small enterprises','large':'large enterprises','land':'land'}[item.split('_')[-1]]
        if item.startswith('privatise_'):
            question=f'How do you feel about transferring {sector} into private ownership (privatisation)?'
            label=f'Attitudes toward privatisation: {sector}'
            mapping.update({'Positive':'Rather positive','Negative':'Rather negative','Mixed / ambivalent':'Hard to say: negative or positive'})
            opt.update(negative='Скоріше негативно',ambivalent='Важко сказати, негативно чи позитивно',positive='Скоріше позитивно')
        elif item.startswith('existing_private_'):
            question=f'How do you feel about the existence of privately owned {sector} in Ukraine?'
            label=f'Attitudes toward existing private ownership: {sector}'
            mapping.update({'Positive':'Positive / rather positive','Negative':'Negative / rather negative'})
            opt.update(negative='Негативно',rather_negative='Скоріше негативно',dont_know='Важко відповісти',rather_positive='Скоріше позитивно',positive='Позитивно')
        else:
            question=(f'Was it worth transferring {sector} into private ownership (privatising them)?' if item.startswith('retrospective_') else
                      f'Is it advisable to return privately owned {sector} to state ownership?')
            label=(f'Was privatisation worthwhile: {sector}' if item.startswith('retrospective_') else f'Views on returning private {sector} to the state')
            mapping.update({'Yes':'Yes / rather yes','No':'No / rather no'})
            opt.update(no='Ні',rather_no='Скоріше ні',dont_know='Важко відповісти',rather_yes='Скоріше так',yes='Так')
    elif item.startswith('trust_'):
        institution={'trust_banks':'banks','trust_unions':'trade unions','trust_tax_authority':'the tax authority','trust_state_managers':'managers of state enterprises'}[item]
        question=f'What is your level of trust in {institution}?';label='Trust in '+institution
        mapping.update({'Trust':'Completely / mostly trust','Distrust':'Do not trust at all / mostly distrust'})
        opt.update(negative='Зовсім не довіряю',rather_negative='Переважно не довіряю',undecided='Важко сказати, довіряю чи ні',rather_positive='Переважно довіряю',positive='Цілком довіряю')
    elif item in ['start_business','work_private_employer']:
        question=('Would you like to start your own business (enterprise, farm, etc.)?' if item=='start_business' else 'Would you personally agree to work for a private entrepreneur?')
        label='Willingness to start a business' if item=='start_business' else 'Willingness to work for a private entrepreneur'
        mapping.update({'Yes':'Yes / rather yes','No':'No / rather no'})
        opt.update(no='Ні',rather_no='Скоріше ні',dont_know='Важко сказати',rather_yes='Скоріше так',yes='Так')
        if item=='start_business':
            opt['already_owner']='Вже маю власний бізнес (2020 only)'
            notes.append('“Already owns a business” is offered only in 2020; absent in earlier waves, not zero.')
    elif item=='enterprise_initiative':
        question='How important to you is the opportunity for entrepreneurial initiative (private enterprises, business, farming)?'
        label='Importance of the opportunity for entrepreneurial initiative'
        mapping.update({'Important':'Rather / very important','Not important':'Not at all / rather unimportant'})
        opt.update(negative='Зовсім не важливо',rather_negative='Скоріше неважливо',undecided='Важко сказати, важливо чи ні',rather_positive='Скоріше важливо',positive='Дуже важливо')
        refs.append(reference('data/documentation/monitoring/mon2020.pdf',[531],years,source_url('mon2020.pdf'),'Shared question stem r3; item r3.9 appears on PDF p. 534.'))
    elif item=='accept_market_values':
        question='Do you accept as your own the post-independence values of private property, enrichment, individualism and personal success?'
        label='Acceptance of post-independence values as one’s own'
        mapping.update({'Accept':'Definitely / rather yes','Reject':'Definitely / rather no'})
        opt.update(negative='Однозначно ні',rather_negative='Скоріше ні',rather_positive='Скоріше так',positive='Однозначно так',dont_know='Важко відповісти')
    elif item=='market_relations_natural':
        question='To what extent have you adapted to the current life situation?';label='Adaptation to the current life situation'
        mapping.update({'Adapted; markets feel natural':'Actively adapted; markets feel natural','Still finding a place in life':'Constantly searching for a place in life','Not adapting; waiting for change':'No wish to adapt; waiting for better times'})
        opt.update(adapted='Активно включився в нове життя, ринкові відносини видаються мені природним способом життєдіяльності',
                   searching='Перебуваю в постійному пошуку себе в теперішньому житті',
                   not_adapting='Не маю бажання пристосовуватися до теперішньої ситуації, живу як доведеться, чекаю змін на краще',dont_know='Важко відповісти')
    elif item=='land_sales_agricultural':
        question='Should buying and selling agricultural land in Ukraine be allowed?';label='Allowing the purchase and sale of agricultural land'
        opt.update(yes='Так',no='Ні',dont_know='Важко відповісти')
    elif item=='land_ownership_rights':
        question='What should ownership rights over land and land holdings be?';label='Preferred land ownership rights'
        mapping.update({'Inheritable use, no sale':'Lifetime inheritable use, no sale','Community ownership':'Community ownership; temporary use by residents','State ownership':'State ownership of all land'})
        opt.update(full_ownership_including_sale='Full ownership, including the right to sell',inheritable_use_no_sale='Lifetime use with inheritance rights, but no right to sell',
                   community_ownership='Ownership by the community (village, city), which allocates temporary use to its residents',state_ownership='State ownership of all land',dont_know='Hard to say')
    elif item=='state_market_role':
        question='How should the state participate in managing the economy?';label='Preferred role of the state in managing the economy'
        mapping.update({'Minimal state involvement':'Minimise state involvement; market regulates','State and market combined':'Combine state management and market methods','Planned economy':'Return to planning and full state control'})
        opt.update(minimal_state_market='Треба мінімізувати участь держави — все регулює ринок',mixed_state_market='Треба поєднати державне управління і ринкові методи',
                   planned_economy='Треба повернутися до планової економіки на основі повного державного обліку і контролю',dont_know='Важко відповісти')
    elif item=='ownership_policy':
        question='What should Ukraine’s state policy on ownership be?';label='Preferred state policy on ownership'
        mapping.update({'Broad privatisation':'Broad transfer of state firms to private owners',
                        'Privatise except efficient state firms':'Keep efficient state firms; others may be private',
                        'Retain state enterprises':'Keep current state firms; no more nationalisation',
                        'Nationalise private firms':'Return as many companies as possible to state',"Don't know / no answer":'Hard to say / no answer'})
        opt.update(nationalise='Необхідно повернути державі якнайбільше компаній',
                   retain_state_firms='Повертати компанії державі не потрібно, але ті, що належать їй, повинні залишатися державними',
                   privatise_except_efficient_state_firms='Ефективні державні компанії треба залишити, решту можна передати у приватну власність',
                   broad_privatisation='Необхідно здійснити широку передачу державних підприємств у приватну власність',dont_know_or_no_answer='Важко відповісти / немає відповіді')
        opt.pop('no_answer')
    else:raise ValueError(item)
    codes={str(c) for cs in groups.values() for c in cs}
    assert codes==set(opt),(item,codes-set(opt),set(opt)-codes)
    source_question=refs[0]['excerpt']
    if item=='enterprise_initiative':source_question='Оцініть ступінь важливості ОСОБИСТО ДЛЯ ВАС наведеного нижче: '+source_question
    return dict(question=question,label=label,polarity='',source_question=source_question,source_options=opt,
                display_groups=rename(groups,mapping),references=refs,wording_notes=notes,wording_type='English translation/summary; original Ukrainian tables below')


def pew_wording(item,years,groups):
    page,code={'transition_approval':(35,'Q16a'),'better_than_communism':(37,'Q17'),'transition_ordinary':(38,'Q20a'),
               'transition_business':(38,'Q20b'),'transition_politicians':(39,'Q20c')}[item]
    notes=['English topline wording checked; Ukrainian fielded translations have not been independently verified.']
    mapping={}
    chart_note=''
    if item=='transition_approval':
        question='Do you approve or disapprove of the move from a state-controlled to a market economy?'
        label='Approval of the transition to a market economy'
        q='Again, thinking back to 1991, do you strongly approve, approve, disapprove or strongly disapprove that our country moved from having a state-controlled economy to having a market economy?'
        options={'strongly_approve':'Strongly approve','approve':'Approve','disapprove':'Disapprove','strongly_disapprove':'Strongly disapprove','dont_know':'DK/Refused'}
        mapping={'Approve':'Strongly approve / approve','Disapprove':'Disapprove / strongly disapprove'}
        chart_note='1991 asks about efforts to establish a free market; later waves ask about the transition.'
        notes.append('1991: “Overall, do you strongly approve, approve, disapprove or strongly disapprove of efforts to establish a free market economy in…?” Prospective wording differs from later retrospective wording; 1991 is shown as an isolated point.')
    elif item=='better_than_communism':
        question='Is the economic situation for most Ukrainians better, worse, or about the same as under communism?'
        label='Economic situation for most people compared with communism'
        q='Would you say that the economic situation for most (survey country nationality) people today is better, worse, or about the same as it was under communism?'
        options={'better':'Better','worse':'Worse','same':'About the same','dont_know':'DK/Refused'}
    else:
        who={'transition_ordinary':'ordinary people','transition_business':'business people','transition_politicians':'politicians'}[item]
        question=f'How much have {who} benefited from the changes since 1991?'
        label=who.capitalize()+' seen as benefiting from changes since 1991'
        q='How much have ____ benefited from the changes since 1989 / 1991 – a great deal, a fair amount, not too much, or not at all? Item: '+who+'. Ukraine: since 1991.'
        options={'great':'A great deal','fair':'A fair amount','little':'Not too much','none':'Not at all','dont_know':'DK/Refused'}
        mapping={'Benefited substantially':'A great deal / a fair amount','Benefited little or not at all':'Not too much / not at all'}
        if item=='transition_business':
            chart_note='2009/2011: “people who own businesses”; 2019: “business people”.'
            notes.append(chart_note)
    return dict(question=question,label=label,polarity='',source_question=q,source_options=options,display_groups=rename(groups,mapping),
                references=[reference('data/documentation/pew_2019_europe_topline.pdf',[page],years,PEW,'English published topline, '+code)],
                wording_notes=notes,wording_type='English topline; chart question shortened',chart_note=chart_note,
                isolated_years=[1991] if item=='transition_approval' else [])


def ess_wording(item,years,groups):
    z=pd.read_csv(ROOT/'docs/ess_question_crosswalk.csv');z=z[z['item'].eq(item)]
    question,label,polarity={
        'gincdif':('Do you agree or disagree: government should take measures to reduce differences in income levels?',
                    'Agreement that government should reduce income differences',''),
        'imbgeco':('Is it generally bad or good for Ukraine’s economy that people come to live here from other countries?',
                   'Immigration judged bad or good for the economy','0 = bad for the economy; 10 = good for the economy'),
        'gvctzpv':('For democracy in general, how important is it that government protects all citizens against poverty?',
                    'Poverty protection as a requirement of democracy','0 = not at all important for democracy in general; 10 = extremely important'),
        'grdfinc':('For democracy in general, how important is it that government takes measures to reduce income differences?',
                   'Reducing income differences as a requirement of democracy','0 = not at all important for democracy in general; 10 = extremely important'),
        'gvctzpvc':('To what extent does this apply in Ukraine: government protects all citizens against poverty?',
                    'Perceived government protection of all citizens against poverty','0 = does not apply at all; 10 = applies completely'),
        'grdfincc':('To what extent does this apply in Ukraine: government takes measures to reduce income differences?',
                   'Perceived government action to reduce income differences','0 = does not apply at all; 10 = applies completely'),
    }[item]
    options={str(int(float(k))):v for k,v in json.loads(z.iloc[-1].response_labels).items()}
    refs=[reference('docs/ess_question_crosswalk.csv',[],years,SOURCE_LINK+'#european-social-survey-ess',
                    'English source wording and value labels from supplied codebooks, separately checked for each included round.', ' | '.join(z.wording.unique()))]
    ua='data/documentation/ess/ESS Round 10 UA UKR Source Questionnaire.pdf'
    search={'gincdif':'B33','imbgeco':'B43','gvctzpv':'D8','grdfinc':'D9','gvctzpvc':'D20','grdfincc':'D21'}[item]
    pages=pdf_pages(ua)
    ns=[i+1 for i,t in enumerate(pages) if re.search(r'\b'+search+r'\b',t)]
    assert ns,(item,search)
    ua_question={
        'gincdif':'До якої міри Ви погоджуєтесь чи не погоджуєтесь з наступними твердженнями? Уряд повинен вжити заходів для зменшення різниці у рівнях доходів людей.',
        'imbgeco':'Як Ви вважаєте, те, що люди з інших країн переїжджають жити до України, це в цілому добре чи погано для економіки країни?',
        'gvctzpv':'Міркуючи про демократію швидше в цілому, аніж окремо про Україну, наскільки важливим для демократії в цілому, на Ваш погляд, є наступне… щоб влада захищала всіх громадян від бідності?',
        'grdfinc':'Міркуючи про демократію швидше в цілому, аніж окремо про Україну, наскільки важливим для демократії в цілому, на Ваш погляд, є наступне… щоб влада вживала заходів по скороченню різниці у рівнях доходів громадян?',
        'gvctzpvc':'Наскільки кожне із таких тверджень відповідає стану справ в Україні сьогодні? …в Україні влада захищає всіх громадян від бідності.',
        'grdfincc':'Наскільки кожне із таких тверджень відповідає стану справ в Україні сьогодні? …в Україні влада вживає заходів по скороченню різниці у рівнях доходів громадян.',
    }[item]
    refs.append(reference(ua,ns,[2022],'https://github.com/KSE-Sociological-Center/ESS10_Ukraine',
                          'Ukrainian ESS Round 10 source questionnaire, '+search+'; shared stem and item joined, interviewer instructions omitted.',ua_question))
    if item in ['gvctzpv','grdfinc']:
        options['0 / 10 (Ukrainian 2022)']='Зовсім НЕ важливо для демократії в цілому / Життєво важливо для демократії в цілому'
    mapping={'Agree':'Agree strongly / agree','Disagree':'Disagree / disagree strongly'}
    return dict(question=question,label=label,polarity=polarity,source_question=' | '.join(z.wording.unique()),
                source_options=options,display_groups=rename(groups,mapping),references=refs,
                wording_notes=['English codebook wording and category labels checked across included rounds; the Ukrainian Round 10 form also checked. Earlier and Round 11 national forms not independently verified.',
                               'The applicability items ask whether government TAKES MEASURES, not whether income inequality actually falls.' ] if item=='grdfincc' else
                              ['English codebook wording and category labels checked across included rounds; the Ukrainian Round 10 form also checked. Earlier and Round 11 national forms not independently verified.'],
                wording_type='English question summary; codebook text below')


ISSP_OPTIONS = {
    'agree': ['Повністю згоден','Скоріше згоден','Наскільки згоден, настільки й не згоден','Скоріше не згоден','Повністю не згоден'],
    'important': ['Надзвичайно важливо','Дуже важливо','Важливо','Не дуже важливо','Взагалі не важливо'],
    'tax': ['Мають платити набагато більші податки','Більші податки','Такі самі податки','Менші податки','Набагато менші податки'],
    'tax_level': ['Занадто високий','Зависокий','Нормальний','Занизький','Занадто низький'],
    'fair5': ['Повністю справедливою, правильною','Скоріше справедливою, правильною',
              'Наскільки справедливою, правильною, настільки й несправедливою, неправильною',
              'Скоріше несправедливою, неправильною','Повністю несправедливою, неправильною'],
    'conflict': ['Дуже гострий конфлікт','Гострий конфлікт','Не дуже гострий конфлікт','Немає конфлікту взагалі'],
    'society': ['A: Нечисленна еліта наверху, небагато людей посередині й переважна більшість внизу',
                'B: Суспільство як піраміда: нечисленна еліта на верхівці, більш численний прошарок посередині та найбільше людей внизу',
                'C: Схожа на піраміду типу В, проте дещо менше людей знаходиться на самому низу піраміди',
                'D: Суспільство, де більшість людей знаходиться посередині',
                'E: Велика кількість людей на верхівці та нечисленна кількість людей внизу'],
}


def issp_wording(item,years,groups):
    from issp_analysis import ITEMS
    spec=ITEMS[item];kind=spec['kind']
    mapping={"Don't know":'Hard to say','Essential / very important':'Extremely / very important',
             'Mixed feelings':'Equally fair and unfair','Weak / no conflicts':'Not very strong / no conflicts',
             'Strong conflicts':'Very strong / strong conflicts','Agree':'Completely / rather agree','Disagree':'Completely / rather disagree',
             'Fair':'Completely / rather fair','Unfair':'Completely / rather unfair',
             'A: Elite over a large bottom':'A: Small elite, most people at bottom'}
    notes=['Ukrainian national questionnaires checked for 2009 and 2019, alongside the microdata value labels. Chart text is an English translation/summary. The Russian-language forms have not been independently compared here.']
    code09=code19='';q=''
    if item.startswith('ahead_'):
        suffix=item[6:]
        en,ua,letter09,letter19={
            'wealth':('coming from a wealthy family','походження з багатої родини','a','a'),
            'parents':('having well-educated parents','мати батьків із хорошою освітою','b','b'),
            'education':('personally obtaining a good education','особисто здобути хорошу освіту','c','c'),
            'work':('working hard and conscientiously','тяжко й сумлінно працювати','e','d'),
            'connections':('having personal connections with the right people','мати особисті зв’язки з «потрібними» людьми','f','e'),
            'political':('having connections in political circles','мати зв’язки у політичних колах','g','f'),
            'bribes':('giving bribes','давати хабарі','h','g'),
            'race':('nationality / ethnic background','національність','i','h'),
            'religion':('a person’s religion','релігія, котру сповідує людина','j','i'),
            'gender':('being a man or a woman','бути чоловіком або жінкою','k','j'),
        }[suffix]
        question=f'How important is {en} for getting ahead in life?';label='Importance for success: '+en
        q='Оцініть, будь ласка, наскільки важливим є те, що я зачитаю, для того, щоб досягти життєвого успіху… Пункт: '+ua+'.'
        code09='Q1'+letter09;code19='Q1'+letter19;pages09=[2];pages19=[2]
        if suffix=='race':notes.append('National wording is “національність” (nationality/ethnic background), not “race” in the international source variable label.')
    elif item.startswith('pay_'):
        en,ua,letter09,letter19={
            'responsibility':('the responsibility of the job or position','ступінь відповідальності роботи чи посади','a','a'),
            'education':('years of general/specialised education and further training','кількість років, проведених в закладах загальної та спеціальної освіти, а також підвищення кваліфікації','b','b'),
            'children':('whether the person has children','якщо людина має дітей','d','c'),
            'performance':('how well the person does the job','те, як добре він / вона виконують свою роботу','e','d'),
        }[item[4:]]
        question=f'When deciding how much people should earn, how important is {en}?';label='Pay-setting criterion: '+en
        q='При вирішенні питання щодо розміру заробітної плати працівників, наскільки важливим, на вашу думку, мають бути… '+ua+'?'
        code09='Q12'+letter09;code19='Q14'+letter19;pages09=[6];pages19=[6]
        notes.append('The highest option is “Вкрай важливо” in the 2009 pay battery and “Надзвичайно важливо” in 2019; translated as “Extremely important”.')
    elif item.startswith('earn_'):
        actual=item.startswith('earn_actual_');occupation=item.split('_')[-1]
        en,ua,letter={'doctor':('a general physician','лікар-терапевт','a'),
                      'chairman':('the chair of a large company’s board','голова правління великої компанії','b'),
                      'shop':('a shop assistant','продавець у магазині','c'),
                      'worker':('an unskilled factory worker','некваліфікований робітник на заводі','d'),
                      'minister':('a minister in Ukraine’s government','міністр Уряду України','e')}[occupation]
        question=(f'How much do you think {en} actually earns per month after all taxes?' if actual else f'How much do you think {en} should earn per month after all taxes?')
        label=('Perceived monthly pay: ' if actual else 'Desired monthly pay: ')+en
        q=('Нам було б цікаво дізнатися, скільки, на вашу думку, реально заробляють в місяць представники деяких професій та посад після вирахування усіх податків.' if actual else
           'Не зважаючи на ту платню, яку, на вашу думку, вони заробляють, будь ласка, вкажіть скільки, на вашу думку, вони мають заробляти на місяць після відрахування усіх податків.')+' Професія/посада: '+ua+'.'
        code09=('Q4' if actual else 'Q5')+letter;code19=('Q2' if actual else 'Q3')+letter;pages09=[3];pages19=[2]
        notes.append('Respondent estimates of actual/desired pay, not observed wages. Open monetary answers, monthly UAH after taxes; nominal prices, no inflation adjustment.')
    elif item.startswith('conflict_'):
        en,ua,letter={'rich_poor':('rich and poor','бідними та багатими','a'),
                      'class':('the working and middle classes','робітничим класом і середнім класом','b'),
                      'management':('management and employees','керівним персоналом та працівниками','c')}[item[9:]]
        question=f'How strong is the conflict in Ukraine between {en}?';label='Perceived conflict: '+en
        q='В багатьох країнах існують відмінності або навіть конфлікти між соціальними групами. На вашу думку, наскільки гострим є конфлікт в Україні між… '+ua+'?'
        code09='Q9'+letter;code19='Q12'+letter;pages09=[5];pages19=[5]
    else:
        question,label,q,code09,code19,pages09,pages19={
            'income_gap':('Do you agree or disagree that income differences in Ukraine are too large?', 'Agreement that income differences in Ukraine are too large',
                          'Наскільки ви погоджуєтесь чи ні з наступними твердженнями? В Україні надто велика різниця у доходах.','Q6a','Q4a',[4],[3]),
            'redistribution':('Do you agree that government is responsible for reducing differences between high and low incomes?', 'Government responsibility for reducing income differences',
                              'Наскільки ви погоджуєтесь чи ні з наступними твердженнями? Уряд відповідальний за зменшення різниці у доходах між особами з високими та низьким доходами.','Q6b','Q4b',[4],[3]),
            'unemployed_living':('Do you agree that government must provide an acceptable standard of living for unemployed people?', 'Government obligation to provide for unemployed people',
                                 'Наскільки ви погоджуєтесь чи ні з наступними твердженнями? Уряд зобов’язаний забезпечити прийнятний рівень життя для безробітних.','Q6c','Q4c',[4],[3]),
            'tax_rich':('Should people with high incomes pay higher, the same, or lower taxes than people with low incomes?', 'Preferred taxes on high versus low incomes',
                        'На вашу думку, чи мають люди з високими доходами платити більші податки, ніж особи з низькими доходами, або такі самі, чи навіть менші?','Q7a','Q8a',[4],[3]),
            'tax_level':('How would you rate the current level of taxation of people with high incomes in Ukraine?', 'Current taxation of high incomes judged too high or too low',
                         'Загалом, як би ви оцінили рівень оподаткування осіб з високими доходами в Україні? Рівень оподаткування доходів цих осіб…','Q7b','Q8b',[4],[4]),
            'buy_health':('Is it fair and right that high-income people can afford better healthcare than low-income people?', 'Fairness of richer people being able to afford better healthcare',
                          'Чи ви вважаєте справедливою та правильною ситуацію, коли особи з високими доходами можуть дозволити собі більш якісні послуги у сфері охорони здоров’я, ніж особи з низькими доходами?','Q8a','Q9a',[4],[4]),
            'buy_education':('Is it fair and right that high-income people can buy better education for their children than low-income people?', 'Fairness of richer people buying better education for children',
                             'Чи ви вважаєте справедливою та правильною ситуацію, коли особи з високими доходами можуть дозволити собі купити своїм дітям більш якісні послуги у сфері освіти, ніж особи з низькими доходами?','Q8b','Q9b',[4],[4]),
            'society_actual':('Which of the five diagrams best describes how people are distributed in Ukrainian society today?', 'Perceived shape of Ukrainian society',
                              'Якщо взяти до уваги тип суспільства, що існує в Україні на цей час, яка діаграма найкраще змальовує розподіл людей в українському суспільстві?','Q14a','Q15a',[6],[6,7]),
            'society_ideal':('Which of the five models of society would you choose for Ukraine?', 'Preferred shape of Ukrainian society',
                             'На яку модель Україна має походити – яку б ви обрали?','Q14b','Q15b',[6],[6,7]),
        }[item]
    options={str(i+1):v for i,v in enumerate(ISSP_OPTIONS[kind])} if kind!='money' else {'amount':'Open response: monthly UAH after all taxes'}
    options.update({'8 (2009); −8 (2019)':'Важко сказати / ВС (hard to say)', '9 (2009); −9 (2019)':'No answer (archive category)'})
    if kind=='money':options={'amount':'Open response: monthly UAH after all taxes','special':'Do not know / refusal / other negative special codes excluded; archive labels retained in the crosswalk'}
    if item=='tax_rich':notes.append('Both Ukrainian questionnaires say higher taxes, not explicitly a higher share of income or tax rate. The chart preserves the national wording.')
    if item=='redistribution':notes.append('2009: “Зобов’язанням Уряду має бути…” (should be an obligation of government); 2019: “Уряд відповідальний…” (government is responsible). Both concern responsibility for reducing the gap; the modal wording differs.')
    if kind=='society':notes.append('Respondents saw five diagrams and descriptions. The chart legend abbreviates those descriptions; the source link includes the original diagrams.')
    refs=[reference('data/documentation/issp/2009_ua_questionnaire.pdf',pages09,[2009],'https://doi.org/10.4232/1.12777','Ukrainian national questionnaire, '+code09),
          reference('data/documentation/issp/ZA7810_q_ua-ua.pdf',pages19,[2019],'https://doi.org/10.4232/1.13853','Ukrainian national questionnaire, '+code19)]
    return dict(question=question,label=label,polarity='Monthly UAH after all taxes, nominal prices; respondent estimates.' if kind=='money' else '',
                source_question=q,source_options=options,display_groups=rename(groups,mapping),references=refs,wording_notes=notes,
                wording_type='English translation/summary; Ukrainian 2019 wording below (shared stems and items joined)')


def build_audit():
    defs=pd.read_csv(ROOT/'docs/question_trend_definitions.csv')
    estimates=pd.read_csv(ROOT/'output/tables/question_trend_estimates.csv')
    trace=pd.read_csv(ROOT/'output/tables/question_trend_source_cells.csv')
    records=[]
    for d in defs.to_dict('records'):
        survey,item=d['survey'],d['item'];groups=json.loads(d['response_groups'])
        years=sorted(estimates.loc[estimates.survey.eq(survey)&estimates['item'].eq(item),'year'].astype(int).unique().tolist())
        if survey in ['WVS','EVS']:r=values_wording(survey,item,years,groups)
        elif survey=='Monitoring':r=monitoring_wording(item,years,groups,trace)
        elif survey=='Pew':r=pew_wording(item,years,groups)
        elif survey=='ESS':r=ess_wording(item,years,groups)
        elif survey=='ISSP':r=issp_wording(item,years,groups)
        else:raise ValueError(survey)
        assert len(r['display_groups'])==len(groups)
        # A label change must not silently change group membership or order.
        assert list(r['display_groups'].values())==list(groups.values())
        r.update(chart_id=survey.lower()+'__'+item.lower(),survey=survey,item=item,years=years,
                 original_groups=groups,response_renames=dict(zip(groups,r['display_groups'])),audit_date='2026-09-29')
        r.setdefault('chart_note','');r.setdefault('isolated_years',[])
        records.append(r)
    assert len(records)==95 and len({r['chart_id'] for r in records})==95
    out=pd.DataFrame(records)
    for c in ['source_options','display_groups','references','wording_notes','years','original_groups','response_renames','isolated_years']:
        out[c]=out[c].map(lambda x:json.dumps(x,ensure_ascii=False))
    out.to_csv(AUDIT,index=False,encoding='utf-8-sig')
    print(f'Wording audit: {len(records)} charts; category membership unchanged. {AUDIT}')


def load_audit():
    data=pd.read_csv(AUDIT,keep_default_na=False).to_dict('records')
    for r in data:
        for c in ['source_options','display_groups','references','wording_notes','years','original_groups','response_renames','isolated_years']:
            r[c]=json.loads(r[c])
    return {r['chart_id']:r for r in data}


if __name__=='__main__':
    build_audit()
