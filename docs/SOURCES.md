# Data sources and methods

These citations identify the releases used in **Market and state attitudes in Ukraine**. Dates in charts refer to Ukrainian fieldwork, which can differ from a dataset’s round label or publication year. Source files, acquisition URLs and checksums are recorded in the [manifests](../data/source_manifests/).

## World Values Survey (WVS)

Haerpfer, C., Inglehart, R., Moreno, A., Welzel, C., Kizilova, K., Diez-Medrano, J., Lagos, M., Norris, P., Ponarin, E., and Puranen, B. (2024). *World Values Survey Time-Series (1981–2022) Cross-National Data-Set WVS1-7v5.0*. World Values Survey Association. [doi:10.14281/18241.25](https://doi.org/10.14281/18241.25). [Official archive](https://www.worldvaluessurvey.org/WVSDocumentationWVL.jsp).

**Used:** Ukraine 1996, 2006, 2011 and 2020, from the standalone WVS time-series SPSS v5.0 file. This citation matches the acquired release, rather than the earlier v3.0 time series.

**Method:** Adults aged 18+, weighted by `S017`. Numeric items use valid responses and harmonised scale directions; categorical charts retain nonresponse in the denominator. The 95% intervals use weighted respondent-level linearisation and are approximate because verified sampling-cluster identifiers are unavailable. [Core crosswalk](question_crosswalk.csv); [additional questions](extended_question_definitions.csv).

## European Values Study (EVS)

EVS (2022). *EVS Trend File 1981–2017*. GESIS Data Archive, Cologne. ZA7503, version 3.0.0. [doi:10.4232/1.14021](https://doi.org/10.4232/1.14021).

**Used:** Ukraine 1999, 2008 and 2020. The final observation was fielded in 2020 despite “2017” in the trend-file title.

**Method:** Adults aged 18+, weighted by `S017`, with the same numeric and categorical rules as WVS and approximate respondent-level intervals. EVS and WVS remain distinct series so their estimates can be compared without double-counting respondents from integrated files. [Core crosswalk](question_crosswalk.csv); [additional questions](extended_question_definitions.csv).

## Life in Transition Survey (LiTS)

European Bank for Reconstruction and Development and World Bank. *Life in Transition Survey*: round I (2006), round II (2010), and round III (2016), original survey datasets. [Official data archive](https://www.ebrd.com/home/what-we-do/office-of-the-chief-economist/lits/life-in-transition-survey-data.html).

**Used:** Ukrainian samples in `LITS-2006-data.dta`, `lits2.dta` and `lits_iii.dta`.

**Method:** Adults aged 18+, using `weight_0`, `weight` and `weight_population`, respectively. Market, planned-economy and indifferent responses are separate nominal categories. Main estimates use substantive answers; separate exports include nonresponse. Approximate intervals account for primary sampling units, without unavailable strata. LiTS contributes to the project tables but not the HTML trends, because its last Ukrainian observation is 2016. [Crosswalk](question_crosswalk.csv).

## Pew Research Center

The project uses published Ukrainian tables and historical comparisons from these releases:

- Pew Research Center (2009). *Pew Global Attitudes Project: August–September 2009 Survey, Topline Results*. [Topline PDF](https://www.pewresearch.org/global/wp-content/uploads/sites/2/2009/11/Pew-Research-Center_TOPLINE-Two-Decades-After-the-Walls-Fall-End-of-Communism-Cheered-But-Now-With-More-Reservations_2009.pdf).
- Pew Research Center (2011). *Pew Global Attitudes Project: 2011 Spring Survey Topline Results*, December 5 release. [Topline PDF](https://www.pewresearch.org/wp-content/uploads/sites/2/2011/12/Pew-Global-Attitudes-Former-Soviet-Union-Report-Topline.pdf).
- Pew Research Center (2014). *Faith and Skepticism about Trade, Foreign Investment*, September 16. [Report and tables](https://www.pewresearch.org/wp-content/uploads/sites/2/2014/09/Pew-Research-Center-Trade-Report-FINAL-September-16-2014.pdf).
- Pew Research Center (2014). *Emerging and Developing Economies Much More Optimistic than Rich Countries about the Future*, October. [Report and tables](https://www.pewresearch.org/wp-content/uploads/sites/2/2014/10/Pew-Research-Center-Inequality-Report-FINAL-October-17-2014.pdf).
- Pew Research Center (2017). *Religious Belief and National Belonging in Central and Eastern Europe*, May 10. [Report](https://www.pewresearch.org/wp-content/uploads/sites/20/2017/05/CEUP-FULL-REPORT.pdf); [topline](https://assets.pewresearch.org/wp-content/uploads/sites/11/2017/05/09154356/Central-and-Eastern-Europe-Topline_FINAL-FOR-PUBLICATION.pdf). Ukrainian fieldwork was in **2015**.
- Pew Research Center (2019). *European Public Opinion Three Decades After the Fall of Communism*, October 15. [Report](https://www.pewresearch.org/global/wp-content/uploads/sites/2/2019/10/Pew-Research-Center-Value-of-Europe-report-FINAL-UPDATED.pdf); [topline](https://www.pewresearch.org/global/wp-content/uploads/sites/2/2019/10/Pew-Research-Center-Value-of-Europe-Topline-for-Release-FINAL.pdf); [methodology](https://www.pewresearch.org/global/2019/10/15/methodology-43/).

**Method:** Published percentages are transcribed with their original denominators, rounding and nonresponse. Historical points quoted in later releases retain their original survey years. No confidence intervals are reconstructed from rounded percentages. The 1991 transition question concerned efforts to establish a market economy; later questions evaluate the transition retrospectively. [Question crosswalk](pew_question_crosswalk.csv); [published source-cell trace](../output/tables/extended_published_trace.csv).

## Ukrainian Society Monitoring

Institute of Sociology, National Academy of Sciences of Ukraine. *Українське суспільство* [*Ukrainian Society*], sociological monitoring series, annual volumes and statistical appendices. [Official publication catalogue](https://isnasu.org.ua/publish/ukrainske-suspilstvo/issues.php).

The acquired volumes and supplementary historical compilations are individually identified, with direct links, in the [source register](monitoring_sources.csv). Important recent sources include:

- Institute of Sociology, NAS of Ukraine (2020). *Українське суспільство: моніторинг соціальних змін* [*Ukrainian Society: Monitoring Social Changes*]. [Volume](https://isnasu.org.ua/assets/files/monitoring/mon2020.pdf).
- Institute of Sociology, NAS of Ukraine (2021). Statistical appendix to the monitoring series. [Tables](https://isnasu.org.ua/assets/files/monitoring/monitoring-2021dlya-tipografii.pdf).
- Institute of Sociology, NAS of Ukraine (2023). *Українське суспільство в умовах війни. Рік 2023* [*Ukrainian Society in Wartime. Year 2023*]. [Volume](https://isnasu.org.ua/assets/files/monitoring/Maket_Ukr_suspilstvo_2023.pdf).
- Institute of Sociology, NAS of Ukraine (2024). *Українське суспільство в умовах війни. Рік 2024* [*Ukrainian Society in Wartime. Year 2024*]. [Volume linked by the Institute](https://drive.google.com/file/d/1bqw3rZ3ajsNJ2l7zBQL5uRjAWO030EYk/view).
- Institute of Sociology, NAS of Ukraine (2025). *Українське суспільство в умовах війни. Рік 2025: Колективна монографія* [*Ukrainian Society in Wartime. Year 2025: Collective Monograph*]. [Volume linked by the Institute](https://drive.google.com/file/d/1CeJIiK0ZLNJ0aHyPbXHrWO21ykIB6m7W/view).

**Method:** Published national response percentages, covering selected questions and years from 1992 to 2025. Original categories, missing responses and rounding are retained. Wording changes are documented; questions about privatisation, existing ownership and renationalisation are separate measures. No intervals are estimated without respondent data or published item-specific uncertainty. [Crosswalk](monitoring_question_crosswalk.csv); [table locations](monitoring_table_locations.csv); [extraction trace](../output/tables/monitoring_analysis_trace.csv).

## European Social Survey (ESS)

European Social Survey / ESS ERIC. *European Social Survey integrated data*, the editions below. ESS Data Archive, Sikt. [Data portal](https://www.europeansocialsurvey.org/data-portal).

| Round | Edition used | Ukrainian fieldwork | Dataset DOI |
|---|---|---|---|
| 2 | 3.6 | 2005 | [10.21338/ess2e03_6](https://doi.org/10.21338/ess2e03_6) |
| 3 | 3.7 | 2006–07 | [10.21338/ess3e03_7](https://doi.org/10.21338/ess3e03_7) |
| 4 | 4.6 | 2009 | [10.21338/ess4e04_6](https://doi.org/10.21338/ess4e04_6) |
| 5 | 3.6 | 2011 | [10.21338/ess5e03_6](https://doi.org/10.21338/ess5e03_6) |
| 6 | 2.7 | 2013 | [10.21338/ess6e02_7](https://doi.org/10.21338/ess6e02_7) |
| 11 | 4.2 | 2024 | [10.21338/ess11e04_2](https://doi.org/10.21338/ess11e04_2) |

Ukrainian national ESS team. *Ukrainian European Social Survey 2022*, separate ESS10-related study, `ESS10UAe4.sav`, edition 4. Coordinated by Tymofii Brik (Kyiv School of Economics) and Andrii Gorbachyk (Taras Shevchenko National University of Kyiv); fieldwork by KIIS, 18 January–8 February 2022. [Dataset and study documentation, KSE Sociological Center](https://github.com/KSE-Sociological-Center/ESS10_Ukraine).

**Method:** Adults aged 18+, using supplied `pspwght` weights, which incorporate design weights. ESS 2022 and 2024 intervals use strata and primary sampling units; earlier intervals use approximate respondent-level linearisation. Numeric responses use valid ratings; categorical charts include nonresponse. Round 3 interviews span December 2006–January 2007 and are plotted at 2007, labelled 2006–07. [Question crosswalk](ess_question_crosswalk.csv); [sample audit](../output/tables/ess_sample_audit.csv).

## International Social Survey Programme (ISSP)

- ISSP Research Group (2018). *International Social Survey Programme: Religion III – ISSP 2008*. GESIS Data Archive, Cologne. ZA4950, version 2.3.0. [doi:10.4232/1.13161](https://doi.org/10.4232/1.13161).
- ISSP Research Group (2017). *International Social Survey Programme: Social Inequality IV – ISSP 2009*. GESIS Data Archive, Cologne. ZA5400, version 4.0.0. [doi:10.4232/1.12777](https://doi.org/10.4232/1.12777).
- Oksamytna, Svitlana, and Ivashchenko, Olga (2022). *International Social Survey Programme: Social Inequality V – ISSP 2019 (Ukraine)*. GESIS Data Archive, Cologne. ZA7810, version 1.0.0. [doi:10.4232/1.13853](https://doi.org/10.4232/1.13853).

**Method:** Ukrainian adults aged 18+, weighted by the supplied `WEIGHT`. The 2008 module contributes business-confidence measurement; the 2009 and 2019 modules provide the comparable HTML series. Intervals are approximate because sampling identifiers are unavailable. Categorical shares include nonresponse; monetary means use valid amounts and are monthly after-tax UAH at current prices. The Ukrainian tax question asks about higher taxes without explicitly specifying a share of income. [Question crosswalk](issp_question_crosswalk.csv); [sample audit](../output/tables/issp_sample_audit.csv); [published-table checks](../output/tables/issp_published_checks.csv).

## Comparability

### Question wording

The [chart wording audit](chart_wording_audit.csv), checked on 29 September 2026, covers every question and displayed response group in the 95-chart HTML gallery. Charts use labelled English summaries; an expandable panel preserves complete alternatives, grouping rules, source references and differences across waves. Correcting a display label does not change its raw-code membership or its estimate.

The audit uses WVS English master questionnaires for each included wave; the EVS ZA7503 codebook and Ukrainian national questionnaires for [1999](https://access.gesis.org/dbk/9793), [2008](https://access.gesis.org/dbk/18074) and [2020](https://access.gesis.org/dbk/70790); Pew's original toplines; the Ukrainian Monitoring tables; ESS supplied English codebooks and the Ukrainian Round 10 questionnaire; and ISSP's Ukrainian national questionnaires for 2009 and 2019. Other national-language versions have not all been independently verified.

For WVS 2020, the [Ukrainian national report](https://ucep.org.ua/wp-content/uploads/2020/11/WVS_UA_2020_report_WEB.pdf), Table 7.1, PDF pp. 83–84 (printed pp. 82–83), supplies local wording for the economic scales. Its income-incentive endpoint explicitly refers to higher income for greater individual effort; the English WVS7 master omits that explicit income reference. The Ukrainian EVS questionnaires say “Той, хто більше працює, повинен отримувати більше”, against an endpoint saying income differences should not be very large. The audit preserves the local text rather than substituting the English master's abstract “greater incentives” wording. EVS 2020 also shortens the competition endpoints to good/harmful, omitting the explanations included in 1999/2008. These wave differences appear in the chart's wording panel. Pew's 1991 question asks about efforts to establish a free market; later waves ask retrospectively about the transition, so the 1991 point is not joined to the later line. Pew also changes “people who own businesses” in 2009/2011 to “business people” in 2019.

Survey estimates can be compared across programmes where question wording, response scales and populations match. The gallery keeps survey identity visible, connects actual observations and does not interpolate annual estimates. Different respondents are sampled in each wave; age-group comparisons describe those groups at each date.

Territorial coverage changes are the main population-comparability limitation. WVS 2020, EVS 2020, later Pew and ISSP releases exclude occupied territories to varying degrees; wartime ESS and Monitoring observations cover accessible populations and are also affected by displacement. The [WVS Ukraine 2020 report](https://ucep.org.ua/wp-content/uploads/2020/11/WVS_UA_2020_report_ENG_WEB.pdf) documents this issue. Geographic sensitivity estimates exclude Crimea/Sevastopol and Donetsk/Luhansk consistently where verified identifiers permit; published Pew and Monitoring margins cannot be reweighted this way. Crosswalks record wave-specific coverage and unresolved gaps.

Numeric charts show weighted means and available 95% confidence intervals. Ordered categories combine positive and negative responses while keeping middle, undecided and missing categories separate; nominal questions show every option. Open monetary answers are not adjusted for inflation. Published percentages may not total exactly 100% because of rounding. Wide intervals indicate that an estimate is less precise; approximate intervals may understate uncertainty when full survey-design information is missing.
