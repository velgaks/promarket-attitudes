"""Mean/share plots with approximate 95% CIs; no stacked distribution charts.

Horizontal display offsets separate groups within the same actual fieldwork year.
No annual interpolation or smoothing is used.
"""
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from matplotlib.transforms import ScaledTranslation
import pandas as pd
import numpy as np
from analyze import ROOT, AGES, INDEX

OUT=ROOT/'output/figures'
BLUE='#2a78d6'; ORANGE='#eb6834'; GREY='#697681'; INK='#0b0b0b'
LABELS={'private_ownership':'Private ownership','competition':'Benefits of competition',
        'individual_responsibility':'Individual responsibility','income_incentives':'Income incentives'}
EXPORTS=[]
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'text.color':INK,
                     'axes.labelcolor':'#52514e','xtick.color':'#52514e','ytick.color':'#52514e',
                     'svg.fonttype':'none','pdf.fonttype':42})

def layout(title,subtitle,note,shape=(1,1),height=5.7,source='EBRD LiTS'):
    fig,axes=plt.subplots(*shape,figsize=(10,height),squeeze=False)
    fig.subplots_adjust(left=.08,right=.97,top=.75,bottom=.23,hspace=.46,wspace=.23)
    fig.text(.06,.96,title,fontsize=16,weight='bold',va='top')
    fig.text(.06,.90,subtitle,fontsize=10.5,color='#52514e',va='top')
    fig.text(.06,.12,note,fontsize=8,color='#898781')
    fig.text(.06,.08,f'Chart: Valentyn Hatsko, TG: @gorbach_squad. Source: {source}, retrieved September 2026.',fontsize=8,weight='semibold')
    fig.text(.06,.04,'Data, code and method: promarket-attitudes / scripts / README.md',fontsize=8,color='#898781')
    for ax in axes.flat:
        for side in ['left','right','top']:ax.spines[side].set_visible(False)
        ax.spines['bottom'].set_color('#e1e0d9');ax.tick_params(length=0,pad=7,labelsize=9)
        ax.set_axisbelow(True);ax.yaxis.grid(True,color='#e1e0d9',lw=.6)
    return fig,axes

def errors(ax,z,color,marker,label,offset=0,multiplier=1):
    z=z.sort_values('year')
    transform=ax.transData+ScaledTranslation(offset/72,0,ax.figure.dpi_scale_trans)
    return ax.errorbar(z.year,z.estimate*multiplier,
        yerr=[(z.estimate-z.ci_low)*multiplier,(z.ci_high-z.estimate)*multiplier],
        fmt=marker,linestyle='-',linewidth=1.2,color=color,mfc='white',mec=color,ms=5,
        elinewidth=1.2,capsize=3,capthick=1.1,label=label,transform=transform,zorder=3)

def axis_years(ax,years,bounds=(1,10),ticks=None,rotate=False):
    ax.set_ylim(*bounds);ax.set_yticks(ticks or [1,4,7,10])
    ax.set_xticks(years);ax.set_xlim(min(years)-2,max(years)+2)
    if rotate:ax.tick_params(axis='x',labelrotation=45)

def legend(fig,handles,labels):
    fig.legend(handles,labels,loc='upper left',bbox_to_anchor=(.055,.855),ncol=len(labels),frameon=False,fontsize=10)

def save(fig,name):
    for ext in ['png','svg']:
        fig.savefig(OUT/f'{name}.{ext}',dpi=300,facecolor='white',metadata={'Date':None} if ext=='svg' else None)
    EXPORTS.append(name);plt.close(fig)

