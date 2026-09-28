"""Build the opening question/survey/year inventory from analysed observations."""
import json
import pandas as pd
from analyze import TABLES


def build_inventory():
    latest = pd.read_csv(TABLES / 'latest_positive_shares.csv')
    sources = {name: pd.read_csv(TABLES / name) for name in latest.source_table.unique()}
    rows = []
    for r in latest.itertuples():
        source = sources[r.source_table]
        source = source[source.survey.eq(r.survey) & source.item.eq(r.item)]
        if 'age_group' in source:
            source = source[source.age_group.eq('All')]
        years = sorted(source.year.astype(int).unique().tolist())
        assert years and years[-1] == r.year, (r.survey, r.item)
        rows.append(dict(question=r.question, survey=r.survey, item=r.item,
                         years=', '.join(map(str, years)), source_table=r.source_table))
    # Open monetary responses have means, not a meaningful affirmative percentage.
    issp=pd.read_csv(TABLES/'issp_estimates.csv')
    for item,z in issp[issp.age_group.eq('All')&issp.item.str.startswith('earn_')].groupby('item'):
        rows.append(dict(question=z.iloc[0].question,survey='ISSP',item=item,
            years=', '.join(map(str,sorted(z.year.astype(int).unique()))),source_table='issp_estimates.csv'))
    detail = pd.DataFrame(rows)
    detail.to_csv(TABLES / 'question_year_inventory.csv', index=False, encoding='utf-8-sig')

    # Combine named responses or related battery subitems only when every member
    # has exactly the same observed years. Every original item stays in detail.
    groups = []
    def group(survey, items, question):
        selected = detail[detail.survey.eq(survey) & detail.item.isin(items)]
        assert set(selected.item) == set(items), (survey, items)
        assert selected.years.nunique() == 1, (survey, items, 'Different coverage')
        groups.append((survey, items, question))

    for survey in ['WVS', 'EVS']:
        group(survey, ['E036', 'E039', 'E037', 'E035'],
              'Private vs state ownership; benefits vs harms of competition; individual vs government responsibility; income equality vs incentives for effort')
        group(survey, ['E224', 'E227'],
              'Are taxing the rich to help the poor and state aid for unemployment essential to democracy?')
        group(survey, ['E069_05', 'E069_13'], 'Confidence in labour unions and major companies')
    group('LiTS', ['connections_a', 'connections_b', 'connections_d'],
          'Importance of connections for government jobs, private-sector jobs and permits')
    group('LiTS', ['poverty_1', 'poverty_2', 'poverty_3', 'poverty_4'],
          'Why are people poor: bad luck, laziness, injustice or an inevitable part of modern life?')
    group('LiTS', ['success_effort', 'success_skill'], 'What matters most for success: effort/hard work or intelligence/skills?')
    group('LiTS', ['trust_banks', 'trust_foreign_investors', 'trust_unions'], 'Trust in banks, foreign investors and trade unions')
    group('LiTS', ['competition', 'income_incentives', 'private_ownership'],
          'Benefits vs harms of competition; income equality vs incentives; private vs state ownership')
    group('LiTS', ['keep_private', 'nationalise', 'reprivatise'],
          'What should happen to privatised firms: retain current owners, nationalise or re-privatise?')
    group('LiTS', ['pay_a', 'pay_b', 'pay_c', 'pay_d'],
          'Give income or pay more taxes for education, health, climate action and people in need?')
    group('LiTS', [f'state_{i}' for i in range(1, 7)],
          'State involvement in inequality, employment, energy/food prices, utilities and large companies')
    group('LiTS', [f'support_{i}' for i in range(1, 8)],
          'Who deserves state support: elderly people, people with disabilities, veterans, families, working poor, unemployed people or nobody?')
    group('LiTS', ['spend_education', 'spend_health', 'spend_housing', 'spend_pensions', 'spend_public_infrastructure', 'spend_the_environment'],
          'First spending priority: education, health, housing, pensions, infrastructure or environment')
    group('Pew', ['success_Q66a', 'success_Q66b', 'success_Q66c', 'success_Q66d', 'success_Q66f', 'success_Q66g'],
          'Importance for getting ahead: education, hard work, connections, bribes, wealthy family and luck')
    group('Pew', ['foreign_acquisitions', 'foreign_factories'], 'Are foreign purchases of domestic companies and new foreign-owned factories good?')
    group('Pew', ['freedom_vs_welfare', 'welfare_vs_freedom'], 'Freedom from state interference vs guaranteeing that nobody is in need')
    group('Pew', ['high_tax_redistribution', 'low_tax_growth'], 'Reduce inequality through higher taxes and redistribution or lower taxes and growth?')
    group('Pew', ['trade_jobs', 'trade_prices', 'trade_wages'], 'Does trade create jobs, reduce prices and increase wages?')
    group('Pew', ['transition_business', 'transition_ordinary', 'transition_politicians'], 'Have business people, ordinary people and politicians benefited from post-1991 changes?')
    group('Monitoring', ['manager_worker_conflict', 'owner_worker_conflict', 'rich_poor_conflict'],
          'Conflict between managers and workers, owners and employees, and rich and poor')
    group('Monitoring', [f'respect_owners_{i}' for i in range(1, 5)],
          'Feelings towards small/large business owners and landowners farming themselves or hiring workers')
    group('Monitoring', [f'business_duty_{i}' for i in range(1, 9)],
          'Responsibilities of business: taxes/investment/jobs, working conditions, training, environment, politics, charity, culture/sport and regional problems')
    group('Monitoring', [f'crisis_{i}' for i in range(1, 14)],
          'Anti-crisis measures: nationalisation/privatisation, taxes on big business, West/Russia ties, wages, IMF policy, industrial/SME jobs, foreign/domestic capital and land sales')
    for prefix, label in [
        ('existing_private', 'Approval of existing private ownership: small enterprises, large enterprises and land'),
        ('privatise', 'Support for privatisation: small enterprises, large enterprises and land'),
        ('renationalise', 'Return private assets to the state: small enterprises, large enterprises and land'),
        ('retrospective', 'Was privatisation worth doing: small enterprises, large enterprises and land?'),
    ]:
        group('Monitoring', [prefix + '_' + s for s in ['small', 'large', 'land']], label)
    group('Monitoring', ['ownership_mixed', 'ownership_private', 'ownership_state'], 'Preferred ownership mix: private, mixed or state')
    group('Monitoring', ['ownership_policy_broad_privatisation', 'ownership_policy_nationalise', 'ownership_policy_privatise_except_efficient_state_firms', 'ownership_policy_retain_state_firms'],
          'Ownership policy: broad/selective privatisation, retaining state firms or nationalisation')
    group('Monitoring', ['state_role_minimal_state_market', 'state_role_mixed_state_market', 'state_role_planned_economy'],
          'Preferred system: minimal state involvement, mixed state/market economy or planning')
    group('Monitoring', ['trust_banks', 'trust_unions'], 'Trust in banks and trade unions')
    group('ESS',['gvctzpv','grdfinc'],'Importance of poverty protection and reducing income gaps for democracy')
    group('ESS',['gvctzpvc','grdfincc'],'Does government actually protect against poverty and reduce income gaps?')
    group('ESS',['bsnprft','frmwktg','cmprcti'],'Business profits vs customer service; collusion to keep prices high; consumer protection')
    group('ESS',['ctzchtx','mnyacth','scbevts'],'Tax honesty; making money honestly; whether society benefits from everyone looking after themselves')
    group('ESS',['tstfnch','tstpboh','tstrprh'],'Trust in honest dealings by financial companies, public officials and tradespeople')
    group('ESS',['dfincac','smdfslv'],'Income differences as rewards for effort; small living-standard differences as a condition of fairness')
    group('ESS',['gvcldcr','gvhlthc','gvjbevn','gvpdlwk','gvslvol','gvslvue'],'Government responsibility for childcare, healthcare, jobs, care leave, pensions and unemployment provision')
    group('ESS',['earnpen','earnueb'],'Should higher/lower earners receive more, or equal pensions and unemployment benefits?')
    group('ESS',['sbbsntx','sbcwkfm','sbenccm','sbeqsoc','sblazy','sblwcoa','sblwlka','sbprvpv','sbstrec'],'Effects of social benefits: business taxes, work/family, immigration, equality, laziness, mutual care, self-reliance, poverty and the economy')
    group('ESS',['bennent','insfben','lbenent'],'Benefit misuse, insufficient help and failure to receive legal entitlements')
    group('ESS',['prtsick','uentrjb'],'Do employees pretend to be sick; do unemployed people try to find work?')
    group('ESS',['fineqpy','eqparlv'],'Fines for unequal pay for equal work; requiring equal parental leave')
    for prefix,title in [('ahead_','What helps people get ahead: family resources, education, effort, connections and discrimination'),
                         ('pay_','What should determine pay: responsibility, qualifications, performance and family needs'),
                         ('conflict_','Economic conflict between social groups'),
                         ('earn_actual_','Estimated monthly earnings of doctors, corporate chairmen, shop assistants, factory workers and ministers (nominal UAH)'),
                         ('earn_ideal_','Preferred monthly earnings of doctors, corporate chairmen, shop assistants, factory workers and ministers (nominal UAH)')]:
        selected=detail[detail.survey.eq('ISSP')&detail.item.str.startswith(prefix)]
        for years,z in selected.groupby('years'):
            if len(z)>1:group('ISSP',z.item.tolist(),title)

    lookup = {}
    for i, (survey, items, question) in enumerate(groups):
        for item in items:
            assert (survey, item) not in lookup
            lookup[survey, item] = (i, question)
    compact = []
    seen = set()
    for r in detail.itertuples():
        key = (r.survey, r.item)
        if key in lookup:
            i, question = lookup[key]
            if i in seen:
                continue
            seen.add(i)
            items = groups[i][1]
        else:
            question, items = r.question, [r.item]
        compact.append(dict(question=question, survey=r.survey, years=r.years, items=';'.join(items)))
    compact = pd.DataFrame(compact)
    priority = {
        'WVS': ['E036'], 'EVS': ['E036'],
        'ESS': ['gincdif','gvctzpv','grdfinc','dfincac','ditxssp'],
        'ISSP': ['redistribution','income_gap','unemployed_living','tax_rich','buy_health','buy_education'],
        'LiTS': ['market', 'competition', 'reduce_gap', 'keep_private'],
        'Pew': ['transition_approval', 'free_market_better', 'government_care_poor'],
        'Monitoring': ['private_business', 'privatise_small', 'existing_private_small',
                       'renationalise_small', 'retrospective_small',
                       'state_role_minimal_state_market', 'ownership_policy_broad_privatisation'],
    }
    order = {survey: i for i, survey in enumerate(priority)}
    compact['_survey_order'] = compact.survey.map(order)
    compact['_priority'] = [min([priority[r.survey].index(item) for item in r.items.split(';')
                                if item in priority[r.survey]] or [100]) for r in compact.itertuples()]
    compact = compact.sort_values(['_survey_order', '_priority'], kind='stable').drop(columns=['_survey_order', '_priority'])
    represented = [(r.survey, item) for r in compact.itertuples() for item in r.items.split(';')]
    assert len(represented) == len(set(represented)) == len(detail)
    assert set(represented) == set(zip(detail.survey, detail.item))
    compact.to_csv(TABLES / 'question_year_inventory_compact.csv', index=False, encoding='utf-8-sig')
    status = dict(status='passed', indicators=len(detail), display_rows=len(compact),
                  survey_item_years=sum(len(r.years.split(', ')) for r in detail.itertuples()),
                  scope=f'All {len(detail)} included indicators; years come from generated national results; battery rows share identical coverage. ESS 2007 denotes the pooled 2006–07 fieldwork round.')
    (TABLES / 'question_inventory_validation.json').write_text(json.dumps(status, indent=2), encoding='utf8')
    return compact


if __name__ == '__main__':
    result = build_inventory()
    print(f'Opening inventory: {len(result)} rows; complete indicator coverage verified.')
