"""Build the research note in Markdown and PDF from generated result tables.

Missing WVS data produces an explicitly labelled interim note, never a final one.
"""
from pathlib import Path
import json, re
from html import escape
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab import rl_config
import matplotlib
from analyze import ROOT, AGES, INDEX
from question_inventory import build_inventory

# Stable PDF metadata makes an unchanged rerun retain its visual-review hash.
rl_config.invariant = 1

OUT=ROOT/'output'; T=OUT/'tables'; ledger=[]
est=pd.read_csv(T/'estimates.csv');dist=pd.read_csv(T/'distributions.csv')
audit=pd.read_csv(T/'sample_audit.csv');missing=pd.read_csv(T/'missingness.csv')
index_diagnostics=pd.read_csv(T/'index_diagnostics.csv')
index_leave_out=pd.read_csv(T/'index_leave_one_out.csv')
pew_results=pd.read_csv(T/'pew_published_results.csv')
monitoring_results=pd.read_csv(T/'monitoring_estimates.csv')
latest_results=pd.read_csv(T/'latest_positive_shares.csv')
extended_results=pd.read_csv(T/'extended_microdata_shares.csv')
new_results={name:pd.read_csv(T/name) for name in ['attitude_correlations.csv','ideological_coherence.csv',
             'market_supporter_attitudes.csv','market_principle_rankings.csv']}
validation=json.loads((T/'validation.json').read_text())
coverage=json.loads((T/'coverage_status.json').read_text())
ess_results=pd.read_csv(T/'ess_estimates.csv')
issp_results=pd.read_csv(T/'issp_estimates.csv')

def issp(item,year,response='Agree',group='All',metric='estimate'):
    z=issp_results[issp_results.item.eq(item)&issp_results.year.eq(year)&issp_results.response.eq(response)&issp_results.age_group.eq(group)]
    assert len(z)==1,(item,year,response,group)
    value=float(z.iloc[0][metric])
    ledger.append(dict(table='issp_estimates.csv',survey='ISSP',item=item,year=year,response=response,age_group=group,metric=metric,value=value))
    return value

def issp_pair(item,year=2019,filename='issp_joint_agreement.csv'):
    z=pd.read_csv(T/filename);z=z[z.item.eq(item)&z.year.eq(year)]
    assert len(z)==1
    value=float(z.iloc[0].estimate)
    ledger.append(dict(table=filename,survey='ISSP',item=item,year=year,metric='estimate',value=value))
    return value

def gallery_figure(name,alt):
    from PIL import Image as PILImage
    path=OUT/'question_trends'/f'{name}.png'
    with PILImage.open(path) as im:aspect=im.height/im.width
    story.extend([Image(str(path),width=width,height=width*aspect),Spacer(1,5)])
    md.append(f'![{alt}](question_trends/{name}.png)\n')


def ess(item,year,response='Mean',group='All',metric='estimate'):
    z=ess_results[ess_results.item.eq(item)&ess_results.year.eq(year)&ess_results.response.eq(response)&ess_results.age_group.eq(group)]
    assert len(z)==1
    value=float(z.iloc[0][metric])
    ledger.append(dict(table='ess_estimates.csv',survey='ESS',item=item,year=year,response=response,age_group=group,metric=metric,value=value))
    return value

def ess_joint(item,filename='ess_joint_agreement.csv'):
    z=pd.read_csv(T/filename);z=z[z.item.eq(item)]
    assert len(z)==1
    value=float(z.iloc[0].estimate)
    ledger.append(dict(table=filename,survey='ESS',item=item,year=int(z.iloc[0].year),metric='estimate',value=value))
    return value

def val(year, metric='estimate', group='All', territory='survey_coverage', weighted=True, survey='LiTS', item='market'):
    row=est[(est.survey==survey)&(est.item==item)&(est.year==year)&(est.age_group==group)&(est.territory==territory)&(est.weighted==weighted)].iloc[0]
    n=float(row[metric]);ledger.append(dict(table='estimates.csv',survey=survey,item=item,year=year,age_group=group,territory=territory,weighted=weighted,metric=metric,value=n))
    return n

def share(year,response,denominator='valid'):
    row=dist[(dist.survey=='LiTS')&(dist.item=='market')&(dist.year==year)&(dist.age_group=='All')&(dist.territory=='survey_coverage')&(dist.denominator==denominator)&(dist.response==response)].iloc[0]
    n=float(row.estimate);ledger.append(dict(table='distributions.csv',survey='LiTS',item='market',age_group='All',territory='survey_coverage',year=year,response=response,denominator=denominator,metric='estimate',value=n))
    return n

def category(survey,year,item,response):
    row=dist[(dist.survey==survey)&(dist.item==item)&(dist.year==year)&(dist.age_group=='All')&(dist.territory=='survey_coverage')&(dist.denominator=='valid')&(dist.response==response)].iloc[0]
    n=float(row.estimate)
    ledger.append(dict(table='distributions.csv',survey=survey,item=item,age_group='All',territory='survey_coverage',year=year,response=response,denominator='valid',metric='estimate',value=n))
    return n

def sample_n(survey,year):
    n=int(audit[(audit.survey==survey)&(audit.year==year)].iloc[0].n_eligible)
    ledger.append(dict(table='sample_audit.csv',survey=survey,year=year,metric='n_eligible',value=n))
    return n

def diagnostic(survey,year,metric):
    r=index_diagnostics[index_diagnostics.survey.eq(survey)&index_diagnostics.year.eq(year)].iloc[0]
    n=float(r[metric]);ledger.append(dict(table='index_diagnostics.csv',survey=survey,year=year,metric=metric,value=n))
    return n

def leave_out(survey,year,omitted):
    r=index_leave_out[index_leave_out.survey.eq(survey)&index_leave_out.year.eq(year)&index_leave_out.omitted.eq(omitted)&index_leave_out.age_group.eq('All')].iloc[0]
    n=float(r.estimate);ledger.append(dict(table='index_leave_one_out.csv',survey=survey,year=year,omitted=omitted,age_group='All',metric='estimate',value=n))
    return n

def pew(year,group='All'):
    r=pew_results[pew_results.year.eq(year)&pew_results.age_group.eq(group)].iloc[0]
    n=float(r.estimate)
    ledger.append(dict(table='pew_published_results.csv',survey='Pew',year=year,
        item='transition_approval',age_group=group,denominator='all_adults',metric='estimate',value=n))
    return n

def monitoring(item,year):
    z=monitoring_results[monitoring_results.item.eq(item)&monitoring_results.year.eq(year)]
    assert len(z)==1
    n=float(z.iloc[0].estimate)
    ledger.append(dict(table='monitoring_estimates.csv',survey='Monitoring',item=item,year=year,
        age_group='All',denominator='all_respondents_as_published',metric='estimate',value=n))
    return n

def pct(v):return f'{v*100:.1f}'

def latest(survey,item,metric='estimate'):
    r=latest_results[latest_results.survey.eq(survey)&latest_results.item.eq(item)]
    assert len(r)==1
    row=r.iloc[0];n=float(row[metric])
    ledger.append(dict(table='latest_positive_shares.csv',survey=survey,item=item,year=int(row.year),metric=metric,value=n))
    return n

def computed(filename,survey,year,item,metric='estimate',battery=None):
    z=new_results[filename]
    z=z[z.survey.eq(survey)&z.year.eq(year)&z.item.eq(item)]
    if battery is not None:z=z[z.battery.eq(battery)]
    assert len(z)==1,(filename,survey,year,item,battery)
    n=float(z.iloc[0][metric])
    ledger.append(dict(table=filename,survey=survey,year=year,item=item,battery=battery,metric=metric,value=n))
    return n

