"""Question-level trends: numeric means and complete categorical response sets."""
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib
import json
import textwrap

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

from analyze import ROOT
from figures import BLUE, INK
from chart_wording import load_audit

TABLES = ROOT / 'output/tables'
OUT = ROOT / 'output/question_trends'
CUTOFF = 2019
FIGSIZE = (11, 7.4)
SURVEYS = ['WVS', 'EVS', 'Pew', 'Monitoring', 'ESS', 'ISSP']
SOURCES = {'WVS': 'World Values Survey', 'EVS': 'European Values Study',
           'Pew': 'Pew Research Center', 'Monitoring': 'Institute of Sociology NAS Ukraine', 'ESS':'European Social Survey / Ukrainian ESS team'}
LABELS = {
    'E035': 'Income differences as incentives',
    'E036': 'Support for private ownership',
    'E037': 'Individual responsibility for provision',
    'E038': 'Unemployed people accepting any available job',
    'E039': 'Benefits of competition',
    'E040': 'Belief that hard work brings success',
    'E224': 'Taxing the rich as a feature of democracy',
    'E227': 'Unemployment aid as a feature of democracy',
    'E233A': 'Equalising incomes as a feature of democracy',
    'F114A': 'Rejecting unjustified benefit claims',
    'F116': 'Rejecting tax cheating',
    'E069_05': 'Confidence in labour unions',
    'E069_09': 'Confidence in the social security system',
    'E069_13': 'Confidence in major companies',
    'E069_41': 'Confidence in banks',
    'B008': 'Prioritising growth and jobs over the environment',
    'transition_approval': 'Approval of the transition to a market economy',
    'better_than_communism': 'Economic conditions judged better than under communism',
    'transition_business': 'Business people seen as benefiting from the transition',
    'transition_ordinary': 'Ordinary people seen as benefiting from the transition',
    'transition_politicians': 'Politicians seen as benefiting from the transition',
    'accept_market_values': 'Acceptance of post-independence market values',
    'enterprise_initiative': 'Importance of entrepreneurial opportunity',
    'market_relations_natural': 'Market relations accepted as a natural way of life',
    'start_business': 'Willingness to start a business',
    'trust_banks': 'Trust in banks',
    'trust_state_managers': 'Trust in managers of state enterprises',
    'trust_tax_authority': 'Trust in the tax authority',
    'trust_unions': 'Trust in trade unions',
    'land_ownership_rights': 'Support for full land ownership, including sale',
    'land_sales_agricultural': 'Support for buying and selling agricultural land',
    'ownership_policy_broad_privatisation': 'Support for broad privatisation',
    'ownership_policy_nationalise': 'Support for nationalising private enterprises',
    'ownership_policy_privatise_except_efficient_state_firms': 'Privatisation except for efficient state enterprises',
    'ownership_policy_retain_state_firms': 'Support for retaining existing state enterprises',
    'state_role_minimal_state_market': 'Preference for minimal state involvement',
    'state_role_mixed_state_market': 'Preference for combining state and market',
    'state_role_planned_economy': 'Preference for returning to a planned economy',
    'work_private_employer': 'Willingness to work for a private employer',
}
for sector, name in [('small', 'small enterprises'), ('large', 'large enterprises'), ('land', 'land')]:
    for prefix, wording in [('existing_private', 'Approval of existing private ownership'),
                            ('privatise', 'Support for privatisation'),
                            ('renationalise', 'Opposition to renationalisation'),
                            ('retrospective', 'Past privatisation judged worthwhile')]:
        LABELS[f'{prefix}_{sector}'] = f'{wording}: {name}'

POLARITY = {
    'E035': '1 = more equal incomes; 10 = greater income incentives',
    'E036': '1 = more state ownership; 10 = more private ownership',
    'E037': '1 = government responsibility; 10 = individual responsibility',
    'E038': '1 = right to refuse a job; 10 = accept any available job',
    'E039': '1 = competition harmful; 10 = competition beneficial',
    'E040': '1 = luck and connections; 10 = hard work brings success',
    'E224': '1 = not essential to democracy; 10 = essential to democracy',
    'E227': '1 = not essential to democracy; 10 = essential to democracy',
    'E233A': '1 = not essential to democracy; 10 = essential to democracy',
    'F114A': '1 = always justifiable; 10 = never justifiable (reversed original scale)',
    'F116': '1 = always justifiable; 10 = never justifiable (reversed original scale)',
}
LABELS.update({'state_market_role':'Preferred relationship between state and market',
               'ownership_policy':'Preferred ownership policy',
               'market_relations_natural':'Adaptation to the current life situation',
               'land_ownership_rights':'Preferred land ownership rights'})
for sector in ['small','large','land']:
    LABELS['renationalise_'+sector]=LABELS['renationalise_'+sector].replace('Opposition to renationalisation','Views on renationalisation')

