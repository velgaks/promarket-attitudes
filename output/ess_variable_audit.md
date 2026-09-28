# ESS: variables for the Ukraine market-attitudes note and HTML

The supplied files add **47 questions**, covering **63 question-wave observations**. Six qualify for the HTML trend gallery (at least two waves, latest fieldwork in 2019 or later). The integrated file covers rounds 2–6 and 11; ESS10UAe4 is the separate Ukrainian related study.

## Best additions

- **Redistribution (`gincdif`)**: the strongest direct policy time series, 2005, 2006–07, 2009, 2011, 2013, 2022 and 2024. Plot agree/disagree, neutral and missing responses together.
- **Social protection as democracy (`gvctzpv`, `grdfinc`)**: 2013 and 2022. Plot original 0–10 means with 95% intervals.
- **Delivery versus aspiration (`gvctzpvc`, `grdfincc`)**: the matching 2013/2022 evaluations of actual poverty protection and inequality reduction. Keep the wording distinct from desired policy.
- **Economic effect of immigration (`imbgeco`)**: seven waves through 2024; original 0–10 means. This is a belief about economic openness, not a direct vote for immigration or markets.
- **Equality versus incentives (`dfincac`, `smdfslv`)**: 2009 provides within-person comparisons with redistribution. Available in the note, not a recent trend.
- **Welfare state (`gv*`, `sb*`, `ditxssp`, `txearn`, `earnpen`, `earnueb`)**: the 2009 module distinguishes public provision, tax/spending trade-offs, incentives, contribution-based benefits and perceived consequences.
- **Business beliefs and economic norms**: 2005 questions about profits, service quality, collusion, honesty, tax evasion and trust.
- **Labour regulation (`fineqpy`, `eqparlv`)**: 2024 support for equal-pay fines and equal parental-leave requirements. One-wave additions to the note and latest-response appendix.

## Full selected inventory

Years below are actual Ukrainian fieldwork years, not nominal ESS round dates. In machine-readable year fields the pooled 2006–07 round is stored as 2007; chart ticks show 2006–07.