def values_figures(e):
    main=e[e.survey.isin(['WVS','EVS'])&e.weighted&e.territory.eq('survey_coverage')]
    fig,axes=layout('Economic attitudes do not move as a single package',
        'Ukraine · weighted means, 1–10 · bars show approximate 95% confidence intervals',
        'Higher values favour markets; survey marks separated within years for readability.',(2,2),7.2,'WVS / EVS')
    handles=[]
    for ax,(item,label) in zip(axes.flat,LABELS.items()):
        for survey,color,marker,offset in [('WVS',BLUE,'o',-4),('EVS',ORANGE,'s',4)]:
            z=main[main.item.eq(item)&main.survey.eq(survey)&main.age_group.eq('All')]
            handle=errors(ax,z,color,marker,survey,offset)
            if item=='private_ownership':handles.append(handle)
        ax.set_title(label,loc='left',fontsize=12,weight='bold')
        axis_years(ax,sorted(main.year.unique()),rotate=True)
    legend(fig,handles,['WVS','EVS']);save(fig,'national_dimension_trends')
    for survey in ['WVS','EVS']:
        fig,axes=layout(f'{survey}: age gaps depend on the attitude measured',
            'Ukraine · weighted means, 1–10 · bars show approximate 95% confidence intervals',
            'Valid answers, adults 18+; age-group marks separated within each fieldwork year.',(2,2),7.2,survey)
        handles=[];years=sorted(main.loc[main.survey.eq(survey),'year'].unique())
        for ax,(item,label) in zip(axes.flat,LABELS.items()):
            for group,color,marker,offset in zip(AGES,[BLUE,ORANGE,GREY],['o','s','^'],[-6,0,6]):
                z=main[main.item.eq(item)&main.survey.eq(survey)&main.age_group.eq(group)]
                handle=errors(ax,z,color,marker,group,offset)
                if item=='private_ownership':handles.append(handle)
            ax.set_title(label,loc='left',fontsize=12,weight='bold');axis_years(ax,years)
        legend(fig,handles,AGES);save(fig,f'{survey.lower()}_age_dimension_trends')

def index_figures(e):
    main=e[e.item.eq(INDEX)&e.weighted&e.territory.eq('survey_coverage')]
    for by_age in [False,True]:
        title='Index age gaps narrow in some surveys' if by_age else 'Summary scores show no steady rise towards markets'
        fig,axes=layout(title,'Ukraine · 0–100 scores · bars show approximate 95% confidence intervals',
            'WVS/EVS: average of four attitudes, all four answered. LiTS: percentage preferring a market economy.',
            (1,3),5.8,'WVS / EVS / EBRD LiTS')
        handles=[]
        for ax,survey in zip(axes.flat,['WVS','EVS','LiTS']):
            z=main[main.survey.eq(survey)]
            if by_age:
                for group,color,marker,offset in zip(AGES,[BLUE,ORANGE,GREY],['o','s','^'],[-6,0,6]):
                    handle=errors(ax,z[z.age_group.eq(group)],color,marker,group,offset)
                    if survey=='WVS':handles.append(handle)
            else:
                z=z[z.age_group.eq('All')];errors(ax,z,BLUE,'o',survey)
                for r in z.itertuples():
                    ax.annotate(f'{r.estimate:.1f}',(r.year,r.ci_high),xytext=(0,7),textcoords='offset points',ha='center',fontsize=9)
            ax.set_title(survey+(' · direct preference' if survey=='LiTS' else ' · four-item index'),loc='left',fontsize=11,weight='bold')
            axis_years(ax,sorted(z.year.unique()),bounds=(0,100),ticks=[0,25,50,75,100],rotate=True)
        if by_age:legend(fig,handles,AGES)
        save(fig,'index_age_trends' if by_age else 'national_index_trends')