def corr(survey,year,a,b,battery='core'):
    z=new_results['attitude_correlations.csv']
    match=z[z.survey.eq(survey)&z.year.eq(year)&z.battery.eq(battery)&
            z.item_1.isin([a,b])&z.item_2.isin([a,b])]
    assert len(match)==1
    return computed('attitude_correlations.csv',survey,year,match.iloc[0]['item'],battery=battery)

def coherence(survey,year,metric='mean_pairwise_correlation'):
    return computed('ideological_coherence.csv',survey,year,'core',metric,'core')

def rtext(value):return '0.00' if round(value,2)==0 else f'{value:.2f}'
def interval(year,group='All'):
    return f'{pct(val(year,group=group))} [{pct(val(year,"ci_low",group))}, {pct(val(year,"ci_high",group))}]'

fontdir=Path(matplotlib.get_data_path())/'fonts/ttf'
for name,file in [('Body','DejaVuSerif.ttf'),('BodyBold','DejaVuSerif-Bold.ttf'),('Sans','DejaVuSans.ttf'),('SansBold','DejaVuSans-Bold.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(fontdir/file)))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='BodyBold',italic='Body',boldItalic='BodyBold')
pdfmetrics.registerFontFamily('Sans',normal='Sans',bold='SansBold',italic='Sans',boldItalic='SansBold')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='Text',fontName='Body',fontSize=10.4,leading=15,spaceAfter=8,textColor=colors.HexColor('#17202a')))
styles.add(ParagraphStyle(name='SmallText',parent=styles['Text'],fontSize=8.5,leading=12,spaceAfter=6))
styles.add(ParagraphStyle(name='TitleCustom',fontName='SansBold',fontSize=24,leading=29,spaceAfter=12,textColor=colors.HexColor('#143454')))
styles.add(ParagraphStyle(name='HeadingCustom',fontName='SansBold',fontSize=16,leading=21,spaceAfter=10,textColor=colors.HexColor('#143454')))
styles.add(ParagraphStyle(name='SubheadingCustom',fontName='SansBold',fontSize=10.5,leading=14,spaceBefore=5,spaceAfter=6,textColor=colors.HexColor('#143454')))
styles.add(ParagraphStyle(name='Cell',fontName='Sans',fontSize=8.6,leading=11))
styles.add(ParagraphStyle(name='HeaderCell',parent=styles['Cell'],fontName='SansBold',textColor=colors.white))
story=[];md=[]
width=A4[0]-40*mm

def markup(s):
    s=escape(s)
    s=s.replace('\n','<br/>')
    s=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',s)
    s=re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)',r'<link href="\2" color="#235f99">\1</link>',s)
    return s

def p(s,small=False):
    story.append(Paragraph(markup(s),styles['SmallText' if small else 'Text']));md.append(s+'\n')
def h(s,level=2):
    style='TitleCustom' if level==1 else 'HeadingCustom' if level==2 else 'SubheadingCustom'
    story.append(Paragraph(markup(s),styles[style]));md.append('#'*level+' '+s+'\n')