| Variable | Question | Fieldwork years | Display type | HTML |
|---|---|---|---|---|
| `gincdif` | Should the government take measures to reduce differences in income levels? | 2005, 2006–07, 2009, 2011, 2013, 2022, 2024 | ordinal | Yes |
| `bsnprft` | Businesses only interested in profit, not improve service/quality? | 2005 | ordinal | No: single wave / old endpoint |
| `cmprcti` | Nowadays customer/consumer are in better position to protect interest? | 2005 | ordinal | No: single wave / old endpoint |
| `ctzchtx` | Citizens should not cheat on taxes? | 2005 | ordinal | No: single wave / old endpoint |
| `frmwktg` | Nowadays large firms work together in order to keep prices high? | 2005 | ordinal | No: single wave / old endpoint |
| `mnyacth` | If you want to make money, you can't always act honestly? | 2005 | ordinal | No: single wave / old endpoint |
| `scbevts` | Society better off if everyone looked after themselves? | 2005 | ordinal | No: single wave / old endpoint |
| `imbgeco` | Is immigration bad or good for Ukraine's economy? | 2005, 2006–07, 2009, 2011, 2013, 2022, 2024 | numeric | Yes |
| `tstfnch` | Trust financial companies/bank/insurers deal honestly with you? | 2005 | numeric | No: single wave / old endpoint |
| `tstpboh` | Trust public officials deal honestly with you? | 2005 | numeric | No: single wave / old endpoint |
| `tstrprh` | Trust plumber/builder/mechanic/other repairer deal honestly with you? | 2005 | numeric | No: single wave / old endpoint |
| `pyavtxw` | Someone paying cash without receipt to avoid VAT or tax, how wrong? | 2005 | ordinal | No: single wave / old endpoint |
| `dfincac` | Large differences in income acceptable to reward talents and efforts? | 2009 | ordinal | No: single wave / old endpoint |
| `smdfslv` | For fair society, differences in standard of living should be small? | 2009 | ordinal | No: single wave / old endpoint |
| `bennent` | Many manage to obtain benefits/services not entitled to? | 2009 | ordinal | No: single wave / old endpoint |
| `insfben` | Insufficient benefits in country to help people in real need? | 2009 | ordinal | No: single wave / old endpoint |
| `lbenent` | Many with very low incomes get less benefit than legally entitled to? | 2009 | ordinal | No: single wave / old endpoint |
| `prtsick` | Employees often pretend they are sick to stay at home? | 2009 | ordinal | No: single wave / old endpoint |
| `sbbsntx` | Social benefits/services cost businesses too much in taxes/charges? | 2009 | ordinal | No: single wave / old endpoint |
| `sbcwkfm` | Social benefits/services make it easier to combine work and family? | 2009 | ordinal | No: single wave / old endpoint |
| `sbenccm` | Social benefits/services encourage people other countries to come live here? | 2009 | ordinal | No: single wave / old endpoint |
| `sbeqsoc` | Social benefits/services lead to a more equal society? | 2009 | ordinal | No: single wave / old endpoint |
| `sblazy` | Social benefits/services make people lazy? | 2009 | ordinal | No: single wave / old endpoint |
| `sblwcoa` | Social benefits/services make people less willing care for one another? | 2009 | ordinal | No: single wave / old endpoint |
| `sblwlka` | Social benefits/services make people less willing look after themselves/family? | 2009 | ordinal | No: single wave / old endpoint |
| `sbprvpv` | Social benefits/services prevent widespread poverty? | 2009 | ordinal | No: single wave / old endpoint |
| `sbstrec` | Social benefits/services place too great strain on economy? | 2009 | ordinal | No: single wave / old endpoint |
| `uentrjb` | Most unemployed people do not really try to find a job? | 2009 | ordinal | No: single wave / old endpoint |
| `ditxssp` | Government decrease/increase taxes and social spending? | 2009 | numeric | No: single wave / old endpoint |
| `gvcldcr` | Child care services for working parents, governments' responsibility? | 2009 | numeric | No: single wave / old endpoint |
| `gvhlthc` | Health care for the sick, governments' responsibility? | 2009 | numeric | No: single wave / old endpoint |
| `gvjbevn` | Job for everyone, governments' responsibility? | 2009 | numeric | No: single wave / old endpoint |
| `gvpdlwk` | Paid leave from work to care for sick family, governments' responsibility? | 2009 | numeric | No: single wave / old endpoint |
| `gvslvol` | Standard of living for the old, governments' responsibility? | 2009 | numeric | No: single wave / old endpoint |
| `gvslvue` | Standard of living for the unemployed, governments' responsibility? | 2009 | numeric | No: single wave / old endpoint |
| `imrccon` | Immigrants receive more or less than they contribute? | 2009 | numeric | No: single wave / old endpoint |
| `earnpen` | Higher or lower earners should get larger old age pensions? | 2009 | nominal | No: single wave / old endpoint |
| `earnueb` | Higher or lower earners should get larger unemployment benefits? | 2009 | nominal | No: single wave / old endpoint |
| `txearn` | Taxation for higher versus lower earners? | 2009 | nominal | No: single wave / old endpoint |
| `imsclbn` | When should immigrants obtain rights to social benefits/services? | 2009 | ordinal | No: single wave / old endpoint |
| `gvprppv` | Government do more to prevent people falling into poverty? | 2011 | ordinal | No: single wave / old endpoint |
| `gvctzpv` | How important is government protection against poverty for democracy? | 2013, 2022 | numeric | Yes |
| `grdfinc` | How important is government reduction of income differences for democracy? | 2013, 2022 | numeric | Yes |
| `gvctzpvc` | To what extent does the government in Ukraine protect citizens against poverty? | 2013, 2022 | numeric | Yes |
| `grdfincc` | To what extent does the government in Ukraine reduce income differences? | 2013, 2022 | numeric | Yes |
| `fineqpy` | Making businesses pay a fine when they pay men more than women for doing the same work? | 2024 | ordinal | No: single wave / old endpoint |
| `eqparlv` | Require both parents to take equal periods of paid leave to care for their child? | 2024 | ordinal | No: single wave / old endpoint |