from ess_analysis import LABELS as ESS_LABELS, POLARITY as ESS_POLARITY
LABELS.update(ESS_LABELS)
POLARITY.update(ESS_POLARITY)
from issp_analysis import LABELS as ISSP_LABELS, POLARITY as ISSP_POLARITY
LABELS.update(ISSP_LABELS)
POLARITY.update(ISSP_POLARITY)
SOURCES['ISSP']='ISSP / GESIS / Ukrainian survey teams'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_series():
    audit=pd.read_csv(TABLES/'question_trend_selection.csv')
    definitions=pd.read_csv(ROOT/'docs/question_trend_definitions.csv').set_index(['survey','item'])
    estimates=pd.read_csv(TABLES/'question_trend_estimates.csv')
    wording=load_audit()
    records=[]
    for (survey,item),z in estimates.groupby(['survey','item'],sort=False):
        meta=definitions.loc[(survey,item)]
        chosen=audit[audit.included & audit.survey.eq(survey) & audit.chart_item.eq(item)]
        question=meta.question_override if pd.notna(meta.question_override) else chosen.iloc[0].question
        numeric=meta.question_type=='numeric'
        groups=json.loads(meta.response_groups)
        order={label:i for i,label in enumerate(groups)}
        z=z.assign(_order=z.response.map(order)).sort_values(['_order','year']).drop(columns='_order').copy()
        years=sorted(z.year.astype(int).unique().tolist())
        assert len(years)>=2 and years[-1]>=CUTOFF
        chart_id=survey.lower()+'__'+item.lower()
        checked=wording[chart_id]
        assert checked['years']==years
        assert checked['original_groups']==groups
        question=checked['question']
        z['source_response']=z.response
        z['response']=z.response.map(checked['response_renames'])
        assert z.response.notna().all()
        monetary=survey=='ISSP' and item.startswith('earn_')
        scale_min=0 if survey in ['ESS','ISSP'] else 1
        metric='Weighted mean (monthly UAH, nominal)' if monetary else f'Weighted mean ({scale_min}–10)' if numeric else 'Response shares (%)'
        response=checked['polarity'] if numeric else 'All categories; adjacent positive and negative answers combined.' if meta.question_type=='ordinal' else 'All response options shown separately.'
        z['chart_id']=chart_id;z['question']=question;z['plotted_metric']=metric
        z.to_csv(OUT/f'{chart_id}.csv',index=False,encoding='utf-8-sig')
        records.append(dict(id=chart_id,survey=survey,item=item,question=question,label=checked['label'],wording=checked,
            response=response,metric=metric,mean=numeric,kind=meta.question_type,note=meta.method_note,scale_min=scale_min,monetary=monetary,
            ci=bool(z.ci_low.notna().all()),data=z,source_table='question_trend_estimates.csv',
            first_year=years[0],latest_year=years[-1],years=years))
    records.sort(key=lambda r:(SURVEYS.index(r['survey']),r['label']))
    audit.to_csv(OUT/'selection_audit.csv',index=False,encoding='utf-8-sig')
    return records,audit


def compact_header(fig, title, question, metadata, subtitle=None):
    """Stack header lines by their rendered height, including wrapped titles."""
    y = .965
    rows = [(title, 16, 'bold', INK)]
    if subtitle:
        rows.append((subtitle, 12, 'normal', '#52514e'))
    rows += [(question, 10.5, 'normal', '#52514e'),
             (metadata, 10.5, 'normal', '#52514e')]
    for text, size, weight, color in rows:
        artist = fig.text(.06, y, text, fontsize=size, weight=weight,
                          color=color, va='top', linespacing=1.2)
        fig.canvas.draw()
        bounds = artist.get_window_extent(fig.canvas.get_renderer())
        y -= bounds.height / fig.bbox.height + 7 / (72 * fig.get_figheight())
    return y