def lits_figures(e,d):
    base=e[e.survey.eq('LiTS')&e.item.eq('market')&e.weighted&e.territory.eq('survey_coverage')]
    fig,axes=layout('Market preference fell, then levelled off',
        'Ukraine · response shares (%) · bars show approximate 95% confidence intervals',
        'Substantive responses only; category marks separated within years for readability.')
    ax=axes[0,0];handles=[];names=[]
    d=d[d.survey.eq('LiTS')&d.item.eq('market')&d.age_group.eq('All')&d.territory.eq('survey_coverage')&d.denominator.eq('valid')]
    for response,label,color,marker,offset in [(1,'Market preferable',BLUE,'o',-7),(2,'Planned sometimes preferable',ORANGE,'s',0),(3,'Indifferent',GREY,'^',7)]:
        handles.append(errors(ax,d[d.response.eq(response)],color,marker,label,offset,100));names.append(label)
    axis_years(ax,[2006,2010,2016],(0,60),list(range(0,61,10)))
    ax.yaxis.set_major_formatter(PercentFormatter(100,decimals=0));legend(fig,handles,names)
    save(fig,'lits_response_shares')
    fig,axes=layout('Young adults’ market preference was lower than in 2006',
        'Ukraine · market preference by current age (%) · approximate 95% confidence intervals',
        'Valid responses; age-group marks separated within years for readability.')
    ax=axes[0,0];handles=[]
    for group,color,marker,offset in zip(AGES,[BLUE,ORANGE,GREY],['o','s','^'],[-7,0,7]):
        handles.append(errors(ax,base[base.age_group.eq(group)],color,marker,group,offset,100))
    axis_years(ax,[2006,2010,2016],(0,80),[0,20,40,60,80])
    ax.yaxis.set_major_formatter(PercentFormatter(100,decimals=0));legend(fig,handles,AGES)
    save(fig,'lits_age_groups')
    fig,axes=layout('Geographic restriction leaves similar estimates after 2010',
        'Ukraine · market preference (%) · bars show approximate 95% confidence intervals',
        'Restricted domain excludes Crimea/Sevastopol and all of Donetsk and Luhansk.')
    ax=axes[0,0];handles=[];names=[]
    z=e[e.survey.eq('LiTS')&e.item.eq('market')&e.weighted&e.age_group.eq('All')&e.year.ge(2010)]
    for terr,label,color,marker,offset in [('survey_coverage','Survey coverage',BLUE,'o',-5),('exclude_crimea_donetsk_luhansk','Restricted geography',ORANGE,'s',5)]:
        handles.append(errors(ax,z[z.territory.eq(terr)],color,marker,label,offset,100));names.append(label)
    axis_years(ax,[2010,2016],(0,60),list(range(0,61,10)))
    ax.yaxis.set_major_formatter(PercentFormatter(100,decimals=0));legend(fig,handles,names)
    save(fig,'lits_territory_sensitivity')

