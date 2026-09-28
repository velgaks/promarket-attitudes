# ISSP question audit

Verified 28 September 2026. Ukraine participates in the 2008 Religion III and 2009/2019 Social Inequality modules in the official [GESIS inventory](https://www.gesis.org/issp/ueberblick). No Ukrainian Role of Government or Work Orientations sample is listed. The acquired releases are ZA4950 v2.3.0, ZA5400 v4.0.0 and ZA7810 v1.0.0. Ukraine 2019 is a separate national release, not part of ZA7600. Original microdata remain local.

## Scope and selection

The catalogue audits all 851 fields in the three files, retaining 59 economic attitudes and related beliefs (95 question-wave observations). Thirty-six questions meet the HTML requirement of two observations and an endpoint from 2019. Forty-nine questions have a named affirmative response; the ten open monetary questions use latest means instead. Single-wave items remain in the note's inventory and appendix, without invented trends.

Included: redistribution, taxes, public provision, unequal access to services, inequality and its explanations, fair rewards, perceived routes to success, class conflict, estimated and desired occupational pay, society shapes, and confidence in business. The international tax-aid and labour-mobility items are explicit economic extensions. General religion, identity, personal income, own-pay satisfaction, family occupation, social position and social contacts are excluded. Optional global-income fairness v66 has no valid Ukrainian 2019 observations and is excluded.

## Question and coding checks

The 2009 Ukrainian questionnaire and 2019 national questionnaire preserve comparable response scales for the replicated economic questions. The official replication crosswalk also maps the repeated modules. The tax item in both Ukrainian forms asks about *higher taxes*, without the English source's explicit income-share qualification. The getting-ahead item uses *nationality* in Ukrainian, rather than the English source's *race*. Labels follow these national wordings. University access in 2009 refers to the best chances of entry among students from the best schools; it does not imply that nobody else can enter.

Ordinal answers combine the two positive and two negative endpoints, retaining middle categories and nonresponse. The middle importance category is labelled “Important” following the national forms. The society-shape options are nominal and all five are retained, plus nonresponse. Earnings are monthly hryvnias after taxes in both national forms; values remain nominal. All nonnegative reported amounts are retained, with missing codes excluded and a winsorisation diagnostic exported.

The published 2009 variable report's Ukraine rows for V32, V33 and V36 (PDF pages 99, 101 and 107) independently reproduce every substantive raw response count and the rounded valid-response percentages. These anchors use the codebook's unweighted valid denominator; analysis charts use the supplied weights and retain nonresponse in categorical denominators. See `issp_published_checks.csv`.

## Estimation and coverage

Adults aged 18+; supplied WEIGHT; age groups 18–34, 35–54 and 55+. All released Ukrainian respondents have eligible ages. Numeric means exclude nonnumeric answers. Categorical shares retain all adults, including don't-know and missing responses. Intervals use approximate weighted respondent linearization because verified cluster/stratum identifiers are not supplied.

The 2019 national technical report identifies occupied Crimea and Donetsk/Luhansk areas as excluded, and its README flags methodological deviations from ISSP sampling standards. Weighting adjusts for sex and age. Common-geography checks exclude region codes 1, 7 and 13 in both inequality waves (Crimea/Sevastopol, Donetsk, Luhansk). They reproduce the broad redistribution and service-access patterns. All estimates also have unweighted checks.

Correlations are weighted Pearson correlations among pairwise-valid answers, aligned so higher means more agreement, importance or perceived fairness. Joint endorsement means either of the two strongest responses to both named propositions, divided by all eligible adults. These are specific pair comparisons, not a broad latent-ideology score.

## Inventory

| Question | Years | Original fields | HTML trend |
|---|---|---|---|
| Confidence in business and industry? | 2008 | 2008: V15 | No: one observation |
| Income differences are too large? | 2009, 2019 | 2009: V32; 2019: v21 | Yes |
| Government should reduce income differences? | 2009, 2019 | 2009: V33; 2019: v22 | Yes |
| Government should provide a decent living for unemployed people? | 2009, 2019 | 2009: V34; 2019: v23 | Yes |
| Government should spend less on benefits for poor people? | 2009 | 2009: V35 | No: one observation |
| Getting to the top requires being corrupt? | 2009 | 2009: V17 | No: one observation |
| Students from the best secondary schools have the best chances of university education? | 2009 | 2009: V18 | No: one observation |
| Only the rich can afford university? | 2009 | 2009: V19 | No: one observation |
| People have equal chances of entering university regardless of background? | 2009 | 2009: V20 | No: one observation |
| Should richer people pay higher, the same or lower taxes? | 2009, 2019 | 2009: V36; 2019: v28 | Yes |
| Are current taxes on high incomes too high or too low? | 2009, 2019 | 2009: V37; 2019: v29 | Yes |
| Is it fair that richer people can buy better healthcare? | 2009, 2019 | 2009: V38; 2019: v30 | Yes |
| Is it fair that richer people can buy better education for their children? | 2009, 2019 | 2009: V39; 2019: v31 | Yes |
| Which diagram best describes the shape of Ukrainian society? | 2009, 2019 | 2009: V54; 2019: v48 | Yes |
| Which shape of society would you prefer for Ukraine? | 2009, 2019 | 2009: V55; 2019: v49 | Yes |
| Importance for getting ahead: coming from a wealthy family? | 2009, 2019 | 2009: V6; 2019: v1 | Yes |
| Importance for getting ahead: having well-educated parents? | 2009, 2019 | 2009: V7; 2019: v2 | Yes |
| Importance for getting ahead: having a good education? | 2009, 2019 | 2009: V8; 2019: v3 | Yes |
| Importance for getting ahead: having ambition? | 2009 | 2009: V9 | No: one observation |
| Importance for getting ahead: hard work? | 2009, 2019 | 2009: V10; 2019: v4 | Yes |
| Importance for getting ahead: knowing the right people? | 2009, 2019 | 2009: V11; 2019: v5 | Yes |
| Importance for getting ahead: political connections? | 2009, 2019 | 2009: V12; 2019: v6 | Yes |
| Importance for getting ahead: giving bribes? | 2009, 2019 | 2009: V13; 2019: v7 | Yes |
| Importance for getting ahead: ethnic background (nationality)? | 2009, 2019 | 2009: V14; 2019: v8 | Yes |
| Importance for getting ahead: a person’s religion? | 2009, 2019 | 2009: V15; 2019: v9 | Yes |
| Importance for getting ahead: being born a man or woman? | 2009, 2019 | 2009: V16; 2019: v10 | Yes |
| What should determine pay: job responsibility? | 2009, 2019 | 2009: V47; 2019: v44 | Yes |
| What should determine pay: education and training? | 2009, 2019 | 2009: V48; 2019: v45 | Yes |
| What should determine pay: what is needed to support a family? | 2009 | 2009: V49 | No: one observation |
| What should determine pay: children to support? | 2009, 2019 | 2009: V50; 2019: v46 | Yes |
| What should determine pay: how well the job is done? | 2009, 2019 | 2009: V51; 2019: v47 | Yes |
| What should determine pay: how hard the person works? | 2009 | 2009: V52 | No: one observation |
| How much conflict is there between rich and poor? | 2009, 2019 | 2009: V40; 2019: v36 | Yes |
| How much conflict is there between working and middle classes? | 2009, 2019 | 2009: V41; 2019: v37 | Yes |
| How much conflict is there between management and workers? | 2009, 2019 | 2009: V42; 2019: v38 | Yes |
| How much conflict is there between top and bottom of society? | 2009 | 2009: V43 | No: one observation |
| How much does a doctor earn per month after taxes? | 2009, 2019 | 2009: V22; 2019: v11 | Yes |
| How much should a doctor earn per month after taxes? | 2009, 2019 | 2009: V27; 2019: v16 | Yes |
| How much does a corporate chairman earn per month after taxes? | 2009, 2019 | 2009: V23; 2019: v12 | Yes |
| How much should a corporate chairman earn per month after taxes? | 2009, 2019 | 2009: V28; 2019: v17 | Yes |
| How much does a shop assistant earn per month after taxes? | 2009, 2019 | 2009: V24; 2019: v13 | Yes |
| How much should a shop assistant earn per month after taxes? | 2009, 2019 | 2009: V29; 2019: v18 | Yes |
| How much does an unskilled factory worker earn per month after taxes? | 2009, 2019 | 2009: V25; 2019: v14 | Yes |
| How much should an unskilled factory worker earn per month after taxes? | 2009, 2019 | 2009: V30; 2019: v19 | Yes |
| How much does a cabinet minister earn per month after taxes? | 2009, 2019 | 2009: V26; 2019: v15 | Yes |
| How much should a cabinet minister earn per month after taxes? | 2009, 2019 | 2009: V31; 2019: v20 | Yes |
| Companies should reduce differences in employee pay? | 2019 | 2019: v24 | No: one observation |
| Politicians do not care about reducing income differences? | 2019 | 2019: v26 | No: one observation |
| Economic differences between rich and poor countries are too large? | 2019 | 2019: v33 | No: one observation |
| People in wealthy countries should pay additional tax to help poorer countries? | 2019 | 2019: v34 | No: one observation |
| People from poor countries should be allowed to work in wealthy countries? | 2019 | 2019: v35 | No: one observation |
| Workers need extra pay to acquire skills and qualifications? | 2019 | 2019: v62 | No: one observation |
| Large income differences are necessary for prosperity? | 2019 | 2019: v63 | No: one observation |
| Inequality persists because it benefits the rich and powerful? | 2019 | 2019: v64 | No: one observation |
| Inequality persists because ordinary people do not unite against it? | 2019 | 2019: v65 | No: one observation |
| Is government successful in reducing income differences? | 2019 | 2019: v27 | No: one observation |
| Is the income distribution in Ukraine fair? | 2019 | 2019: v50 | No: one observation |
| How angry do differences in wealth between rich and poor make you? | 2019 | 2019: v32 | No: one observation |
| Who should have the greatest responsibility for reducing income differences? | 2019 | 2019: v25 | No: one observation |

## Reproduction and provenance

Download the named releases through GESIS into `data/raw/issp`. `acquire_issp_sources.py` retrieves public documentation and inventories downloaded originals. Run `issp_analysis.py`, `issp_documentation.py`, then the appendix, inventory, trend and note stages in `run.py`. The full run also regenerates all earlier surveys. `issp.json` and `issp_acquisition.json` record versions, source URLs and file hashes; `issp_question_crosswalk.csv` records fields, scale labels, missingness and comparability. `issp_variable_catalogue.csv` preserves inclusion/exclusion decisions for every field. Export packages contain code, documentation and aggregates, not licensed respondent records.