def draw(r):
    if not r['mean']:
        return draw_categories(r)
    z = r['data']
    fig, ax = plt.subplots(figsize=FIGSIZE)
    fig.subplots_adjust(left=.09, right=.96, top=.70, bottom=.22)
    fmt = (lambda v: f'{v:,.0f}') if r.get('monetary') else (lambda v: f'{v:.2f}') if r['mean'] else (lambda v: f'{v:.1f}%')
    first, last = z.iloc[0], z.iloc[-1]
    finding = f"{r['label']}: {fmt(first.estimate)} to {fmt(last.estimate)}"
    headline = '\n'.join(textwrap.wrap(finding, width=76))
    question = '\n'.join(textwrap.wrap('Question (summary): '+r['question'], width=116))
    header_bottom = compact_header(fig, headline, question,
        f"Ukraine · {r['survey']} · {r['metric']} · {int(first.year)}–{int(last.year)}")
    fig.subplots_adjust(top=header_bottom-.025)
    for side in ['left', 'right', 'top']:
        ax.spines[side].set_visible(False)
    ax.spines['bottom'].set_color('#e1e0d9')
    ax.spines['bottom'].set_bounds(first.year, last.year)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color='#e1e0d9', linewidth=.6)
    ax.tick_params(length=0, pad=8, labelsize=10)
    if r['ci']:
        ax.errorbar(z.year, z.estimate, yerr=[z.estimate-z.ci_low, z.ci_high-z.estimate],
                    fmt='o-', color=BLUE, mfc='white', ms=5, lw=1.6, capsize=3,
                    elinewidth=1.1, zorder=3)
    else:
        ax.plot(z.year, z.estimate, 'o-', color=BLUE, mfc='white', ms=4.5, lw=1.6)
    if r.get('monetary'):
        ax.set_ylim(0,max(z.ci_high.max(),z.estimate.max())*1.18)
        ax.set_ylabel('Mean monthly UAH (nominal)',fontsize=10)
        ax.ticklabel_format(axis='y',style='plain',useOffset=False)
    elif r['mean']:
        ax.set_ylim(r['scale_min'], 10)
        ax.set_yticks([0,2,4,6,8,10] if r['scale_min']==0 else [1,3,5,7,10])
        ax.set_ylabel(f"Mean ({r['scale_min']}–10)", fontsize=10)
    else:
        ax.set_ylim(0, 100)
        ax.set_yticks(range(0, 101, 20))
        ax.yaxis.set_major_formatter(PercentFormatter(100, decimals=0))
        ax.set_ylabel('Respondents (%)', fontsize=10)
    years = z.year.tolist()
    span = last.year-first.year
    ax.set_xlim(first.year-max(span*.035, .35), last.year+max(span*.06, .4))
    # Tick thinning is cosmetic; every observation remains drawn and exported.
    ticks = years if len(years) <= 10 else years[::3] + ([years[-1]] if years[-1] not in years[::3] else [])
    ax.set_xticks(ticks)
    if r['survey']=='ESS':ax.set_xticklabels(['2006–07' if y==2007 else str(y) for y in ticks])
    ax.set_xlabel('Survey year', fontsize=10, labelpad=9)
    picks = range(len(z)) if len(z) <= 5 else sorted({0, len(z)-1, int(z.estimate.to_numpy().argmin()), int(z.estimate.to_numpy().argmax())})
    used = []
    for i in picks:
        row = z.iloc[i]
        y = row.ci_high if r['ci'] else row.estimate
        offset = 10
        # Separate labels on neighbouring annual observations.
        if any(abs(row.year-x) < max(span*.09, .5) and abs(y-v) < (1 if r['mean'] else 10) for x,v in used):
            offset = 27
        if y > (ax.get_ylim()[1]*.9 if r.get('monetary') else 9 if r['mean'] else 92):
            y = row.ci_low if r['ci'] else row.estimate
            offset = -19
        ax.annotate(fmt(row.estimate), (row.year,y), xytext=(0,offset), textcoords='offset points',
                    ha='center', va='bottom', fontsize=10, color=INK)
        used.append((row.year,y))
    fig.text(.06, .135, '\n'.join(textwrap.wrap(r['response'], 128)), fontsize=9, color='#52514e')
    note = r['wording'].get('chart_note') or r['note']
    fig.text(.06, .08, note, fontsize=8, color='#898781')
    fig.text(.06, .04,
             f"Chart: Valentyn Hatsko, TG: @gorbach_squad. Source: {SOURCES[r['survey']]}, retrieved September 2026.",
             fontsize=8, weight='semibold')
    for ext in ['png', 'svg']:
        fig.savefig(OUT / f"{r['id']}.{ext}", dpi=300, facecolor='white',
                    metadata={'Date':None} if ext == 'svg' else None)
        if ext == 'svg':
            path=OUT / f"{r['id']}.svg"
            path.write_text(path.read_text(encoding='utf8').replace("font-family: 'DejaVu Sans'", "font-family: 'DejaVu Sans', Arial, sans-serif"),encoding='utf8')
    plt.close(fig)