def page():story.append(PageBreak());md.append('\n<!-- page break -->\n')
def table(headers,rows,weights=None,compact=False):
    cell=ParagraphStyle(name='AppendixCell',parent=styles['Cell'],fontSize=8,leading=10) if compact else styles['Cell']
    cells=[[Paragraph(markup(str(v)),styles['HeaderCell'] if i==0 else cell) for v in row] for i,row in enumerate([headers]+rows)]
    weights=weights or [1]*len(headers);widths=[width*w/sum(weights) for w in weights]
    tb=Table(cells,colWidths=widths,hAlign='LEFT',repeatRows=1)
    pad=4 if compact else 7
    tb.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#143454')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),pad),('BOTTOMPADDING',(0,0),(-1,-1),pad),('LINEBELOW',(0,1),(-1,-1),.4,colors.HexColor('#d8dde2'))]))
    story.extend([tb,Spacer(1,8)])
    md.append('| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+'\n'.join('| '+' | '.join(str(v).replace('\n','<br>') for v in r)+' |' for r in rows)+'\n')
def figure(name,alt):
    from PIL import Image as PILImage
    with PILImage.open(OUT/'figures'/f'{name}.png') as im: aspect=im.height/im.width
    story.append(Image(str(OUT/'figures'/f'{name}.png'),width=width,height=width*aspect));story.append(Spacer(1,5))
    md.append(f'![{alt}](figures/{name}.png)\n')

def score(survey,year,item,metric='estimate',group='All',territory='survey_coverage',weighted=True):
    return val(year,metric,group,territory,weighted,survey,item)

def vtext(survey,year,item,group='All'):
    return f'{score(survey,year,item,group=group):.2f}'

def score_interval(survey,year,item):
    return f'{score(survey,year,item):.2f}\n[{score(survey,year,item,"ci_low"):.2f}, {score(survey,year,item,"ci_high"):.2f}]'

full=all(coverage.values())
start=1991
stem='ukraine_market_attitudes' if full else 'ukraine_market_attitudes_interim'
state='Research note' if full else 'Interim research note — WVS pending'
short_labels={'private_ownership':'Private ownership','competition':'Competition','individual_responsibility':'Individual responsibility','income_incentives':'Income incentives'}

h(f'Pro-market attitudes in Ukraine, {start}–2020',1)
p(f'**{state} · 28 September 2026**')
p('With separate Monitoring evidence for 2021–2025, ESS evidence for 2005–2024, and ISSP evidence for 2008–2019.',small=True)
h('Questions, surveys and available years')
p('Coverage of all questions included in the analysis and latest-response appendix. Years are Ukrainian fieldwork years; ESS 2007 denotes the pooled December 2006–January 2007 round. Related subquestions share a row only when their year coverage is identical. Individual descriptions and codes are exported in question_year_inventory.csv.',small=True)
inventory = build_inventory()
table(['Question / question battery', 'Survey', 'Available years'],
      inventory[['question','survey','years']].values.tolist(), [5.5,1.2,3.3], compact=True)
page()
if not full:
    p('**Incomplete study:** EVS and LiTS have been analysed. WVS microdata remain unavailable because the archive download has failed. The requested 1996–2020 study is not yet complete. No WVS values have been imputed or copied from published charts.')
h('Attitudes moved differently across dimensions')
p('Ukrainians’ attitudes did not move uniformly towards or away from markets between 1991 and 2020. Private business and competition attracted support, while privatisation and a minimal economic role for the state were less popular. Younger adults generally scored higher on the pro-market index, but the age gap narrowed. WVS, EVS and LiTS are combined with published results from Pew and the Institute of Sociology’s Ukrainian Society monitoring. A separate extension covers later monitoring waves.')
if full:
    p(f'WVS shows a rebound after 2011, rather than a steady long-run rise. From 2011 to 2020, income incentives moved from {vtext("WVS",2011,"income_incentives")} to {vtext("WVS",2020,"income_incentives")}, and individual responsibility from {vtext("WVS",2011,"individual_responsibility")} to {vtext("WVS",2020,"individual_responsibility")}. Yet the 2020 private-ownership mean of {vtext("WVS",2020,"private_ownership")} remained below {vtext("WVS",1996,"private_ownership")} in 1996. All scores run from 1 to 10, with higher values favouring the market-oriented endpoint.')
else:
    p(f'In EVS, support for income incentives fell from {vtext("EVS",2008,"income_incentives")} in 2008 to {vtext("EVS",2020,"income_incentives")} in 2020 on the ten-point scale.')
figure('national_dimension_trends','Separate national trends in ownership, competition, individual responsibility and income incentives')
if full:
    p(f'EVS shows a decline in support for income incentives from {vtext("EVS",2008,"income_incentives")} in 2008 to {vtext("EVS",2020,"income_incentives")} in 2020, while ownership and competition changed little. Both surveys place competition among the most market-oriented attitudes in 2020, and private ownership among the least.',small=True)
else:
    p('All estimates concern attitudes before the full-scale invasion. The endpoint is 2020 for EVS and 2016 for LiTS. Approximate uncertainty intervals are reported in the appendix and aggregate tables; changing territorial coverage is addressed below.',small=True)

page();h('WVS and EVS reach similar scores in 2020')
p('The WVS and EVS pro-market index averages ownership, competition, individual responsibility and income incentives on a 0–100 scale, giving each equal weight. Higher scores mean more market-oriented answers. The LiTS index is the percentage choosing a market economy over the planned-economy and indifferent responses.')
figure('national_index_trends','Separate WVS and EVS four-item indices and LiTS market-preference indicator, with approximate 95% confidence intervals')
p(f'The WVS index falls from {score("WVS",1996,INDEX):.1f} in 1996 to {score("WVS",2011,INDEX):.1f} in 2011, then returns to {score("WVS",2020,INDEX):.1f} in 2020, close to its starting level. EVS falls from {score("EVS",1999,INDEX):.1f} in 1999 to {score("EVS",2008,INDEX):.1f} in 2008 and {score("EVS",2020,INDEX):.1f} in 2020. Despite their different earlier paths, the two surveys give very similar summary scores in 2020.')
p('The similar 2020 averages contain a different mix of views. WVS records stronger support for private ownership and competition; EVS records stronger support for individual responsibility and income incentives. Comparing the surveys therefore reveals both agreement in the overall score and differences in its components.')
p(f'The EVS decline after 2008 is concentrated in income incentives. Without this component, the index changes by just {leave_out("EVS",2020,"income_incentives")-leave_out("EVS",2008,"income_incentives"):+.1f} points, compared with {score("EVS",2020,INDEX)-score("EVS",2008,INDEX):+.1f} points for all four components, using the same respondents. The main shift was towards income equality, with much less movement in views about ownership, competition and individual responsibility.')
h('LiTS also separates competition from income incentives',3)
p(f'The expanded questionnaire audit adds three economic scales previously omitted from LiTS. In 2016, {latest("LiTS","competition"):.1f}% chose the pro-competition half of its scale and {latest("LiTS","private_ownership"):.1f}% the private-ownership half, but only {latest("LiTS","income_incentives"):.1f}% favoured income differences as incentives. Meanwhile, {latest("LiTS","reduce_gap"):.1f}% agreed that the rich–poor gap should shrink. Support for competition coexisted with a preference for greater equality.',small=True)

page();h('Private business and privatisation followed different paths')
p(f'The Institute of Sociology’s monitoring asks directly about developing private business. Approval rose from {monitoring("private_business",1992):.1f}% in 1992 to {monitoring("private_business",2014):.1f}% in 2014, the last verified wave of this question. Support for transferring state assets into private ownership moved in the opposite direction.')
figure('monitoring_business_privatisation','Monitoring: approval of private business and separate privatisation series, observed years through 2020')
p(f'Positive attitudes to small-enterprise privatisation fell from {monitoring("privatise_small",1992):.1f}% in 1992 to {monitoring("privatise_small",2018):.1f}% in 2018. Land privatisation fell much more, from {monitoring("privatise_land",1992):.1f}% to {monitoring("privatise_land",2018):.1f}%. Large-enterprise privatisation was already unpopular at the start: support moved from {monitoring("privatise_large",1992):.1f}% to {monitoring("privatise_large",2018):.1f}%.')
p(f'A **privatisation support index**, averaging the three affirmative shares, falls from {monitoring("privatisation_support_index",1992):.1f} in 1992 to {monitoring("privatisation_support_index",2006):.1f} in 2006 and {monitoring("privatisation_support_index",2018):.1f} in 2018. Attitudes to private business improved while views of privatisation remained negative.',small=True)
h('Existing private ownership attracted more support',3)
p(f'In the separate ownership module, approval of existing private ownership rose between 2013 and 2020: from {monitoring("existing_private_small",2013):.1f}% to {monitoring("existing_private_small",2020):.1f}% for small enterprises, {monitoring("existing_private_large",2013):.1f}% to {monitoring("existing_private_large",2020):.1f}% for large enterprises, and {monitoring("existing_private_land",2013):.1f}% to {monitoring("existing_private_land",2020):.1f}% for land. Opposition to renationalising small enterprises also rose, from {monitoring("renationalise_small",2013):.1f}% to {monitoring("renationalise_small",2020):.1f}%. Acceptance of private ownership was strongest for small businesses.',small=True)

page();h('Younger adults were more pro-market; age gaps narrowed')
figure('index_age_trends','WVS and EVS four-item indices and LiTS direct market preference by age, with approximate 95% confidence intervals')
for survey in ['WVS','EVS']:
    if not coverage.get(survey):continue
    first=min(est.loc[est.survey.eq(survey),'year'])
    p(f'**{survey}.** Index scores for ages 18–34 and 55+ were {score(survey,first,INDEX,group="18-34"):.1f} and {score(survey,first,INDEX,group="55+"):.1f} in {first}; by 2020 they were {score(survey,2020,INDEX,group="18-34"):.1f} and {score(survey,2020,INDEX,group="55+"):.1f}. Younger adults remained more market-oriented overall, but the gap shrank.')
p(f'**LiTS.** Market preference among ages 18–34 fell from {pct(val(2006,group="18-34"))}% in 2006 to {pct(val(2016,group="18-34"))}% in 2016. The oldest group remained near one quarter ({pct(val(2006,group="55+"))}% and {pct(val(2016,group="55+"))}%). Ages 35–54 led in the final wave at {pct(val(2016,group="35-54"))}%.')
h('Competition converged; an incentives gap emerged',3)
p(f'WVS competition means were almost identical across age groups in 2020: {vtext("WVS",2020,"competition","18-34")}, {vtext("WVS",2020,"competition","35-54")} and {vtext("WVS",2020,"competition","55+")}, from youngest to oldest. In EVS, support for income incentives fell after 2008 from {vtext("EVS",2008,"income_incentives","18-34")} to {vtext("EVS",2020,"income_incentives","18-34")} among ages 18–34 and from {vtext("EVS",2008,"income_incentives","55+")} to {vtext("EVS",2020,"income_incentives","55+")} among ages 55+. The larger fall among older adults opened a gap where there had been almost none.',small=True)
p(f'Pew’s 2019 transition-approval figures also show an age divide: {pew(2019,"18-34"):.0f}% among ages 18–34, {pew(2019,"35-59"):.0f}% among ages 35–59 and {pew(2019,"60+"):.0f}% among ages 60+. Approval was much lower among the oldest group. [Pew age chart, p. 23](https://www.pewresearch.org/global/wp-content/uploads/sites/2/2019/10/Pew-Research-Center-Value-of-Europe-report-FINAL-UPDATED.pdf#page=24).',small=True)

page();h('Support for markets included a substantial state role')
p(f'LiTS market preference fell from {pct(val(2006))}% in 2006 to {pct(val(2010))}% in 2010, then remained at {pct(val(2016))}% in 2016. Its alternatives are a planned economy under some circumstances and indifference to the system.')
p(f'Monitoring gives respondents an explicit mixed-economy option. In 2020, {monitoring("state_role_mixed_state_market",2020):.1f}% preferred combining state management with market methods, {monitoring("state_role_planned_economy",2020):.1f}% wanted a return to planning, and only {monitoring("state_role_minimal_state_market",2020):.1f}% preferred minimal state involvement. The mixed option was the most popular in every observed wave from 2002 to 2020. Support for markets often meant a continuing economic role for government.')
h('Pew: approval of the transition recovered after 2011',3)
p(f'Approval of the move from a state-controlled to a market economy rose from {pew(2011):.0f}% in 2011 to {pew(2019):.0f}% in 2019, a {pew(2019)-pew(2011):.0f}-percentage-point recovery. Together with the WVS rebound and growing acceptance of existing private ownership in Monitoring, this points to a more favourable assessment of markets during the 2010s.',small=True)
p(f'Pew’s separate 2015 survey makes the coexistence of markets and social protection especially clear: {latest("Pew","free_market_better"):.0f}% agreed that most people were better off in a free-market economy, while {latest("Pew","government_care_poor"):.0f}% said government should care for very poor people unable to look after themselves.',small=True)
table(['Pew approval (%)','1991 benchmark','2009','2011','2019'],[['Published share']+[f'{pew(y):.0f}' for y in [1991,2009,2011,2019]]],[1.5,1.5,1,1,1])
p('Source: [Pew 2019 topline, Q16a, p. 150](https://www.pewresearch.org/global/wp-content/uploads/sites/2/2019/10/Pew-Research-Center-Value-of-Europe-Topline-for-Release-FINAL.pdf#page=35).',small=True)
h('Later monitoring waves: 2021 and the wartime years',3)
p(f'The 2021 monitoring still showed limited support for privatisation: {monitoring("privatise_small",2021):.1f}% for small enterprises, {monitoring("privatise_large",2021):.1f}% for large enterprises and {monitoring("privatise_land",2021):.1f}% for land. The three-sector index was {monitoring("privatisation_support_index",2021):.1f}.',small=True)
p('A new ownership-policy question in 2023–2025 favoured selective privatisation: sell state firms except those operating efficiently. This was the largest single response in each year. Broad privatisation attracted far less support.',small=True)
table(['Ownership policy (% of all respondents)','2023','2024','2025'],[
    [label]+[f'{monitoring("ownership_policy_"+item,y):.1f}' for y in [2023,2024,2025]]
    for item,label in [('privatise_except_efficient_state_firms','Privatise except efficient state firms'),
                       ('broad_privatisation','Broad privatisation'),('nationalise','Nationalise private enterprises')]
],[3.5,1,1,1])
p('These later waves form a separate extension. The main cross-survey analysis and age comparisons end in 2020.',small=True)

page();h('ESS: redistribution remains popular, but less so than in 2013')
p(f'ESS extends the direct redistribution question to 2024. Agreement that government should reduce income differences fell from {ess("gincdif",2013,"Agree"):.1f}% in 2013 to {ess("gincdif",2022,"Agree"):.1f}% in January–February 2022 and {ess("gincdif",2024,"Agree"):.1f}% in 2024. Earlier results fluctuated: {ess("gincdif",2005,"Agree"):.1f}% in 2005, {ess("gincdif",2007,"Agree"):.1f}% in 2006–07, {ess("gincdif",2009,"Agree"):.1f}% in 2009 and {ess("gincdif",2011,"Agree"):.1f}% in 2011. Support remains a clear majority; its long-run path is not a steady decline.')
story.append(Image(str(OUT/'question_trends/ess__gincdif.png'),width=170*mm,height=170*mm*7.4/11))
md.append('![ESS redistribution: all response categories and 95% intervals](question_trends/ess__gincdif.png)\n')
h('Social protection is central to the idea of democracy',3)
p(f'In 2022, protecting citizens against poverty scored {ess("gvctzpv",2022):.2f} out of 10 for its importance to democracy; reducing income differences scored {ess("grdfinc",2022):.2f}. Ratings of what government actually delivered were only {ess("gvctzpvc",2022):.2f} and {ess("grdfincc",2022):.2f}. The same gap appeared in 2013. Strong demand for social protection coexisted with a very poor assessment of its delivery.',small=True)
p('The HTML now includes six ESS question trends: redistribution; immigration’s economic effects; and the importance and perceived delivery of the two social-democratic principles. The separate Ukrainian ESS10 study was fielded on 18 January–8 February 2022; the supplied ESS11 interviews started between 30 April and 3 July 2024.',small=True)

page();h('ESS: equality and rewards for effort coexist within respondents')
p(f'In the 2009 welfare module, {latest("ESS","dfincac"):.1f}% agreed that large income differences were acceptable as rewards for talents and effort. At the same time, {latest("ESS","smdfslv"):.1f}% said a fair society should have small differences in living standards, and {ess("gincdif",2009,"Agree"):.1f}% favoured government action to reduce income gaps.')
p(f'These are partly the same people: {ess_joint("gincdif__dfincac"):.1f}% of all adults endorsed both redistribution and large income differences as rewards; {ess_joint("smdfslv__dfincac"):.1f}% endorsed both small living-standard gaps and large income differences as rewards. The correlation between the latter two agreement scales was just {ess_joint("dfincac__smdfslv","ess_correlations.csv"):.2f}. The tension between equality and incentives is visible within individual answers, not just across survey averages.')
h('Government responsibility was broad, with unemployment provision lowest',3)
table(['Government responsibility, ESS 2009','Mean, 0–10'],[
    [label,f'{ess(item,2009):.2f}'] for item,label in [
        ('gvhlthc','Healthcare for sick people'),('gvslvol','A reasonable living standard in old age'),
        ('gvjbevn','A job for everyone who wants one'),('gvcldcr','Childcare for working parents'),
        ('gvpdlwk','Paid leave to care for sick family members'),('gvslvue','A reasonable living standard for unemployed people')]
],[5.4,1.3],compact=True)
p(f'Only {latest("ESS","sblazy"):.1f}% agreed that social benefits made people lazy, and {latest("ESS","sbstrec"):.1f}% that they put too great a strain on the economy. The tax-and-spending trade-off averaged {ess("ditxssp",2009):.2f} on a scale from 0 (cut both substantially) to 10 (increase both substantially). These one-wave questions add detail about the scope of state provision.',small=True)
h('The recent waves add labour regulation and economic openness',3)
p(f'In 2024, {latest("ESS","fineqpy"):.1f}% favoured fining firms that pay men more than women for the same work, and {latest("ESS","eqparlv"):.1f}% favoured requiring parents to take equal amounts of parental leave. Immigration’s perceived economic effect improved from {ess("imbgeco",2013):.2f} in 2013 to {ess("imbgeco",2022):.2f} in 2022 and {ess("imbgeco",2024):.2f} in 2024 on the 0–10 bad-to-good scale. These measure specific regulations and economic beliefs.',small=True)
p(f'Redistribution support in 2024 was {ess("gincdif",2024,"Agree","18-34"):.1f}% among ages 18–34, {ess("gincdif",2024,"Agree","35-54"):.1f}% among ages 35–54 and {ess("gincdif",2024,"Agree","55+"):.1f}% among ages 55+. All ESS age-group estimates and intervals are exported.',small=True)

page();h('ISSP: redistribution remains overwhelmingly popular')
p(f'ISSP finds little change in the demand for a strong redistributive state between 2009 and 2019. Agreement that government should reduce income differences was {issp("redistribution",2009):.1f}% and {issp("redistribution",2019):.1f}%, respectively. Support for providing unemployed people with a decent living was similarly high: {issp("unemployed_living",2009):.1f}% and {issp("unemployed_living",2019):.1f}%.')
table(['Position supported','2009','2019'],[[label,f'{issp(key,2009,response):.1f}%',f'{issp(key,2019,response):.1f}%'] for key,label,response in [('income_gap','Income differences are too large','Agree'),('redistribution','Government should reduce income differences','Agree'),('unemployed_living','Government should ensure a decent living for unemployed people','Agree'),('tax_rich','Richer people should pay higher taxes','Higher taxes')]], [4.7,1,1])
p(f'In 2019, {issp("responsibility",2019,"Government"):.1f}% named government as bearing the greatest responsibility for reducing income differences. Only {issp("gov_success",2019,"Successful"):.1f}% thought government was successful at doing so. The demand for redistribution sits alongside dissatisfaction with its delivery.')
h('More acceptance of buying better services',3)
p(f'The share considering it fair that richer people can buy better healthcare rose from {issp("buy_health",2009,"Fair"):.1f}% to {issp("buy_health",2019,"Fair"):.1f}%. For better education for their children, it rose from {issp("buy_education",2009,"Fair"):.1f}% to {issp("buy_education",2019,"Fair"):.1f}%. Yet majorities still called both arrangements unfair in 2019: {issp("buy_health",2019,"Unfair"):.1f}% for healthcare and {issp("buy_education",2019,"Unfair"):.1f}% for education. Much of the growth in acceptance came alongside fewer mixed or uncertain answers.')
p('This is a selective shift: greater acceptance of paying for better services occurred without a comparable retreat from support for redistribution.')
p(f'Younger adults were more accepting of unequal healthcare access in 2019: {issp("buy_health",2019,"Fair","18-34"):.1f}% of those aged 18–34 called it fair, compared with {issp("buy_health",2019,"Fair","55+"):.1f}% of those aged 55+. Redistribution nevertheless attracted large majorities in both groups: {issp("redistribution",2019,"Agree","18-34"):.1f}% and {issp("redistribution",2019,"Agree","55+"):.1f}%, respectively.',small=True)


page();h('Rewarding effort does not imply accepting large inequality')
p(f'In 2019, {issp("skill_premium",2019):.1f}% agreed that workers need extra pay to acquire skills and qualifications. {issp("pay_performance",2019,"Essential / very important"):.1f}% regarded how well a job is done as essential or very important in determining pay. But only {issp("inequality_prosperity",2019):.1f}% agreed that large income differences are necessary for prosperity.')
p(f'These positions coexist within respondents. {issp_pair("redistribution__skill_premium"):.1f}% of all adults supported both government redistribution and extra pay for acquiring skills; {issp_pair("redistribution__pay_performance"):.1f}% supported redistribution and regarded job performance as essential or very important for pay. The corresponding correlations were {issp_pair("redistribution__skill_premium",filename="issp_correlations.csv"):.2f} and {issp_pair("redistribution__pay_performance",filename="issp_correlations.csv"):.2f}: attitudes towards rewards and redistribution were only weakly connected.')
gallery_figure('issp__buy_health','ISSP fairness of buying better healthcare, 2009 and 2019')
p('ISSP sharpens the overall picture: Ukrainians widely endorse differentiated rewards, but this does not translate into support for large income gaps or a smaller redistributive role for government.',small=True)

page();h('Which market principles attract the most support?')
p(f'**Competition attracts consistently broad support.** The pro-competition half of the scale attracts {latest("WVS","E039"):.1f}% in WVS 2020, {latest("EVS","E039"):.1f}% in EVS 2020 and {latest("LiTS","competition"):.1f}% in LiTS 2016, ranking first by affirmative share. By mean score, EVS puts income incentives slightly ahead of competition ({vtext("EVS",2020,"income_incentives")} versus {vtext("EVS",2020,"competition")}). Private ownership ranks second in LiTS by both measures.')
figure('market_principle_ranking','Market-oriented response shares for the main principles, separately ranked within each latest survey wave, with approximate 95% confidence intervals')
p(f'**Private enterprise and international exchange also attract substantial support.** Monitoring 2020 records {monitoring("existing_private_small",2020):.1f}% approval of existing small-business ownership, compared with {monitoring("existing_private_large",2020):.1f}% for large enterprises and {monitoring("existing_private_land",2020):.1f}% for land. In Pew 2014, {latest("Pew","trade_good"):.0f}% welcomed growing trade and business ties, and {latest("Pew","foreign_factories"):.0f}% viewed new foreign-owned factories positively.',small=True)
p(f'**A smaller state and greater income inequality have less consistent appeal.** Individual responsibility over government provision attracts {latest("WVS","E037"):.1f}% in WVS 2020 and {latest("EVS","E037"):.1f}% in EVS 2020. LiTS 2016 records only {latest("LiTS","income_incentives"):.1f}% on the income-incentive side. Ukrainians endorse competition and specific forms of private business more widely than the full set of market-oriented positions.',small=True)

page();h('Do these attitudes form a coherent market ideology?')
p(f'**Market attitudes are fragmented and sometimes pull in opposing directions.** The average correlation across the main item pairs is {rtext(coherence("WVS",2020))} in WVS 2020, {rtext(coherence("EVS",2020))} in EVS 2020 and {rtext(coherence("LiTS",2016))} in LiTS 2016. A positive correlation means that the same respondents tend to favour both market-oriented positions; a value near zero means little linear association.')
figure('attitude_correlation_matrices','Weighted within-wave Pearson correlations: four market attitudes in WVS and EVS 2020 and three in LiTS 2016')
p(f'**EVS shows a partial market cluster.** Private ownership, competition and individual responsibility are positively related: their correlations range from {corr("EVS",2020,"private_ownership","competition"):.2f} to {corr("EVS",2020,"private_ownership","individual_responsibility"):.2f}. Income incentives sit outside that cluster. In LiTS, ownership and competition have a clearer link ({corr("LiTS",2016,"private_ownership","competition"):.2f}), while their links with income incentives are {corr("LiTS",2016,"private_ownership","income_incentives"):.2f} and {corr("LiTS",2016,"competition","income_incentives"):.2f}.',small=True)
p(f'**Some attitudes run against the expected ideological pattern.** In WVS 2020, competition and private ownership are modestly related ({corr("WVS",2020,"private_ownership","competition"):.2f}), but competition is negatively related to individual responsibility ({corr("WVS",2020,"competition","individual_responsibility"):.2f}). People more favourable to competition tend to favour government provision more, not less. The average correlation of {rtext(coherence("WVS",1996))} in 1996 falls to approximately zero in 2020.',small=True)
p(f'**Market preference often includes redistribution.** Among LiTS 2016 respondents who explicitly prefer a market economy, {computed("market_supporter_attitudes.csv","LiTS",2016,"competition"):.1f}% favour competition and {computed("market_supporter_attitudes.csv","LiTS",2016,"private_ownership"):.1f}% favour private ownership; {computed("market_supporter_attitudes.csv","LiTS",2016,"reduce_gap"):.1f}% also want the rich-poor gap reduced. Only {computed("market_supporter_attitudes.csv","LiTS",2016,"income_incentives"):.1f}% favour larger income differences as incentives. This combination occurs within individuals, not just in national averages.',small=True)
p('**The inconsistencies are part of the finding.** Support for one market principle does not reliably carry over to the others. A popular mixed-economy label and weak ideological consistency are separate findings: the former comes from Monitoring’s system-choice question, the latter from individual responses in WVS, EVS and LiTS. Calling the overall pattern a coherent social-market philosophy would smooth over these tensions.',small=True)

page();h('Limitations')
p('**ISSP sampling and monetary comparisons.** GESIS releases Ukraine 2019 separately because its sampling departed from ISSP standards. It excludes occupied territory, and the released files lack verified sampling-cluster identifiers; its confidence intervals are approximate. Salary answers are respondents’ estimates or preferences in nominal hryvnias, with substantial nonresponse and occasional extreme values. Their growth across years also reflects inflation and should not be read as an attitude shift.',small=True)
p('**ESS coverage and weighting.** The 2024 sample describes residents in the areas accessible during wartime; people abroad and in occupied or unsafe areas are not fully represented. Supplied 2024 post-stratification weights equal the design weights, so they do not add a separate demographic calibration. Estimates excluding Crimea/Sevastopol and Donetsk/Luhansk consistently across ESS rounds, and unweighted estimates, are exported. They cannot reconstruct the population absent from the later samples.',small=True)
p('**Territorial coverage changed.** Later surveys exclude Crimea/Sevastopol and occupied parts of Donetsk/Luhansk. Consistent regional exclusions are checked where microdata permit; they cannot fully account for displacement. This check is unavailable for WVS 2006, LiTS 2006 and the published Pew/Monitoring aggregates. Wartime surveys cover a further changed population.',small=True)
p('**Some estimates are less precise.** In EVS 2020, some respondents count much more heavily than others when answers are adjusted to represent the population. Its wider confidence intervals reflect this. WVS/EVS intervals are approximate because the files lack verified information on how respondents were grouped for sampling.',small=True)
p('**Some questions measure different things.** WVS and EVS interviewed at different times in 2020 and differ slightly in competition and incentives wording. Pew’s 1991 question concerns establishing markets; later waves assess the transition. Monitoring’s privatisation, existing ownership and renationalisation items stay separate. In particular, its 2020 land-ownership result does not extend the older land-privatisation series. The 2023–2025 policy question is also separate; interview mode changes and simplified 2025 wording limit fine comparisons.',small=True)
p(f'**Missing answers affect who is represented.** The four-item index excludes respondents who did not answer every item: {diagnostic("WVS",2020,"missing_weighted_pct"):.1f}% of the weighted WVS sample and {diagnostic("EVS",2020,"missing_weighted_pct"):.1f}% of EVS in 2020. Missing LiTS answers increased from {pct(share(2006,0,"all_eligible"))}% in 2006 to {pct(share(2010,0,"all_eligible"))}% in 2010 and {pct(share(2016,0,"all_eligible"))}% in 2016; reported shares use valid answers.',small=True)
p('**Index coverage differs.** WVS/EVS summarise four attitudes; LiTS measures direct market preference; Monitoring summarises expressed support for privatisation. They have different meanings, so their levels are not interchangeable. Age comparisons describe changing groups of respondents, without separating ageing from generational change.',small=True)
p('**Published tables have limits.** Pew and Monitoring do not supply item-specific confidence intervals or joint responses for within-person correlations. Monitoring’s national tables cannot reproduce age-group or complete-case indices. Pew’s published age bands are retained as labelled. Monitoring’s published age indices contain unresolved inconsistencies and are excluded.',small=True)
page();h('Methods appendix: measurement and estimation')
table(['Outcome','Source fields','Analysis coding'],[['Private ownership','WVS / EVS E036','11 − x'],['Competition','WVS / EVS E039','11 − x'],['Individual responsibility','WVS / EVS E037','11 − x'],['Income incentives','WVS / EVS E035','x'],['Economic-system choice','LiTS q310 / q411','Keep categories 1, 2, 3']],[2.2,2,2])
p('Coding uses the harmonised trend-file fields above; out-of-range and missing codes are excluded. Each wave samples adults aged 18+. Weighted means use S017 in WVS/EVS and weight_0, weight and weight_population in successive LiTS waves. The four-item index is 100 × (mean of aligned items − 1) / 9, using all four answers. LiTS codes market preference as 100 and both other valid responses as 0.',small=True)
p('Approximate 95% confidence intervals use weighted-ratio linearization, with sampling clusters in LiTS and respondents in WVS/EVS, and t critical values. Index intervals are calculated from individual index scores. The question crosswalk documents wording, missing codes, weights and geography; README.md gives the full estimator and validation checks.',small=True)
p('Monitoring indicators add the relevant published response percentages, retaining undecided and missing answers in the denominator. Its 0–100 privatisation index is the equal mean of positive shares for small enterprises, large enterprises and land. Zero means no expressed support, including nonresponse; it does not imply unanimous opposition. The same three items are used in every wave.',small=True)

page();h('Methods appendix: estimates and sources')
p('National weighted means with approximate 95% intervals. Components use 1–10 scales; the index uses 0–100. Higher values favour the market-oriented endpoint. Each wave uses its surveyed territory.',small=True)
rows=[]
for survey in ['WVS','EVS']:
    for y in sorted(est.loc[est.survey.eq(survey),'year'].unique()):
        idx=f'{score(survey,y,INDEX):.1f}\n[{score(survey,y,INDEX,"ci_low"):.1f}, {score(survey,y,INDEX,"ci_high"):.1f}]\nn={int(score(survey,y,INDEX,"n_valid")):,}'
        rows.append([f'{survey} {y}\nn={sample_n(survey,y):,}']+[score_interval(survey,y,item) for item in short_labels]+[idx])
table(['Survey / year','Private ownership','Competition','Individual responsibility','Income incentives','Index 0–100'],rows,[1.05,1.35,1.35,1.4,1.35,1.35])
p('The first n is eligible adults; index n counts respondents answering all four items. Item-valid and age-specific counts and intervals are exported. LiTS national means and intervals appear in the national index chart; age groups appear in the age-trend chart.',small=True)
h('Reproduce the results',3)
p('Install requirements.txt and run python scripts/run.py. Outputs include harmonised data, CSV estimates, PNG/SVG charts and this note. note_number_trace.csv links reported estimates to tables; the Monitoring and extended published trace tables link indicators to source cells. The package includes full age-by-dimension, additional LiTS and Pew trend charts, and the questionnaire audit.',small=True)
h('Archive versions and documentation',3)
p('EVS (2022), [Trend File ZA7503 v3.0.0](https://doi.org/10.4232/1.14021). Inglehart et al. (eds., 2022), [WVS: All Rounds, Country-Pooled Datafile](https://doi.org/10.14281/18241.17), JD Systems Institute/WVSA; WVS-only TimeSeries 1981–2022 SPSS v5.0. [Ukraine 2020 report](https://ucep.org.ua/wp-content/uploads/2020/11/WVS_UA_2020_report_ENG_WEB.pdf). Source manifests record versions and hashes.',small=True)
p('[EBRD LiTS I–III files and questionnaires](https://www.ebrd.com/home/what-we-do/office-of-the-chief-economist/lits/life-in-transition-survey-data.html); [sampling annex](https://litsonline-ebrd.com/methodology-annex/index.htm). [LiTS IV coverage notes](https://www.ebrd.com/content/dam/ebrd_dxp/assets/pdfs/office-of-the-chief-economist/publications/life-in-transition-survey-iv/Life-in-Transition-IV-2024-Notes-Abbreviations-English.pdf) exclude Ukraine in 2022–23. Latest verified Ukrainian WVS/EVS fieldwork: 2020.',small=True)
p('Pew (2019), [European Public Opinion Three Decades After the Fall of Communism](https://www.pewresearch.org/global/2019/10/15/european-public-opinion-three-decades-after-the-fall-of-communism/), topline Q16a and age chart p. 23; [methodology](https://www.pewresearch.org/global/2019/10/15/methodology-43/).',small=True)
p('Institute of Sociology NAS Ukraine, [Ukrainian Society monitoring](https://isnasu.org.ua/publish/ukrainske-suspilstvo/issues.php): [Panina’s early tables](https://dif.org.ua/uploads/pdf/40574543644fd4df61d653.39323866.pdf); [2020 volume, pp. 443–447](https://isnasu.org.ua/assets/files/monitoring/mon2020.pdf#page=443); [2021 appendix, pp. 624–625](https://isnasu.org.ua/assets/files/monitoring/monitoring-2021dlya-tipografii.pdf#page=624); [2025 volume, p. 394](https://drive.google.com/file/d/1CeJIiK0ZLNJ0aHyPbXHrWO21ykIB6m7W/view). The Monitoring archive, question crosswalk and indicator definitions document sources and comparability.',small=True)
page();h('Methods appendix: attitude coherence')
p('The analysis measures whether respondents take similar positions across economic questions. WVS/EVS use the same four aligned 1–10 items as the descriptive index. LiTS uses ownership, competition and income incentives in 2010/2016. Each matrix uses respondents answering every item in its named battery, with original survey weights. The index remains an average of selected positions; low internal consistency means it should not be interpreted as a single underlying ideological trait.',small=True)
p('Pearson correlations use continuous response scores, not the positive/negative split used in the ranking chart. The mean correlation summarises all distinct pairs. Cronbach’s alpha summarises internal consistency; no pass/fail cutoff is imposed. Confidence intervals come from 2,000 bootstrap draws of respondents in WVS/EVS and sampling clusters in LiTS, preserving weights. They are approximate because verified strata and full design information are unavailable.',small=True)
rows=[]
for survey,years in [('WVS',[1996,2006,2011,2020]),('EVS',[1999,2008,2020]),('LiTS',[2010,2016])]:
    for year in years:
        mean=rtext(coherence(survey,year))
        lo=rtext(coherence(survey,year,'mean_pairwise_correlation_ci_low'))
        hi=rtext(coherence(survey,year,'mean_pairwise_correlation_ci_high'))
        rows.append([f'{survey} {year}',str(int(coherence(survey,year,'n_complete'))),
                     f'{mean} [{lo}, {hi}]',rtext(coherence(survey,year,'weighted_alpha'))])
table(['Survey / year','Complete n','Mean correlation [95% CI]','Cronbach alpha'],rows,[1.5,1.1,2.6,1.5],compact=True)
p('The exported checks include weighted Spearman correlations using weighted midranks, unweighted correlations, pairwise-complete samples, principal-component loadings, and the common three-item battery across WVS, EVS and LiTS. The broad pattern of partial rather than uniform association survives the rank and weighting checks. LiTS 2016’s ownership-competition link is weaker without weights, but remains positive.',small=True)
p('An extended LiTS matrix adds direct market preference (market=1; planned or indifferent=0) and opposition to reducing the income gap (reversed five-point agreement scale). The two-item market/redistribution comparison is also exported for 2006. Conditional shares among market supporters retain item-valid denominators and the existing cluster-based interval estimator. Questions about institutional trust, what democracy means, or mutually exclusive spending choices are not assigned a common pro-market direction.',small=True)
p('New outputs: market_principle_rankings.csv, attitude_correlations.csv, ideological_coherence.csv, coherence_pc_loadings.csv and market_supporter_attitudes.csv. coherence_question_definitions.csv records LiTS source codes and directions; the existing question crosswalk covers WVS/EVS. Correlation matrices and the over-time coherence chart are exported as PNG/SVG. These results concern the recorded economic preferences, not whether people reason logically or identify with a political ideology.',small=True)

page();h('Methods appendix: ESS extension')
p('The supplied files cover Ukraine in rounds 2–6, 10 and 11. Estimates use adults aged 18+ with known age and positive pspwght. This weight already includes the design weight; the two are not multiplied. Within a Ukrainian wave, the population-size multiplier is constant and does not affect weighted means or percentages. Each respondent appears only once per round. No broad ESS pro-market index is constructed: the repeated items do not span ownership, competition and incentives.',small=True)
p('Round 2 was fielded in January–March 2005, confirmed in the official ESS2 documentation report, p. 204. Round 3 spans December 2006–January 2007; it is pooled as one survey observation, labelled 2006–07 and placed at 2007 in numeric year fields. Rounds 4–6 were fielded in 2009, 2011 and 2013. Round 10 interview starts confirm 18 January–8 February 2022. A few recorded interview end timestamps extend later; start timestamps and the national team’s fieldwork description agree on the pre-invasion collection period. Round 11 interview starts in the supplied file range from 30 April to 3 July 2024.',small=True)
p('Numeric ratings retain their original 0–10 direction and show means among valid ratings. Agreement categories are combined into agree/disagree, retaining the middle category and nonresponse. Categorical shares use all eligible adults. The latest affirmative appendix follows its existing midpoint convention for numeric questions: 6–10 on the original 0–10 scale, with the response explicitly named. Those threshold shares are not used in the ESS numeric charts.',small=True)
p('For 2022 and 2024, 95% intervals use with-replacement Taylor linearization of weighted ratio estimates, with the supplied sampling strata and primary sampling units. All sampled clusters remain in adult and age-group domain calculations. Degrees of freedom equal clusters minus strata; no finite-population correction is applied. Earlier supplied rounds lack cluster/stratum identifiers, so their intervals use approximate weighted respondent linearization. Post-stratification weights are treated as fixed. The 2024 weight equals the design weight in this file.',small=True)
p('Sensitivity tables repeat estimates without weights and on a consistent exclusion of Crimea/Sevastopol and Donetsk/Luhansk oblasts. Region codes are mapped separately for older rounds, the related ESS10 study and ESS11. The 2009 joint-agreement estimates count adults who agreed with both named propositions; missing answers remain in the all-adult denominator. Correlations use weighted pairwise-valid original agreement scales, reversed so higher means stronger agreement. They describe the specified pair of propositions, not a general market-ideology score.',small=True)
p('Reproduce with python scripts/ess_analysis.py, then the usual inventory, appendix, chart and note stages in scripts/run.py. ess_estimates.csv contains all responses, means, age groups and intervals; ess_sensitivity.csv contains robustness estimates; ess_correlations.csv and ess_joint_agreement.csv contain the within-person comparisons. All reported ESS estimates are linked to generated results in note_number_trace.csv.',small=True)
p('ESS: supplied integrated editions 2/3.6, 3/3.7, 4/4.6, 5/3.6, 6/2.7 and 11/4.2, downloaded through the [ESS data portal](https://www.europeansocialsurvey.org/data-portal); the separate [Ukrainian ESS10 study, edition 4](https://github.com/KSE-Sociological-Center/ESS10_Ukraine), with its Ukrainian questionnaire and weighting description. ess_question_crosswalk.csv records wording, codes, missingness and comparability; ess_variable_catalogue.csv records selection decisions. Source files and versions are hashed in ess.json.',small=True)

page();h('Methods appendix: ISSP extension')
p('The official participation inventory lists Ukraine in Religion III (2008), Social Inequality IV (2009) and Social Inequality V (2019). These are the verified Ukrainian ISSP waves; Role of Government and Work Orientations do not supply Ukrainian observations. The analysis uses ZA4950 v2.3.0, ZA5400 v4.0.0 and the separate Ukraine release ZA7810 v1.0.0. Ukraine is not in the integrated 2019 ZA7600 file.',small=True)
p('Fieldwork took place in October 2008, June 2009, and 31 August–14 September 2019. All samples are restricted to adults aged 18+ with known age and positive WEIGHT. Categorical percentages retain all eligible adults, including nonresponse. Numeric means use valid answers. Ninety-five percent intervals use weighted respondent linearization and t critical values, treating weights as fixed. Age groups are 18–34, 35–54 and 55+.',small=True)
p('The audit retains business/industry confidence from 2008, and economic policy preferences, inequality beliefs, pay criteria, perceived mobility, class conflict and earnings questions from the inequality modules. Every retained item has valid Ukrainian responses. The optional 2019 global-income fairness item v66 is unavailable and excluded. Personal income, own-pay satisfaction, social position, demographics and religious beliefs are outside this economic-attitude inventory.',small=True)
p('The question crosswalk records each original field, scale, missing code, response grouping and source hash. Ukrainian tax questions in both years ask whether richer people should pay higher taxes; they do not explicitly ask about a larger share of income. The note therefore describes higher taxes, without treating the answers as a direct measure of support for progressive tax rates.',small=True)
p('Robustness tables provide unweighted estimates and consistently exclude Crimea/Sevastopol and all of Donetsk/Luhansk in both inequality waves. The main patterns in redistribution and buying better services survive these checks. The 2019 release documents exclusions of occupied territory and sampling deviations; supplied weights adjust for sex and age. No sampling clusters are reconstructed from respondent identifiers.',small=True)
p('Within-person comparisons use weighted pairwise-valid Pearson correlations, with scales aligned towards stronger agreement, importance or perceived fairness. Joint support is the weighted share of all adults choosing either of the two strongest response categories on both named questions. These selected associations extend the coherence analysis without assigning all ISSP questions a common pro-market direction.',small=True)
p('The HTML adds every ISSP question observed at least twice and ending in 2019. Verbal ordinal scales combine positive and negative answers, retaining intermediate and missing categories; nominal questions keep all options. Earnings questions retain means with intervals in nominal monthly hryvnias after tax. The monetary audit exports missingness, extremes and a 99th-percentile winsorisation diagnostic; the main estimates keep all valid amounts.',small=True)
p('Sources: [ISSP participation](https://www.gesis.org/issp/ueberblick); [Religion III 2008](https://doi.org/10.4232/1.13161); [Social Inequality IV 2009](https://doi.org/10.4232/1.12777); [Ukraine Social Inequality V 2019](https://doi.org/10.4232/1.13853). Acquisition instructions, hashes and documentation are recorded in issp.json and issp_acquisition.json. The separate issp_variable_audit.md lists all selected questions and exclusions. Original microdata are excluded from export packages.',small=True)

page();h('Appendix: ISSP earnings questions, latest means')
p('ISSP 2019: monthly hryvnias after taxes, in 2019 prices. “Estimated” means what respondents think the occupation earns; “desired” means what they think it should earn. These are beliefs and preferences, not measured occupational wages. Means use valid monetary responses; approximate 95% intervals appear in brackets. A positive-response share is not meaningful for an open monetary question.',small=True)
rows=[]
for job,label in [('doctor','Doctor'),('chairman','Corporate chairman'),('shop','Shop assistant'),('worker','Unskilled factory worker'),('minister','Cabinet minister')]:
    vals=[]
    for kind in ['actual','ideal']:
        key='earn_'+kind+'_'+job
        vals.append(f'{issp(key,2019,"Mean"):,.0f}\n[{issp(key,2019,"Mean",metric="ci_low"):,.0f}, {issp(key,2019,"Mean",metric="ci_high"):,.0f}]')
    rows.append([label]+vals)
table(['Occupation','Estimated monthly pay','Desired monthly pay'],rows,[2,2,2],compact=True)
p('Respondents generally want higher pay for doctors, shop assistants and unskilled workers, and lower pay for corporate chairmen and cabinet ministers. They distinguish between occupations even while favouring a narrower overall income gap. The downloadable tables provide valid counts and missingness for every mean.',small=True)

page();h('Appendix: latest affirmative-response shares')
p('Each row uses the latest verified year for that question in the audited sources. “Affirmative” means the response specified below the question: support for state intervention is labelled as such. Related beliefs, trust and economic norms are included; they are not added to the fixed four-item market indices. The audit and exclusions are documented in variable_audit.md.',small=True)
p('WVS, EVS and LiTS: weighted shares among valid substantive responses, adults 18+. Ten-point bipolar scales count the five categories on the named side; the main charts retain means and 95% intervals. ESS and ISSP: weighted shares of all eligible adults, including nonresponse; numeric affirmative responses are 6–10 on the original 0–10 scale. Pew and Monitoring: published percentages of all respondents. Multi-answer rows need not sum to 100%. Detailed definitions and denominators are in latest_positive_shares.csv.',small=True)
p('Sources added by the audit: [Pew 2011](https://www.pewresearch.org/wp-content/uploads/sites/2/2011/12/Pew-Global-Attitudes-Former-Soviet-Union-Report-Topline.pdf), [Pew 2014 inequality](https://www.pewresearch.org/wp-content/uploads/sites/2/2014/10/Pew-Research-Center-Inequality-Report-FINAL-October-17-2014.pdf), [Pew 2014 trade](https://www.pewresearch.org/wp-content/uploads/sites/2/2014/09/Pew-Research-Center-Trade-Report-FINAL-September-16-2014.pdf), [Pew CEE 2015 fieldwork](https://assets.pewresearch.org/wp-content/uploads/sites/11/2017/05/09154356/Central-and-Eastern-Europe-Topline_FINAL-FOR-PUBLICATION.pdf), and the Monitoring tables listed in the audit. Questions below are concise English descriptions; source wording and page references are retained in the data documentation.',small=True)
for survey in ['WVS','EVS','LiTS','Pew','Monitoring','ESS','ISSP']:
    h(survey,3)
    z=latest_results[latest_results.survey.eq(survey)]
    rows=[]
    for r in z.itertuples():
        rows.append([r.question+'\n'+r.positive_definition,survey,str(r.year),f'{latest(survey,r.item):.1f}%'])
    table(['Question / affirmative response','Survey','Year','Share'],rows,[6.2,1.25,.85,.9],compact=True)

def footer(canvas,doc):
    canvas.saveState();canvas.setFont('Sans',8);canvas.setFillColor(colors.HexColor('#697681'))
    canvas.drawString(20*mm,12*mm,'Ukraine market attitudes · '+('Research note' if full else 'INTERIM: WVS pending'))
    canvas.drawRightString(A4[0]-20*mm,12*mm,str(doc.page));canvas.restoreState()

(OUT/'pdf').mkdir(exist_ok=True)
dest=OUT/'pdf'/f'{stem}.pdf'
doc=SimpleDocTemplate(str(dest),pagesize=A4,rightMargin=20*mm,leftMargin=20*mm,topMargin=18*mm,bottomMargin=20*mm,
    title=f'Pro-market attitudes in Ukraine, {start}–2020',author='Research note prepared for Valentyn Hatsko')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
(OUT/f'{stem}.md').write_text('\n'.join(md),encoding='utf8')
pd.DataFrame(ledger).drop_duplicates().to_csv(T/'note_number_trace.csv',index=False)
print(dest)