def monitoring_figures():
    e=pd.read_csv(ROOT/'output/tables/monitoring_estimates.csv')
    source='Institute of Sociology NAS Ukraine'

    def dots(ax,item,label,color=BLUE,marker='o',end=2020):
        z=e[e.item.eq(item)&e.year.le(end)].sort_values('year')
        ax.plot(z.year,z.estimate,linestyle='-',linewidth=1.2,marker=marker,color=color,
                mfc='white',ms=4.5,label=label)
        ax.yaxis.set_major_formatter(PercentFormatter(100,decimals=0))
        return z

    fig,axes=layout('Private business gained support; privatisation lost it',
        'Ukraine · expressed approval (% of all respondents) · published Monitoring tables',
        'Observed survey years only; published tables do not provide confidence intervals.',
        (1,2),5.8,source)
    ax=axes[0,0]
    z=dots(ax,'private_business','Private business')
    ax.set_title('Developing private business',loc='left',fontsize=12,weight='bold')
    for r in z[z.year.isin([1992,2014])].itertuples():
        ax.annotate(f'{r.estimate:.1f}%',(r.year,r.estimate),xytext=(0,9),textcoords='offset points',ha='center',fontsize=9)
    ax=axes[0,1]
    for sector,label,color,marker in [('small','Small enterprises',BLUE,'o'),('large','Large enterprises',ORANGE,'s'),('land','Land',GREY,'^')]:
        dots(ax,'privatise_'+sector,label,color,marker)
    ax.set_title('Privatisation',loc='left',fontsize=12,weight='bold')
    fig.legend(*ax.get_legend_handles_labels(),loc='upper left',bbox_to_anchor=(.50,.855),
               ncol=3,frameon=False,fontsize=8.4,columnspacing=.8,handletextpad=.4)
    for ax in axes.flat:
        axis_years(ax,[1992,1996,2000,2006,2010,2014,2018],(0,80),[0,20,40,60,80],True)
    save(fig,'monitoring_business_privatisation')

    fig,axes=layout('A mixed economy attracted more support than either pole',
        'Ukraine · preferred role of the state (%) · published Monitoring tables',
        'All respondents; undecided responses retained in denominator. Confidence intervals unavailable.',
        height=5.7,source=source)
    ax=axes[0,0]
    for response,label,color,marker in [('mixed_state_market','Mixed state and market',BLUE,'o'),
            ('planned_economy','Planned economy',ORANGE,'s'),('minimal_state_market','Minimal state involvement',GREY,'^')]:
        dots(ax,'state_role_'+response,label,color,marker)
    axis_years(ax,[2002,2004,2006,2008,2010,2012,2014,2016,2019,2020],(0,60),[0,20,40,60],True)
    legend(fig,*ax.get_legend_handles_labels());save(fig,'monitoring_state_role')

    fig,axes=layout('The privatisation support index fell sharply after 1992',
        'Ukraine · average approval of privatising small enterprises, large enterprises and land · 0–100',
        'Equal average of three affirmative shares; all respondents. Confidence intervals unavailable.',
        height=5.7,source=source)
    ax=axes[0,0];z=dots(ax,'privatisation_support_index','Three-sector index')
    axis_years(ax,[1992,1996,2000,2006,2010,2014,2018],(0,100),[0,25,50,75,100])
    ax.yaxis.set_major_formatter(matplotlib.ticker.ScalarFormatter())
    for r in z[z.year.isin([1992,2006,2018])].itertuples():
        ax.annotate(f'{r.estimate:.1f}',(r.year,r.estimate),xytext=(0,9),textcoords='offset points',ha='center',fontsize=9)
    save(fig,'monitoring_privatisation_index')

    fig,axes=layout('Attitudes depend on the sector and the ownership question',
        'Ukraine · pro-private responses (%) · three distinct questions, asked in 2013, 2017 and 2020',
        'All respondents; anti-renationalisation means answering no or rather no. Confidence intervals unavailable.',
        (1,3),5.8,source)
    for ax,(prefix,title) in zip(axes.flat,[('retrospective','Past privatisation worthwhile'),
            ('existing_private','Approve existing ownership'),('renationalise','Oppose renationalisation')]):
        for sector,label,color,marker in [('small','Small enterprises',BLUE,'o'),('large','Large enterprises',ORANGE,'s'),('land','Land',GREY,'^')]:
            dots(ax,prefix+'_'+sector,label,color,marker)
        ax.set_title(title,loc='left',fontsize=10.5,weight='bold')
        axis_years(ax,[2013,2017,2020],(0,80),[0,20,40,60,80])
    legend(fig,*axes[0,0].get_legend_handles_labels());save(fig,'monitoring_ownership_module')

    fig,axes=layout('Selective privatisation led the wartime policy choices',
        'Ukraine · ownership policy preferences (%) · separate 2023–2025 question',
        'All respondents; wording and survey mode vary. Confidence intervals unavailable.',
        height=5.7,source=source)
    ax=axes[0,0]
    for response,label,color,marker in [('privatise_except_efficient_state_firms','Privatise except efficient state firms',BLUE,'o'),
            ('nationalise','Nationalise private enterprises',ORANGE,'s'),('broad_privatisation','Broad privatisation',GREY,'^')]:
        dots(ax,'ownership_policy_'+response,label,color,marker,end=2025)
    axis_years(ax,[2023,2024,2025],(0,60),[0,20,40,60])
    fig.legend(*ax.get_legend_handles_labels(),loc='upper left',bbox_to_anchor=(.055,.855),ncol=1,frameon=False,fontsize=9)
    fig.subplots_adjust(top=.66)
    save(fig,'monitoring_later_policy')