def draw_categories(r):
    z=r['data'];responses=z.response.unique().tolist()
    colors=[BLUE,'#eb6834','#315778','#777777','#aaaaaa','#444444','#999999','#666666']
    markers=['o','s','^','D','v','P','X','*'];styles=['-','-','--',':','-.','--',':','-.']
    fig,ax=plt.subplots(figsize=FIGSIZE)
    fig.subplots_adjust(left=.09,right=.94,top=.62,bottom=.22)
    last=z[z.year.eq(r['latest_year'])]
    substantive=last[~last.response.str.contains("Don't know|Hard to say|No answer|no answer|missing",regex=True)]
    lead=substantive.loc[substantive.estimate.idxmax()]
    header_bottom = compact_header(fig,
        '\n'.join(textwrap.wrap(r['label'],76)),
        '\n'.join(textwrap.wrap('Question (summary): '+r['question'],116)),
        f"Ukraine · {r['survey']} · All response categories (%) · {r['first_year']}–{r['latest_year']}",
        subtitle='\n'.join(textwrap.wrap(f"{r['latest_year']}: {lead.response} — {lead.estimate:.1f}%",100)))
    for side in ['left','right','top']:ax.spines[side].set_visible(False)
    ax.spines['bottom'].set_color('#e1e0d9');ax.set_axisbelow(True)
    ax.yaxis.grid(True,color='#e1e0d9',lw=.6);ax.tick_params(length=0,pad=8,labelsize=10)
    endpoints=[]
    for i,response in enumerate(responses):
        v=z[z.response.eq(response)].sort_values('year')
        color=colors[i];lw=1.7
        if r['item']=='market_relations_natural' and i>0:color=['#777777','#999999','#bbbbbb','#555555'][i-1];lw=1.1
        isolated=r['wording'].get('isolated_years',[])
        if isolated:
            # Wording break: 1991 Pew asks about efforts to establish a market;
            # later years ask retrospectively about the transition.
            stand=v[v.year.isin(isolated)]
            ax.plot(stand.year,stand.estimate,marker=markers[i],ls='none',color=color,ms=4,mfc='white')
            v=v[~v.year.isin(isolated)]
        if r['ci']:
            ax.errorbar(v.year,v.estimate,yerr=[v.estimate-v.ci_low,v.ci_high-v.estimate],
                        color=color,marker=markers[i],ls=styles[i],ms=4,lw=lw,capsize=2,elinewidth=.7,
                        label='\n'.join(textwrap.wrap(response,32)),mfc='white')
        else:
            ax.plot(v.year,v.estimate,color=color,marker=markers[i],ls=styles[i],ms=4,lw=lw,
                    label='\n'.join(textwrap.wrap(response,32)),mfc='white')
        if v.iloc[-1].year==r['latest_year']:endpoints.append((float(v.iloc[-1].estimate),i))
    ax.set_ylim(0,100);ax.set_yticks(range(0,101,20));ax.yaxis.set_major_formatter(PercentFormatter(100,decimals=0))
    ax.set_ylabel('Respondents (%)',fontsize=10)
    years=r['years'];span=years[-1]-years[0]
    ax.set_xlim(years[0]-max(.03*span,.25),years[-1]+max(.13*span,.4))
    ticks=years if len(years)<=10 else sorted(set(years[::3]+[years[-1]]))
    ax.set_xticks(ticks);ax.set_xlabel('Survey year',fontsize=10,labelpad=9)
    if r['survey']=='ESS':ax.set_xticklabels(['2006–07' if y==2007 else str(y) for y in ticks])
    ax.spines['bottom'].set_bounds(years[0],years[-1])
    ends=sorted(endpoints);target=[v for v,i in ends]
    for i in range(1,len(target)):target[i]=max(target[i],target[i-1]+6)
    if target and target[-1]>96:
        target[-1]=96
        for i in range(len(target)-2,-1,-1):target[i]=min(target[i],target[i+1]-6)
    for (value,i),y in zip(ends,target):
        ax.annotate(f'{value:.1f}%',(years[-1],value),xytext=(years[-1]+max(span*.035,.12),y),
                    ha='left',va='center',fontsize=9,color=INK,
                    arrowprops=dict(arrowstyle='-',lw=.5,color='#999999'))
    handles,labels=ax.get_legend_handles_labels()
    legend = fig.legend(handles,labels,loc='upper left',bbox_to_anchor=(.055,header_bottom),ncol=2 if len(labels)>3 else len(labels),
               frameon=False,fontsize=9,handlelength=2,columnspacing=2,labelspacing=.7)
    fig.canvas.draw()
    legend_bottom = legend.get_window_extent(fig.canvas.get_renderer()).y0 / fig.bbox.height
    fig.subplots_adjust(top=legend_bottom-.025)
    interval='Approximate 95% confidence intervals.' if r['ci'] else 'Confidence intervals unavailable.'
    chart_note=r['wording'].get('chart_note','')
    fig.text(.06,.135,'\n'.join(textwrap.wrap(chart_note or 'Lines connect surveyed years; every response category is shown.',128)),fontsize=9,color='#52514e')
    fig.text(.06,.08,'All respondents. '+interval,fontsize=8,color='#898781')
    fig.text(.06,.04,f"Chart: Valentyn Hatsko, TG: @gorbach_squad. Source: {SOURCES[r['survey']]}, retrieved September 2026.",fontsize=8,weight='semibold')
    for ext in ['png','svg']:
        path=OUT/f"{r['id']}.{ext}"
        fig.savefig(path,dpi=300,facecolor='white',metadata={'Date':None} if ext=='svg' else None)
        if ext=='svg':path.write_text(path.read_text(encoding='utf8').replace("font-family: 'DejaVu Sans'","font-family: 'DejaVu Sans', Arial, sans-serif"),encoding='utf8')
    plt.close(fig)