## Selection boundary

All 2,240 distinct supplied variable labels are catalogued in `docs/ess_variable_catalogue.csv`, with selection decisions. This includes data-management fields and questions asked only in other countries. Selection was checked against actual Ukrainian responses; the presence of a column alone was not treated as availability. Question wording and answer codes come from the bundled ESS codebook and the Ukrainian ESS10 questionnaire.

General political trust, left/right self-placement, satisfaction with the economy, household income, employment history and personal job conditions are not preferences for economic institutions. Broad personal values (equality, wealth, freedom and achievement) are contextual traits, and the revised R11 value items are not automatically spliced to their predecessors. COVID-specific policy trade-offs and broad gender-role beliefs are outside this note's economic-policy scope. Equal-pay enforcement and parental-leave requirements are included as specific labour regulations. No direct ownership or competition variable was found in these Ukrainian files; an ESS-wide market index would change meaning with module availability.

## Measurement and verification

Adults 18+, known age, supplied positive `pspwght` weights. `pspwght` already includes design weighting. The supplied 2024 `pspwght` equals `dweight`; this is recorded rather than assumed to provide additional demographic adjustment. Categorical shares include all eligible adults and preserve missing-response categories. Numeric charts show means among valid 0–10 responses with original directions. The latest affirmative appendix additionally exports explicitly labelled above-midpoint shares, following the existing appendix convention; they do not replace numeric means in charts.

2022 and 2024 intervals account for strata and primary sampling units using Taylor linearization, keeping all PSUs in adult/age domain calculations. Earlier files lack those identifiers, so their intervals are approximate. Weighted/unweighted and consistent territorial-exclusion comparisons are in `ess_sensitivity.csv`. Codes for Crimea/Sevastopol and Donetsk/Luhansk are mapped separately by round. The 2024 resident sample cannot represent people abroad or inaccessible territories.

The 2009 pairwise correlations align scores as stronger agreement with each named statement. Joint-agreement shares retain all adults in the denominator. This tests combinations of particular beliefs, without assuming a single market ideology.

## Sources and reproduction

- [ESS data portal](https://www.europeansocialsurvey.org/data-portal): integrated rounds 2/3.6, 3/3.7, 4/4.6, 5/3.6, 6/2.7 and 11/4.2; supplied SPSS subset and HTML codebook.
- [Ukrainian ESS10 national-team repository](https://github.com/KSE-Sociological-Center/ESS10_Ukraine): edition 4 SPSS, Ukrainian questionnaire, sampling/weighting PDF and version log. Documented collection: 18 January–8 February 2022, matching interview start timestamps. Later end timestamps are not treated as additional interview dates.
- [ESS2 documentation report, p. 204](https://stessrelpubprodwe.blob.core.windows.net/data/round2/survey/ESS2_data_documentation_report_e03_7.pdf#page=204): confirms 28 January–10 March 2005. Other chart years are verified from interview start dates. Supplied R11 starts span 30 April–3 July 2024.
- [ESS weighting guidance](https://www.europeansocialsurvey.org/methodology/ess-methodology/data-processing-and-archiving/weighting).

Run `python scripts/ess_analysis.py`, then the affected appendix/inventory/chart/note stages, or `python scripts/run.py` for the full pipeline. Source versions, hashes and acquisition instructions are in `data/source_manifests/ess.json`. Raw respondent data are excluded from export ZIPs.
