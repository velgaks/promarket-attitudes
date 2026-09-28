"""Comparable national indicators from verified Monitoring published percentages.

Every estimate is a linear combination of source cells, exported for audit.
No respondent-level variance or age composition is inferred from marginals.
"""
import json
import numpy as np
import pandas as pd
from analyze import ROOT

T = ROOT / 'output/tables'


def main():
    raw = pd.read_csv(T / 'monitoring_published_results.csv')
    assert not raw.duplicated(['item', 'year', 'response']).any()
    definitions = []
    results = []
    trace = []

    def add(item, label, terms, unit='percent', interpretation='Expressed support; all source respondents in denominator'):
        """terms are (source_item, response, coefficient). Require all cells."""
        years = sorted(set.intersection(*[
            set(raw.loc[raw.item.eq(i) & raw.response.eq(r), 'year']) for i, r, _ in terms
        ]))
        definitions.append(dict(item=item, label=label, unit=unit,
            formula=' + '.join(f'{w:g} * {i}:{r}' for i, r, w in terms),
            denominator='all_respondents_as_published', interpretation=interpretation,
            years=';'.join(map(str, years)), uncertainty='not_available_from_published_aggregates'))
        for year in years:
            value = 0.
            for source_item, response, coefficient in terms:
                z = raw[raw.item.eq(source_item) & raw.year.eq(year) & raw.response.eq(response)]
                assert len(z) == 1
                r = z.iloc[0]
                value += coefficient * r.percent
                trace.append(dict(item=item, year=year, source_item=source_item, response=response,
                    coefficient=coefficient, percent=r.percent, contribution=coefficient*r.percent,
                    source_file=r.source_file, pdf_page=r.pdf_page, printed_page=r.printed_page,
                    source_url=r.source_url))
            results.append(dict(survey='Monitoring', item=item, year=year, age_group='All',
                estimate=value, ci_low=np.nan, ci_high=np.nan, unit=unit,
                denominator='all_respondents_as_published', period='main_through_2020' if year <= 2020 else 'later_extension',
                uncertainty='not_available_from_published_aggregates'))

    def share(item, label, responses):
        add(item, label, [(item, response, 1.) for response in responses])

    share('private_business', 'Approve developing private business', ['rather_approve', 'strongly_approve'])
    for sector in ['small', 'large', 'land']:
        share(f'privatise_{sector}', f'Positive towards privatisation: {sector}', ['positive'])
        share(f'retrospective_{sector}', f'Past privatisation was worth doing: {sector}', ['rather_yes', 'yes'])
        share(f'existing_private_{sector}', f'Positive towards existing private ownership: {sector}', ['rather_positive', 'positive'])
        share(f'renationalise_{sector}', f'Oppose returning private ownership to state: {sector}', ['rather_no', 'no'])
    share('land_sales_general', 'Allow buying and selling land (general wording)', ['yes'])
    share('land_sales_agricultural', 'Allow buying and selling agricultural land', ['yes'])
    share('work_private_employer', 'Willing to work for a private employer', ['rather_yes', 'yes'])
    share('socialism_capitalism_political_support', 'Support political forces advocating capitalism', ['capitalism'])
    share('land_ownership_rights', 'Full land ownership including right to sell', ['full_ownership_including_sale'])
    for response, label in [
        ('minimal_state_market', 'Market with minimal state involvement'),
        ('mixed_state_market', 'Combine state management and market methods'),
        ('planned_economy', 'Return to a planned economy')]:
        add('state_role_' + response, label, [('state_market_role', response, 1.)])
    for response, label in [
        ('nationalise', 'Nationalise private enterprises'),
        ('retain_state_firms', 'Retain existing state enterprises'),
        ('privatise_except_efficient_state_firms', 'Privatise except efficient state enterprises'),
        ('broad_privatisation', 'Broad privatisation')]:
        add('ownership_policy_' + response, label, [('ownership_policy', response, 1.)])
    add('ownership_policy_any_privatisation', 'Choose either privatisation option', [
        ('ownership_policy', 'privatise_except_efficient_state_firms', 1.),
        ('ownership_policy', 'broad_privatisation', 1.)])
    add('privatisation_support_index', 'Privatisation support index: three-sector average',
        [(f'privatise_{sector}', 'positive', 1/3) for sector in ['small', 'large', 'land']],
        unit='index_0_100', interpretation='Mean of three affirmative shares, equal weights, all respondents. '
        '0 = no expressed support; 100 = everyone positive on every sector. Nonaffirmative answers, '
        'including no answer, add zero; this does not equate indifference with opposition. '
        'An aggregate endorsement measure, not a complete-case respondent index or a broad market-attitude scale.')

    e = pd.DataFrame(results).sort_values(['item', 'year'])
    tr = pd.DataFrame(trace)
    assert not e.duplicated(['item', 'year']).any()
    assert e.estimate.between(0, 100).all()
    assert e[['ci_low', 'ci_high']].isna().all().all()
    summed = tr.groupby(['item', 'year']).contribution.sum()
    actual = e.set_index(['item', 'year']).estimate
    assert np.allclose(actual, summed.reindex(actual.index), rtol=1e-12, atol=1e-12)
    # Preserve the documented wording break rather than manufacture a 2020 jump.
    assert 2020 not in set(e.loc[e.item.eq('privatise_land'), 'year'])
    assert 2020 in set(e.loc[e.item.eq('existing_private_land'), 'year'])
    idx = e[e.item.eq('privatisation_support_index')]
    assert len(idx) == 21 and set(idx.year) == set(e.loc[e.item.eq('privatise_small'), 'year'])
    # Published 2014 all-respondent approval is 60.2, not the valid-answer figure 61.5.
    assert np.isclose(e.loc[e.item.eq('private_business') & e.year.eq(2014), 'estimate'].item(), 60.2)
    # Rejection of renationalisation, not endorsement, is the pro-private direction.
    assert set(tr.loc[tr.item.str.startswith('renationalise_'), 'response']) == {'rather_no', 'no'}
    role=e[e.item.str.startswith('state_role_')&e.year.le(2020)].pivot(index='year',columns='item',values='estimate')
    assert role.idxmax(axis=1).eq('state_role_mixed_state_market').all()
    # Include undecided and every policy option when verifying the narrative ranking.
    policy=raw[raw.item.eq('ownership_policy')].pivot(index='year',columns='response',values='percent')
    assert policy.idxmax(axis=1).eq('privatise_except_efficient_state_firms').all()
    e.to_csv(T / 'monitoring_estimates.csv', index=False)
    tr.to_csv(T / 'monitoring_analysis_trace.csv', index=False)
    pd.DataFrame(definitions).to_csv(ROOT / 'docs/monitoring_indicator_definitions.csv', index=False)
    result = dict(status='passed', indicators=len(definitions), estimates=len(e),
        underlying_question_items=raw.item.nunique(), source_contributions=len(tr),
        main_period_estimates=int(e.year.le(2020).sum()), later_estimates=int(e.year.gt(2020).sum()),
        privatisation_index_waves=len(idx), confidence_intervals='unavailable; not fabricated',
        checks=['Every derived estimate reconciles to its named source cells',
                'Unchanged denominators include undecided and nonresponse',
                'Original privatisation and existing private ownership remain separate',
                'Renationalisation coding reversed', 'Fixed three-sector index composition'])
    (T / 'monitoring_analysis_validation.json').write_text(json.dumps(result, indent=2), encoding='utf8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