def gallery(records):
    content = []
    for r in records:
        svg = (OUT / f"{r['id']}.svg").read_text(encoding='utf8')
        svg = svg[svg.index('<svg'):]
        entry = {k:v for k,v in r.items() if k != 'data'}
        entry['svg'] = svg
        entry['csv'] = (OUT / f"{r['id']}.csv").read_text(encoding='utf-8-sig')
        entry['points'] = json.loads(r['data'][['year','response','estimate','ci_low','ci_high']].to_json(orient='records'))
        content.append(entry)
    payload = json.dumps(content, ensure_ascii=False).replace('</', '<\\/')
    template = '''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Market and state attitudes in Ukraine</title>
<style>
*{box-sizing:border-box}body{margin:0;color:#151515;background:#fff;font:15px/1.5 system-ui,sans-serif}
header{padding:20px 28px;border-bottom:1px solid #ddd}h1{font-size:23px;margin:0 0 5px}p{margin:0;color:#555}
.layout{display:grid;grid-template-columns:320px minmax(0,1fr)}aside{padding:20px;border-right:1px solid #ddd;height:calc(100vh - 105px);overflow:auto;position:sticky;top:0}
label{display:block;font-size:13px;margin-bottom:5px}input,select{font:inherit;padding:8px;border:1px solid #aaa;border-radius:3px;width:100%;margin-bottom:12px}
button,a.download{font:inherit;cursor:pointer;border:1px solid #bbb;background:#fff;border-radius:3px;padding:6px 12px;color:#151515;text-decoration:none}
button:hover,a.download:hover{background:#f1f5f9}button:focus-visible,a:focus-visible{outline:2px solid #2a78d6;outline-offset:2px}
.choice{display:block;text-align:left;width:100%;border:0;border-bottom:1px solid #eee;border-radius:0;padding:10px 8px;font-size:13px}
.choice[aria-current=true]{background:#eaf2fc;border-left:3px solid #2a78d6}.meta{display:block;color:#626262;font-size:12px}
main{padding:20px 28px;min-width:0}.toolbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.position{margin-right:auto;font-size:13px;color:#555}
#chart svg{width:100%;height:auto;display:block}#chart{max-width:1100px;margin:0 auto}
details{max-width:1000px;margin:12px auto}summary{cursor:pointer}table{border-collapse:collapse;width:100%;margin-top:10px;font-size:13px}
th,td{padding:7px 12px;border-bottom:1px solid #ddd;text-align:right}th:first-child,td:first-child,th:nth-child(2),td:nth-child(2){text-align:left}td{overflow-wrap:anywhere}
.methods{font-size:13px;color:#555;padding-top:12px}.count{font-size:12px;color:#555;margin:0 0 8px}
.wording p{margin:8px 0}.wording li{margin:5px 0}.wording h3{font-size:14px;margin:16px 0 6px}.wording blockquote{margin:8px 0;padding-left:12px;border-left:2px solid #ddd;color:#333}.wording a{overflow-wrap:anywhere}
@media(max-width:800px){.layout{display:block}aside{position:static;height:auto;border-right:0;padding-bottom:8px}#list{max-height:190px;overflow:auto}main{padding:10px}header{padding:16px}h1{font-size:21px}}
</style>
<header><h1>Market and state attitudes in Ukraine</h1><p>A synthesis of attitudes toward markets and the state’s role in the economy, drawn from international and Ukrainian surveys.</p></header>
<div class="layout"><aside><label for="search">Find a question</label><input id="search" type="search" placeholder="Competition, taxes, land…">
<label for="survey">Survey</label><select id="survey"><option value="">All surveys</option><option>WVS</option><option>EVS</option><option>Pew</option><option>Monitoring</option><option>ESS</option><option>ISSP</option></select>
<label for="type">Display</label><select id="type"><option value="">All question types</option><option value="numeric">Numeric means</option><option value="ordinal">Grouped ordered categories</option><option value="nominal">All unordered options</option></select>
<div id="count" class="count" aria-live="polite"></div><nav id="list" aria-label="Questions"></nav></aside>
<main><div class="toolbar"><span id="position" class="position"></span><button id="prev" aria-label="Previous chart">Previous</button><button id="next" aria-label="Next chart">Next</button>
<button id="png">PNG</button><button id="svg">SVG</button><button id="csv">Data CSV</button></div>
<div id="chart" role="img"></div>
<details><summary>Question wording and response options</summary><div id="wording" class="methods wording"></div></details>
<details><summary>Values and measurement</summary><div id="definition" class="methods"></div><table><thead><tr><th>Year</th><th>Response</th><th>Estimate</th><th>95% lower</th><th>95% upper</th></tr></thead><tbody id="values"></tbody></table></details>
<details><summary>Sources and methodology</summary><div class="methods">
<p>__CHART_COUNT__ question-level trends. Each series has at least two observations and a latest observation in 2019 or later. Lines connect actual survey years.</p>
<p>Numeric questions show weighted means with 95% confidence intervals. Ordered responses combine positive and negative categories, retaining middle and missing responses. Nominal questions show all options. Numeric means use valid answers; categorical shares include nonresponse.</p>
<ul>
<li><strong>WVS:</strong> Adults aged 18+, national weights, aligned scale directions and approximate intervals. <a href="https://doi.org/10.14281/18241.25">Haerpfer et al. (2024), time series v5.0</a>.</li>
<li><strong>EVS:</strong> Weighted adult estimates and approximate intervals; shown separately from WVS for comparison. <a href="https://doi.org/10.4232/1.14021">EVS (2022), ZA7503 v3.0.0</a>.</li>
<li><strong>Pew:</strong> Published Ukrainian percentages, retaining rounding and nonresponse. Fieldwork years are used, including 2015 for the report published in 2017. <a href="https://github.com/velgaks/promarket-attitudes/blob/main/docs/SOURCES.md#pew-research-center">Reports and toplines</a>.</li>
<li><strong>Monitoring:</strong> Published national tables; differently worded questions remain separate. No intervals are inferred from percentages alone. <a href="https://isnasu.org.ua/publish/ukrainske-suspilstvo/issues.php">Institute of Sociology, NAS of Ukraine</a>.</li>
<li><strong>ESS:</strong> Weighted adult estimates; 2022/2024 intervals account for strata and sampling clusters, earlier intervals are approximate. The 2022 observation is a separate Ukrainian ESS-related study. The 2006–07 fieldwork point is plotted at 2007. <a href="https://github.com/velgaks/promarket-attitudes/blob/main/docs/SOURCES.md#european-social-survey-ess">Dataset editions and citations</a>.</li>
<li><strong>ISSP:</strong> Weighted adult estimates for 2009 and 2019, with approximate intervals. Monetary amounts are monthly after-tax UAH at current prices. <a href="https://doi.org/10.4232/1.12777">ISSP 2009</a>; <a href="https://doi.org/10.4232/1.13853">Oksamytna and Ivashchenko, Ukraine 2019</a>.</li>
<li><strong>LiTS:</strong> Included in the project’s aggregate tables; its 2016 endpoint falls outside this gallery’s selection. <a href="https://www.ebrd.com/home/what-we-do/office-of-the-chief-economist/lits/life-in-transition-survey-data.html">EBRD and World Bank, rounds I–III</a>.</li>
</ul>
<p>Territorial coverage and survey methods change across waves. <a href="https://github.com/velgaks/promarket-attitudes/blob/main/docs/SOURCES.md#comparability">Comparability details</a>.</p>
</div></details>
<p class="count"><a href="https://github.com/velgaks/promarket-attitudes/blob/main/docs/SOURCES.md">Full source citations</a> · <a href="https://github.com/velgaks/promarket-attitudes">About the project</a></p>
</main></div>
<script>const DATA=__DATA__;
let shown=DATA.slice(),current=DATA[0];
const $=id=>document.getElementById(id);
function download(text,name,type){const url=URL.createObjectURL(new Blob([text],{type}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}
function wording(r){const root=$('wording');root.replaceChildren();const w=r.wording;
const add=(tag,text,parent=root)=>{const e=document.createElement(tag);e.textContent=text;parent.append(e);return e};
add('p',w.wording_type+'. Chart questions are summaries, not verbatim quotations.');
add('h3','Source question');add('blockquote',w.source_question);
add('h3','Full response alternatives / scale');const options=add('ul','');for(const [code,label] of Object.entries(w.source_options))add('li',code+': '+label,options);
add('h3',r.mean?'Plotted scale':'How responses are grouped in this chart');
if(r.mean)add('p',r.response);else{const groups=add('ul','');for(const [label,codes] of Object.entries(w.display_groups))add('li',label+' ← source codes: '+codes.join(', '),groups)}
add('h3','Wording across waves');const notes=add('ul','');for(const note of w.wording_notes)add('li',note,notes);
add('h3','Checked sources');for(const ref of w.references){const d=add('details','');add('summary',ref.years.join(', ')+' · '+ref.file.split('/').pop()+(ref.pdf_pages.length?' · PDF p. '+ref.pdf_pages.join(', '):''),d);add('p',ref.verification,d);const link=add('a','Open source',d);link.href=ref.url+(ref.url.toLowerCase().endsWith('.pdf')&&ref.pdf_pages.length?'#page='+ref.pdf_pages[0]:'');link.target='_blank';link.rel='noopener';if(ref.excerpt)add('blockquote',ref.excerpt,d)}
const p=add('p','');const a=add('a','Download the complete wording audit (all charts)',p);a.href='https://github.com/velgaks/promarket-attitudes/blob/main/docs/chart_wording_audit.csv';}
function select(r){current=r;$('chart').innerHTML=r.svg;$('chart').setAttribute('aria-label',r.survey+': '+r.question+' '+r.years.join(', '));
wording(r);
$('position').textContent=(shown.indexOf(r)+1)+' / '+shown.length+' · '+r.survey+' · '+r.first_year+'–'+r.latest_year;
$('definition').textContent=r.metric+'. '+r.response+' '+r.note+' Source table: '+r.source_table;
$('values').replaceChildren();for(const point of r.points){const tr=document.createElement('tr');for(const key of ['year','response','estimate','ci_low','ci_high']){const td=document.createElement('td');td.textContent=point[key]===null?'Unavailable':(key==='year'||key==='response')?point[key]:point[key].toFixed(r.mean?2:1);tr.append(td)}$('values').append(tr)}
document.querySelectorAll('.choice').forEach(b=>b.setAttribute('aria-current',String(b.dataset.id===r.id)))}
function filter(){const q=$('search').value.toLowerCase(),s=$('survey').value,t=$('type').value;shown=DATA.filter(r=>(!s||r.survey===s)&&(!t||r.kind===t)&&(r.question+' '+r.label+' '+r.item+' '+r.survey).toLowerCase().includes(q));$('count').textContent=shown.length+' matching charts';$('list').replaceChildren();
for(const r of shown){const b=document.createElement('button');b.className='choice';b.dataset.id=r.id;const label=document.createElement('span');label.textContent=r.label;const meta=document.createElement('span');meta.className='meta';meta.textContent=r.survey+' · '+r.first_year+'–'+r.latest_year+' · '+r.years.length+' observations';b.append(label,meta);b.onclick=()=>select(r);$('list').append(b)}
if(shown.length)select(shown.includes(current)?current:shown[0]);else{$('position').textContent='No matching questions';$('chart').innerHTML='';$('values').replaceChildren();$('wording').replaceChildren();$('definition').textContent=''}
for(const id of ['prev','next','png','svg','csv'])$(id).disabled=!shown.length}
$('search').oninput=filter;$('survey').onchange=filter;$('type').onchange=filter;
$('prev').onclick=()=>select(shown[(shown.indexOf(current)-1+shown.length)%shown.length]);$('next').onclick=()=>select(shown[(shown.indexOf(current)+1)%shown.length]);
$('svg').onclick=()=>download(current.svg,current.id+'.svg','image/svg+xml');$('csv').onclick=()=>download('\ufeff'+current.csv,current.id+'.csv','text/csv;charset=utf-8');
$('png').onclick=async()=>{const selected=current,button=$('png');button.disabled=true;
const url=URL.createObjectURL(new Blob([selected.svg],{type:'image/svg+xml'}));
try{const image=new Image();await new Promise((resolve,reject)=>{image.onload=resolve;image.onerror=reject;image.src=url});
const canvas=document.createElement('canvas');canvas.width=3300;canvas.height=2220;const ctx=canvas.getContext('2d');ctx.fillStyle='#fff';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.drawImage(image,0,0,canvas.width,canvas.height);
const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/png'));download(blob,selected.id+'.png','image/png');
}finally{URL.revokeObjectURL(url);button.disabled=false}};filter();
</script></html>'''
    (OUT/'index.html').write_text(template.replace('__DATA__',payload).replace('__CHART_COUNT__',str(len(records))),encoding='utf8')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    previous=json.loads((OUT/'manifest.json').read_text()).get('chart_ids',[]) if (OUT/'manifest.json').exists() else []
    records, audit = load_series()
    for r in records:
        draw(r)
    gallery(records)
    # Archive only named obsolete chart exports, never unrelated user files.
    obsolete=set(previous)-{r['id'] for r in records}
    if obsolete:
        archive=ROOT/'tmp/question_trend_superseded';archive.mkdir(parents=True,exist_ok=True)
        for name in obsolete:
            for ext in ['png','svg','csv']:
                path=OUT/f'{name}.{ext}'
                assert path.resolve().parent==OUT.resolve()
                if path.exists():path.replace(archive/path.name)
    data = pd.concat([r['data'] for r in records], ignore_index=True)
    data.to_csv(OUT/'all_chart_data.csv',index=False,encoding='utf-8-sig')
    inventory = pd.DataFrame([{k:v for k,v in r.items() if k not in ['data','mean','ci','wording']}
                              for r in records])
    inventory['years'] = inventory.years.map(lambda y:', '.join(map(str,y)))
    inventory.to_csv(OUT/'chart_inventory.csv',index=False,encoding='utf-8-sig')
    assert set(zip(inventory.survey,inventory.item)) == set(zip(audit[audit.included].survey,audit[audit.included].chart_item))
    # Reconcile every plotted value and interval to its original generated table.
    for r in records:
        original=pd.read_csv(TABLES/r['source_table'])
        original=original[original.survey.eq(r['survey']) & original.item.eq(r['item'])]
        if 'age_group' in original:
            original=original[original.age_group.eq('All')|original.age_group.isna()]
        original=original.assign(_order=original.response.map({v:i for i,v in enumerate(r['data'].source_response.unique())})).sort_values(['_order','year'])
        assert np.allclose(original[['estimate','ci_low','ci_high']],r['data'][['estimate','ci_low','ci_high']],equal_nan=True)
    notes = f'''# Market and state attitudes in Ukraine

{len(records)} separate chart sets (PNG, editable SVG and data CSV), drawn from audited national estimates.
Open index.html for the searchable, offline gallery. Download PNG files alongside the HTML.

## Selection

- At least two distinct observed fieldwork years within a survey/question series.
- Latest available observation is **2019 or later**, inclusive.
- All observed years of an eligible series are retained, including those before 2019.
- One chart per complete question **within each survey**. WVS and EVS remain separate; the three state-role options and four ownership-policy options are now grouped into their two original questions.
- The selection audit covers all {len(audit)} previously audited indicators. LiTS is excluded because its latest Ukrainian observation is 2016. Composite indices are not individual questions.

## Measurement

All eligible numeric rating scales show weighted means with 95% intervals. WVS/EVS scales run 1–10; ESS scales run 0–10. ESS intervals use strata and PSUs in 2022/2024; earlier ESS intervals are approximate because design identifiers are absent in the supplied file. This includes democracy-characteristic and tax/benefit-justifiability questions previously shown as threshold shares. The latter are reversed so high scores mean stronger rejection of cheating; democracy means use only 1–10 ratings, excluding the spontaneous nonnumeric “against democracy” response (code 0), whose frequency is exported. Verbal ordinal scales combine positive and negative categories; neutral/undecided and nonresponse remain separate. Nominal questions show every option. All categorical charts use all respondents, unlike the previous valid-answer-only microdata shares. Published rounding is retained, so totals can differ slightly from 100%. An option not offered in earlier years is absent, never imputed as zero. No eligible multiple-answer question survives both selection criteria: crisis-policy choices end in 2017; business duties have only 2019. Such options are therefore not added as one-point charts.

ISSP adds weighted ordinal/nominal distributions and numeric monetary means for 2009 and 2019. Monetary amounts are monthly UAH after tax at current prices, without inflation adjustment. The Ukrainian tax wording says higher taxes rather than explicitly higher tax rates. The 2019 sample excludes occupied territories and has documented sampling deviations.

## Comparability and sources

The files reuse the verified coding and historical source coverage of the research note. Territorial exclusions, displacement and survey methods vary across waves; the note's Limitations section and project documentation describe these issues. Published Monitoring margins cannot be reweighted geographically. Related but differently worded privatisation, existing ownership and renationalisation questions remain separate. Named alternatives from one categorical question share one chart. Distinct battery subquestions remain separate.

Every plotted row is in all_chart_data.csv with source-table keys and available original metadata. The source_tables/ and docs/ folders in the ZIP retain definitions, provenance, source cells and question comparability documentation. Raw microdata are not redistributed. selection_audit.csv documents every included/excluded indicator; chart_inventory.csv indexes the export files.

## Question wording

Chart questions are explicitly marked as summaries. The HTML's “Question wording and response options” panel provides source wording, full response alternatives, grouping/code mappings, source pages, and wave differences for all 95 charts. `source_response` retains the stable category key in the original estimate table; `response` is the corrected display label. `docs/chart_wording_audit.csv` is the display registry. Ukrainian national forms were checked for EVS 1999/2008/2020, ISSP 2009/2019 and ESS 2022; the Ukrainian WVS 2020 report and original Monitoring tables were also checked. Other WVS/ESS waves and Pew use their master/codebook/topline wording; complete national-language verification is not claimed. Pew's prospective 1991 transition question is drawn as an isolated point. The EVS 2020 competition question omits the explanatory phrases used in earlier waves; local EVS and WVS income endpoints retain explicit references to income rewards for work or effort.

## Rebuild

From the project root, after the existing data pipeline: `python scripts/question_trend_data.py` then `python scripts/question_trends.py`. To re-extract the wording audit from locally acquired documentation, run `python scripts/chart_wording.py` before rendering.
The full `scripts/run.py` also runs this stage. Source estimate files are hashed in manifest.json. Existing figures and the research note are not modified by chart generation.
'''
    (OUT/'README.md').write_text(notes,encoding='utf8')
    source_names=sorted(set(r['source_table'] for r in records)|{'latest_positive_shares.csv','question_year_inventory.csv','question_trend_source_cells.csv','question_trend_selection.csv'})
    manifest=dict(latest_year_cutoff=CUTOFF,min_observed_years=2,chart_count=len(records),
                  counts_by_survey=inventory.groupby('survey').size().to_dict(),
                  mean_charts=sum(r['mean'] for r in records),share_charts=sum(not r['mean'] for r in records),
                  question_types=inventory.kind.value_counts().to_dict(),
                  chart_ids=[r['id'] for r in records],
                  checks='Passed: complete selection coverage; every point and interval matches its source; valid ranges; distinct years.',
                  source_tables={n:digest(TABLES/n) for n in source_names})
    manifest['wording_audit_sha256']=digest(ROOT/'docs/chart_wording_audit.csv')
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    print(json.dumps(manifest,indent=2))
    package_exports(records)