def additional_figures():
    means=pd.read_csv(ROOT/'output/tables/extended_mean_estimates.csv')
    fig,axes=layout('LiTS: competition and ownership differ from income incentives',
        'Ukraine · weighted means, 1–10 · bars show approximate 95% confidence intervals',
        'Higher values favour the market endpoint. Lines connect observed waves only.',(1,3),5.5,'EBRD LiTS II / III')
    for ax,item in zip(axes.flat,['private_ownership','competition','income_incentives']):
        z=means[means.survey.eq('LiTS')&means.item.eq(item)&means.age_group.eq('All')]
        errors(ax,z,BLUE,'o',item);axis_years(ax,sorted(z.year.unique()))
        ax.set_title(LABELS[item],loc='left',fontsize=11,weight='bold')
    save(fig,'lits_additional_dimensions')
    pub=pd.read_csv(ROOT/'output/tables/extended_published_shares.csv')
    old=pd.read_csv(ROOT/'output/tables/pew_published_results.csv')
    fig,axes=layout('Pew: attitudes depend on which market question is asked',
        'Ukraine · affirmative responses, % of all respondents',
        '1991 transition question is prospective; later waves retrospective. CEE 2015 excludes Crimea, Donetsk and Luhansk.\nPublished percentages; item-specific confidence intervals unavailable.',(1,2),5.7,'Pew Global Attitudes / CEE')
    for ax,z,title in [(axes[0,0],old[old.age_group.eq('All')],'Approve market transition'),
        (axes[0,1],pub[pub.survey.eq('Pew')&pub.item.eq('free_market_better')],'Most people better off with markets')]:
        z=z.sort_values('year');ax.plot(z.year,z.estimate,'o-',color=BLUE,mfc='white',lw=1.2)
        ax.set_title(title,loc='left',fontsize=11,weight='bold');axis_years(ax,list(z.year),bounds=(0,100),ticks=[0,25,50,75,100],rotate=True)
        if 'source_file' in z and (z.year==2015).any():
            end=z[z.year.eq(2015)];ax.plot(end.year,end.estimate,'s',color=ORANGE,mfc='white',label='CEE 2015');ax.legend(frameon=False,fontsize=8)
    save(fig,'pew_market_trends')