def package_exports(records):
    source_names=list(json.loads((OUT/'manifest.json').read_text())['source_tables'])
    target=ROOT/'output/question_trends.zip'
    with ZipFile(target,'w',ZIP_DEFLATED) as archive:
        expected=[OUT/name for name in ['index.html','README.md','manifest.json','all_chart_data.csv','selection_audit.csv','chart_inventory.csv']]
        expected += [OUT/f"{r['id']}.{ext}" for r in records for ext in ['png','svg','csv']]
        for path in expected:
            archive.write(path,path.relative_to(OUT))
        for name in source_names + ['monitoring_analysis_trace.csv','monitoring_published_results.csv','extended_published_trace.csv','question_trend_validation.json','ess_validation.json','ess_sample_audit.csv','ess_estimates.csv','ess_sensitivity.csv','ess_variable_inventory.csv','issp_validation.json','issp_estimates.csv','issp_sample_audit.csv','issp_variable_inventory.csv','issp_sensitivity.csv','issp_monetary_audit.csv','issp_published_checks.csv','issp_correlations.csv','issp_joint_agreement.csv']:
            archive.write(TABLES/name,'source_tables/'+name)
        for name in ['SOURCES.md','REPRODUCIBILITY.md','question_crosswalk.csv','extended_question_definitions.csv','monitoring_indicator_definitions.csv','question_trend_definitions.csv','chart_wording_audit.csv','ess_question_crosswalk.csv','ess_variable_catalogue.csv','issp_question_crosswalk.csv','issp_variable_catalogue.csv']:
            archive.write(ROOT/'docs'/name,'docs/'+name)
        for name in ['issp_analysis.py','issp_documentation.py','acquire_issp_sources.py','ess_analysis.py','question_trends.py','question_trend_data.py','chart_wording.py','extended_attitudes.py','extended_published.py','monitoring_extract.py','acquire.py','figures.py','question_inventory.py','analyze.py']:
            archive.write(ROOT/'scripts'/name,'scripts/'+name)
    print(target)


if __name__=='__main__':
    main()