def coherence_figures():
    rankings=pd.read_csv(ROOT/'output/tables/market_principle_rankings.csv')
    correlations=pd.read_csv(ROOT/'output/tables/attitude_correlations.csv')
    summary=pd.read_csv(ROOT/'output/tables/ideological_coherence.csv')
    fig,axes=layout('Competition attracts broad support in every survey',
        'Ukraine · latest microdata waves · market-oriented answers, % of valid responses',
        'Five market-oriented categories of each ten-point scale; bars show approximate 95% intervals.',
        (3,1),7.2,'WVS / EVS / EBRD LiTS')
    fig.subplots_adjust(left=.28,right=.91,top=.80,bottom=.22,hspace=.65)
    for ax,(survey,year) in zip(axes.flat,[('WVS',2020),('EVS',2020),('LiTS',2016)]):
        z=rankings[rankings.survey.eq(survey)].sort_values('rank')
        y=np.arange(len(z))
        ax.barh(y,z.estimate,color=BLUE,height=.50)
        ax.errorbar(z.estimate,y,xerr=[z.estimate-z.ci_low,z.ci_high-z.estimate],
                    fmt='none',ecolor=INK,elinewidth=.8,capsize=2)
        ax.set_yticks(y,[LABELS[item] for item in z.item],fontsize=10)
        ax.set_xlim(0,100);ax.set_ylim(len(z)-.5,-.7)
        ax.set_xticks([0,25,50,75,100]);ax.xaxis.set_major_formatter(PercentFormatter(100,decimals=0))
        ax.yaxis.grid(False);ax.xaxis.grid(True,color='#e1e0d9',lw=.6)
        ax.set_title(f'{survey} {year}',loc='left',fontsize=11,weight='bold',pad=8)
        for row,pos in zip(z.itertuples(),y):
            ax.text(max(row.estimate,row.ci_high)+1.5,pos,f'{row.estimate:.1f}%',va='center',fontsize=9)
    save(fig,'market_principle_ranking')

    from matplotlib.colors import LinearSegmentedColormap
    cmap=LinearSegmentedColormap.from_list('market_correlation',[ORANGE,'#ffffff',BLUE])
    fig,axes=layout('Some market attitudes connect; others pull apart',
        'Ukraine · weighted correlations between respondents’ answers · latest microdata waves',
        'Higher scores favour the market endpoint; complete cases within each displayed battery.',
        (1,3),5.6,'WVS / EVS / EBRD LiTS')
    fig.subplots_adjust(left=.14,right=.98,top=.76,bottom=.38,wspace=.42)
    codes={'private_ownership':1,'competition':2,'individual_responsibility':3,'income_incentives':4}
    for ax,(survey,year) in zip(axes.flat,[('WVS',2020),('EVS',2020),('LiTS',2016)]):
        columns=list(LABELS) if survey!='LiTS' else ['private_ownership','competition','income_incentives']
        n=len(columns);matrix=np.full((n,n),np.nan)
        z=correlations[correlations.survey.eq(survey)&correlations.year.eq(year)&correlations.battery.eq('core')]
        for r in z.itertuples():
            a,b=columns.index(r.item_1),columns.index(r.item_2)
            matrix[b,a]=r.estimate
        im=ax.imshow(matrix,cmap=cmap,vmin=-1,vmax=1,aspect='equal')
        for j in range(n):
            for k in range(j):ax.text(k,j,f'{matrix[j,k]:+.2f}',ha='center',va='center',fontsize=10,color=INK)
        ax.set_xticks(range(n),[codes[c] for c in columns]);ax.set_yticks(range(n),[codes[c] for c in columns])
        ax.xaxis.tick_top();ax.grid(False)
        for spine in ax.spines.values():spine.set_visible(False)
        ax.set_title(f'{survey} {year}',loc='left',fontsize=11,weight='bold',pad=14)
    fig.text(.06,.31,'1  Private ownership     2  Competition     3  Individual responsibility     4  Income incentives',fontsize=9)
    bar=fig.colorbar(im,cax=fig.add_axes([.29,.215,.46,.025]),orientation='horizontal',ticks=[-1,0,1])
    bar.ax.set_xticklabels(['−1: opposite directions','0: no linear link','+1: move together'],fontsize=8)
    bar.outline.set_visible(False)
    save(fig,'attitude_correlation_matrices')

    fig,axes=layout('Market attitudes remain only loosely connected',
        'Ukraine · average correlation across all item pairs · approximate 95% bootstrap intervals',
        'Fixed battery within each programme: four items in WVS/EVS and three in LiTS.',
        (1,3),5.6,'WVS / EVS / EBRD LiTS')
    for ax,survey in zip(axes.flat,['WVS','EVS','LiTS']):
        z=summary[summary.survey.eq(survey)&summary.battery.eq('core')].copy()
        z=z.rename(columns={'mean_pairwise_correlation':'estimate',
                            'mean_pairwise_correlation_ci_low':'ci_low','mean_pairwise_correlation_ci_high':'ci_high'})
        errors(ax,z,BLUE,'o',survey)
        ax.set_title(survey,loc='left',fontsize=12,weight='bold')
        axis_years(ax,sorted(z.year.unique()),(-.15,.4),[-.1,0,.1,.2,.3,.4],True)
        ax.axhline(0,color=GREY,lw=.8)
    save(fig,'coherence_over_time')


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    e=pd.read_csv(ROOT/'output/tables/estimates.csv');d=pd.read_csv(ROOT/'output/tables/distributions.csv')
    values_figures(e);index_figures(e);lits_figures(e,d);monitoring_figures();additional_figures();coherence_figures()
    (ROOT/'output/tables/figure_manifest.json').write_text(json.dumps({'figures':EXPORTS,
        'uncertainty':'Microdata: approximate 95% confidence intervals. Monitoring: published point estimates; intervals unavailable.'},indent=2))
    print('Exported',len(EXPORTS),'figures; microdata estimates have approximate 95% confidence intervals.')

if __name__=='__main__':main()
