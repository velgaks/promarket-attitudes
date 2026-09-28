# Market attitudes in Ukraine

How have Ukrainians’ attitudes toward markets and the state's economic role changed? This project combines WVS, EVS, LiTS, Pew, Ukrainian Society Monitoring, ESS and ISSP. The core historical comparison ends in 2020; explicitly dated extensions cover ESS through 2024 and Monitoring through 2025.

**[Explore 95 interactive question charts](https://velgaks.github.io/promarket-attitudes/)** · **[Read the research note (PDF)](output/pdf/ukraine_market_attitudes.pdf)** · **[Read the note in Markdown](output/ukraine_market_attitudes.md)**

The gallery shows numeric means with 95% confidence intervals, grouped ordinal responses and all nominal options, with PNG/SVG/CSV downloads. It includes questions with at least two observations and a latest observation from 2019 onward. The opening inventory covers 294 indicators across seven survey programmes; the appendix provides 284 latest affirmative-response shares and a separate table for ten open monetary questions.

This repository publishes analysis code, question crosswalks, source manifests and aggregate results. **Respondent microdata, downloaded source PDFs, local archives and temporary files are not included.** Reproducing the analysis requires acquiring the original survey releases through their respective archives. The results can be read without downloading microdata.

Descriptive repeated-cross-section research using WVS, EVS and EBRD LiTS. Four component means are accompanied by a fixed, equally weighted 0–100 descriptive index in WVS and EVS. LiTS uses a separate binary market-preference indicator on a 0–100 scale; its three categories are never averaged ordinally. Education effects and causal explanations are outside scope.

## Current implementation

The original ten Ukrainian microdata waves have been acquired and analysed: WVS 1996/2006/2011/2020, EVS 1999/2008/2020 and LiTS 2006/2010/2016. Pew adds published national results for 1991/2009/2011/2019 and published 2019 age groups. Institute of Sociology Monitoring adds 20 question series, covering 30 observed years from 1992 to 2025. The main cross-survey analysis ends in 2020; later Monitoring waves and ESS through 2024 form separate extensions. ISSP adds Ukraine’s 2008, 2009 and 2019 releases, including 36 recent question trends. The report contains an opening coverage inventory, the expanded analysis and the latest-response appendix at `output/pdf/ukraine_market_attitudes.pdf`, with Markdown at `output/ukraine_market_attitudes.md`. `output/tables/delivery_status.json` distinguishes microdata from published aggregates and records numerical and visual checks. Unverified survey files cannot pass the source-hash and item-crosswalk gate.

## Run

Python 3.12 was used. From the project directory:

```powershell
python -m pip install -r requirements.txt
python scripts/run.py
```

Use `--no-note` to regenerate only data tables and figures. Every stage stops on errors. The exact tested dependency versions are pinned in `requirements-lock.txt`. No R, SPSS or proprietary analysis software is required. A changed PDF requires a fresh visual review; the delivery record checks the reviewed PDF's hash.

## Files and outputs

- The note opens with a question-by-survey coverage table listing all verified years, generated directly from the result tables. Related battery subitems share a display row only when their years match. `output/tables/question_year_inventory.csv` retains every individual indicator; `question_year_inventory_compact.csv` reproduces the opening table.
- `data/raw/`: original microdata, unchanged; excluded from version control.
- `data/source_manifests/`: URLs, release versions, SHA-256 hashes and acquisition records; no registration details or credentials.
- `data/processed/ukraine_harmonised.csv`: local respondent-level analytical extract, not for redistribution.
- `docs/question_crosswalk.csv`: question identities, endpoint descriptions, coding, missingness, weights, geographic variables, evidence and comparability decisions.
- `docs/survey_inventory.csv`: actual Ukrainian fieldwork years and survey identity.
- `docs/index_definitions.csv`: index formula, missing-response rule and interpretation for every survey-wave.
- `output/tables/`: weighted and unweighted estimates; approximate 95% confidence intervals; full response distributions; missingness; geographic sensitivity; audit and external-check results.
- `output/figures/`: 300 dpi PNGs and editable SVGs, with approximate 95% confidence intervals for microdata estimates and published point estimates for Monitoring; no annual interpolation. `figure_manifest.json` lists current exports, excluding superseded distribution charts.
- `output/pdf/`: final note PDF after publication checks.

## Acquisition

1. **LiTS:** use the [official EBRD data archive](https://www.ebrd.com/home/what-we-do/office-of-the-chief-economist/lits/life-in-transition-survey-data.html). The exact original `.dta` links and checksums are in their manifests. Save as `LITS-2006-data.dta`, `lits2.dta` and `lits_iii.dta` in `data/raw/`. `python scripts/acquire.py URL data/raw/FILE.dta` downloads and records public sources. It validates file signatures, verifies TLS and preserves acquisition dates on reruns.
2. **EVS:** register/sign in at [GESIS ZA7503](https://search.gesis.org/research_data/ZA7503), EVS Trend File 1981–2017, version 3.0.0, DOI [10.4232/1.14021](https://doi.org/10.4232/1.14021). Despite the programme-wave title, Ukraine's latest fieldwork is 2020. The user supplied `ZA7503_v3-0-0.sav.zip`; its original `.sav` is retained in `data/raw/`.
3. **WVS:** complete the registration on the [official longitudinal archive](https://www.worldvaluessurvey.org/WVSDocumentationWVL.jsp) and download the WVS-only TimeSeries 1981–2022 SPSS v5.0 file (DOID 11933). The user supplied `F00011933-WVS_Time_Series_1981-2022_spss_v5_0.zip`. Keep the original zip and extract `WVS_Time_Series_1981-2022_spss_v5_0.sav` into `data/raw/`. Do not use the EVS/WVS joint file alongside these standalone files. SPSS user-missing codes are preserved.

Automated WVS transfers returned empty responses; the user's registered manual download resolved acquisition. Official WVS master questionnaires were obtained through IHSN mirrors for waves 3, 5 and 6 and directly from WVS for wave 7; their manifests record URLs and hashes. No later Ukrainian microdata release was verified during the archive check. [LiTS IV coverage notes](https://www.ebrd.com/content/dam/ebrd_dxp/assets/pdfs/office-of-the-chief-economist/publications/life-in-transition-survey-iv/Life-in-Transition-IV-2024-Notes-Abbreviations-English.pdf) explicitly exclude Ukraine from 2022–23.

WVS data terms require non-profit use, proper citations, sending publication citations to the association and no redistribution of raw data. GESIS and EBRD source terms also apply. This project does not publish microdata or send messages to source organisations.

## Estimands and inference

Keep Ukrainian adults 18+ with positive finite person weights. WVS and EVS use their national weights (`S017`); equal-country weights are inappropriate for this country study. LiTS uses `weight_0` (2006), `weight` (2010) and `weight_population` (2016). Weights are not trimmed further. The unweighted comparison retains the same eligible records.

For a response outcome y and domain D, the point estimate is `sum(w*D*y)/sum(w*D)`, over nonmissing y. For LiTS, a category's share is the mean of its binary indicator among valid answers. An additional distribution includes nonresponse explicitly in the denominator. Ten-point items retain all ten categories. Negative missing codes are not scores. Their identities and frequencies are exported.

For LiTS, the linearized ratio contribution is `w*D*(y-mean)/sum(w*D)`. Sum by PSU and use `G/(G-1) * sum(PSU_total^2)` for variance. All eligible-sample PSUs, including those with zero contribution to an age/geographic domain, remain in the variance calculation. Use t critical values with `G-1` degrees of freedom and bound intervals by the scale. Explicit strata/replicate weights were not identified; no strata are guessed from regions. These intervals are approximate.

WVS/EVS trend files do not supply verified sampling-cluster variables in the fields used here. Their intervals use weighted respondent-level linearization and are explicitly approximate; clustering could widen them. Interviewer IDs and country-wave IDs are not treated as sampling clusters. Uneven 2020 EVS weights greatly reduce its Kish effective sample size; it is reported as a weight-dispersion diagnostic, not as a full design-adjusted sample size.

Intervals reflect sampling approximation, not coverage error or missing-response bias. No causal tests, age-period-cohort decomposition, or formal independent-wave tests of changes are reported. LiTS revisits some localities, so independence of wave-level sampling errors is not assumed for change tests.

## Descriptive pro-market indices

For WVS and EVS, let the four aligned responses (ownership, competition, individual responsibility, income incentives) be x1,...,x4, each between 1 and 10. A respondent's index is `100/9 * (mean(x1,...,x4) - 1)`. It requires all four valid responses. Fixed endpoints and equal item weights are preserved across every wave: no within-wave z scores, fitted factor weights, or partial-item means. Survey weights enter the population mean, not the definition of a person's score. Standard errors are calculated from respondent scores, retaining covariance among the four items.

The main index sample is complete cases, so its composition can differ from each component's item-valid sample. `index_diagnostics.csv` reports weighted exclusion shares and an alternative constructed from the four item-specific national means. `index_leave_one_out.csv` removes each component in turn while holding the four-item complete-case sample fixed. `index_item_correlations.csv` and weighted Cronbach's alpha document the limited alignment of the items. Alpha uses the weighted covariance matrix C: `4/3 * (1 - trace(C)/sum(C))`; no reliability threshold is used to select waves or items. The composite is a descriptive aggregation, not a validated common latent attitude scale.

For LiTS, market preferable scores 100, planned sometimes preferable and indifferent score 0, and missing answers remain missing. This measures explicit market preference; zero does not mean identical opposition among planned and indifferent respondents. Its weighted mean and uncertainty interval equal the market-preference share and interval multiplied by 100. Do not interpret LiTS levels as equivalent to WVS/EVS composite levels.

Index national/age-group estimates, weighted/unweighted checks and geographic domains are included in the standard tables and `index_results.csv`. `index_checks.py` verifies endpoint anchoring, complete-case behavior, the mean-of-components identity and exact LiTS rescaling including standard errors and confidence intervals.

## Pew published-data supplement

`scripts/pew_supplement.py` extracts Ukraine's Q16a rows from the [2019 topline](https://www.pewresearch.org/global/wp-content/uploads/sites/2/2019/10/Pew-Research-Center-Value-of-Europe-Topline-for-Release-FINAL.pdf), PDF page 35 / printed page 150. It adds the two rounded approval categories and checks their totals against published nets: 52% (1991), 36% (2009), 34% (2011), 47% (2019). The 2019 report's chart on printed page 22 verifies 1991/2009/2019; the [2011 economic-changes chapter](https://www.pewresearch.org/global/2011/12/05/chapter-2-views-of-economic-changes-and-national-conditions/) verifies 2011. Nonresponses remain in the denominator. These are published weighted percentages, not estimates from local respondent data.

`docs/pew_published_age_values.csv` is a visually audited transcription of the Ukraine age row in the [2019 report](https://www.pewresearch.org/global/wp-content/uploads/sites/2/2019/10/Pew-Research-Center-Value-of-Europe-report-FINAL-UPDATED.pdf), PDF page 24 / printed page 23. Its original groups are 18–34, 35–59 and 60+, and are kept under those labels. `docs/pew_question_crosswalk.csv` documents wording, coding, coverage and comparability; `output/tables/pew_published_results.csv` and `pew_validation.json` record the generated supplement. Fixed source hashes reject changed PDFs pending review. Missing public PDFs are acquired automatically using their recorded URLs. Source PDFs are excluded from the package, while code, transcriptions, aggregates and manifests are included.

The 1991 question concerns efforts to establish a market economy; 2009/2011/2019 assess the transition retrospectively. The former is an earlier benchmark, not an unchanged-wording observation. [Pew's methodology](https://www.pewresearch.org/global/2019/10/15/methodology-43/) defines Ukrainian samples as 18+ and notes that coverage from 2015 excludes Crimea and conflict areas in Donetsk/Luhansk, which earlier surveys included. This supplement does not reproduce geographic exclusions from microdata. Item-specific confidence intervals are unavailable in the published tables and are left missing; no binomial intervals are inferred from rounded percentages or headline sample sizes.

Pew respondent files were not acquired. The [Spring 2019](https://www.pewresearch.org/dataset/spring-2019-survey-data/) and [Fall 2009](https://www.pewresearch.org/dataset/fall-2009-survey-data/) download pages require a Pew account. Their microdata would allow the study's exact age bands and confidence intervals to be calculated. Published age-group comparisons already provide additional evidence in the note without relabelling incompatible bands.

## Institute of Sociology monitoring analysis

The integrated monitoring supplement is documented in [output/monitoring_inventory.md](output/monitoring_inventory.md). It contains 29 public source PDFs, 188 verified question–year observations across 20 market/ownership-related questions, and 964 extracted response percentages. The archive includes the 1994–2005 Panina tables, annual volumes and appendices, the original 2014 frequency tables, and releases through 2025. Exact years vary by question; the coverage grid distinguishes explicit table dashes from observations not located.

`run.py` runs extraction, inventory, indicator analysis, charts and the note. Missing PDFs are downloaded from the recorded source register, with hashes checked against the archived versions. To update the acquisition inventory intentionally, run `python scripts/monitoring_acquire.py` separately; review any changed source before re-estimation. Published all-respondent percentages retain nonresponses. Original privatisation questions, retrospective assessments, existing private ownership and renationalisation stay separate. The 2020 land-ownership figure sometimes appended to the old privatisation series belongs to a different question.

`monitoring_analysis.py` generates 253 estimates for 27 indicators from all 20 question series. `monitoring_estimates.csv` gives each observed year; `monitoring_analysis_trace.csv` records every contributing source percentage and coefficient, with source file, page and URL. `docs/monitoring_indicator_definitions.csv` records response selection, fixed denominators and coding direction. Approval combines the two positive categories where present; opposition to renationalisation combines no and rather no. The three state-role options retain distinct meanings. No-answer and undecided categories are never silently excluded from the denominator.

The **Monitoring privatisation support index** is `(positive_small + positive_large + positive_land) / 3`, on a 0–100 scale, for the 21 waves where all three original questions are present. It summarises expressed endorsement across sectors. Every other answer, including no answer, contributes zero to expressed support; zero does not mean opposition. This aggregate score uses the same three questions and fixed weights across waves, and is not a respondent complete-case or broad pro-market index. Its mean is identifiable from marginal percentages; its respondent variance and confidence interval are not. It is not numerically interchangeable with the WVS/EVS indices. The 2020 existing-ownership module is never substituted into this index.

The note adds the contrast between private business and privatisation, the preference for a mixed economy, acceptance of existing ownership, and a separately dated 2021–2025 extension. Five exportable Monitoring charts cover these series and the index. Full national and age-by-dimension charts for the original surveys remain exported. Item-specific confidence intervals are left missing for Monitoring. Published age-index inconsistencies and incompatible age bands prevent adding its age estimates; the inventory records their locations. The crosswalk, source register, cell audit, estimates and validation results are in the reproducibility package; source PDFs remain local.

## Expanded questionnaire audit and latest-share appendix (September 2026)

The additional appendix has **188 indicators or named response options**, with a question-specific latest year: WVS 26, EVS 20, LiTS 47, Pew 28 and Monitoring 67. These are not 188 independent questions: categorical questions can supply several explicitly labelled options. The main research note remains seven pages; the comprehensive table follows it. See [the audit](output/variable_audit.md) for additions, exclusions and the limits of archive coverage.

`extended_attitudes.py` reads the original microdata and produces all available verified question-wave affirmative shares, weighted/unweighted estimates, missingness and approximate intervals. `extended_published.py` extracts additional Pew/Monitoring cells from the source PDFs, retaining page, question, URL and hash. It reacquires missing public PDFs using the packaged manifests. `latest_appendix.py` combines these with the original results, selects the latest year **for each question**, and checks the source-cell arithmetic. `variable_audit.py` documents availability and scans all 29 acquired Monitoring PDFs. All four stages run through `run.py`.

The requested table is [latest_positive_shares_compact.csv](output/tables/latest_positive_shares_compact.csv). The [detailed CSV](output/tables/latest_positive_shares.csv) adds response coding, uncertainty, denominators and provenance. “Affirmative” endorses the named response, including pro-state statements; it is not a uniform pro-market coding. For microdata, shares use valid substantive answers and the original survey weights; checkbox items use all recorded 0/1 answers. For public tables, shares retain all respondents. Ten-point bipolar items count the five categories on the named side, while all mean charts retain the continuous scores. Existing indices keep their original content.

Pew additions use its 2009, 2011, 2014 trade/inequality, 2015 CEE and 2019 toplines. CEE Ukrainian interviews took place on 3–29 July **2015**, although the report was published in 2017, and exclude Crimea and all of Donetsk/Luhansk. The CEE published free-market net is 47%; summing its rounded agreement categories gives 48%, so the published net is used. Its general-population rows are kept distinct from religious subgroup rows. Monitoring additions cover ownership structure, entrepreneurship, business values and duties, crisis policy, tax/benefit norms, class conflict and economic-institution trust.

All time-series charts now use **lines connecting actual observations**, retain gaps on the calendar axis and show approximate 95% intervals where microdata permit. No annual data are interpolated. Fifteen PNG/SVG chart pairs are exported, including new LiTS three-dimension means and Pew market trends. The QA stages check all appendix numbers against generated tables. The audit and all new source manifests are included in the reproducibility package.

## Market principles and ideological coherence

The new section answers which principles attract support and whether the same respondents favour them together. `scripts/market_coherence.py` runs before chart/report generation. Its latest-wave ranking keeps WVS 2020, EVS 2020 and LiTS 2016 separate and uses the existing market-oriented halves of the ten-point scales and their original design intervals. The other survey examples retain their own question wording and year.

Within-wave weighted Pearson correlations use complete cases for the named battery: four fixed WVS/EVS policy items, or three comparable LiTS scales in 2010/2016. No survey waves are pooled. A separate common-three battery in WVS/EVS removes individual responsibility for comparisons with LiTS. The extended LiTS battery adds binary market preference and reverse-coded agreement that the rich-poor gap should be reduced. These associations are distinct from the unchanged published indices. Trust, concepts of democracy and mechanically competing categorical choices do not receive an assumed ideological polarity.

Uncertainty uses 2,000 nonparametric bootstrap draws (seed 20260925), resampling eligible respondents in WVS/EVS and PSUs in LiTS. Original weights are held fixed; complete-case deletion is applied within each draw. PSUs with no complete cases remain in the sampling frame. Percentile 95% intervals are approximate without full design/strata information. Bootstrap replicates use weighted first and second moments aggregated at PSU level. The outputs also provide weighted Spearman correlations based on weighted empirical midranks, unweighted and pairwise-complete sensitivity, raw and standardized Cronbach alpha, and the first principal component's variance share and signed loadings. No arbitrary coherence/reliability cutoff is applied. Low average association describes the selected positions, not an individual's rationality or political identity.

- `output/tables/market_principle_rankings.csv`: latest-wave affirmative shares and original confidence intervals, plus continuous means, intervals and alternative mean rankings. EVS 2020 puts income incentives ahead of competition by mean score, while competition leads by affirmative share; both results are reported.
- `output/tables/attitude_correlations.csv`: 92 within-battery pair estimates, bootstrap intervals, sample counts and sensitivity checks.
- `output/tables/ideological_coherence.csv`: 21 battery-wave summaries, including mean correlations, alpha and first-component variance, with uncertainty.
- `output/tables/coherence_pc_loadings.csv`: signed first-component loadings.
- `output/tables/market_supporter_attitudes.csv`: LiTS attitudes among respondents explicitly preferring a market economy, with item-valid denominators and PSU-linearized intervals.
- `docs/coherence_question_definitions.csv`: original LiTS fields, labels, weights and polarity; WVS/EVS use the existing four-item crosswalk.

The pipeline reproduces the previously validated WVS/EVS item correlations and alpha, checks covariance/correlation identities and weight invariance, and traces every new reported estimate to its output table. Eighteen PNG/SVG pairs are now exported; the three additions show latest principle rankings, correlation matrices and over-time mean correlations. The note adds two findings pages and one methods page. Pew/Monitoring published marginal tables cannot identify within-person correlations.

## Individual question trend exports

Run `python scripts/question_trend_data.py` and `python scripts/question_trends.py` to regenerate the [HTML gallery](output/question_trends/index.html) and the local chart ZIP. The full pipeline also runs both stages.

The gallery has **59 complete questions** from WVS, EVS, Pew, Monitoring and ESS, each with at least two observations and a latest year of 2019 or later. All **21 numeric rating scales use means with 95% confidence intervals** (approximate where design identifiers are unavailable). Verbal ordinal scales pool positive and negative categories, retaining neutral, undecided and other answers; nominal questions show every option together. State-role and ownership-policy options now share their original questions instead of appearing as seven separate graphs. The other **38 charts** show complete categorical responses. Categorical microdata percentages now include all adults and show missing answers, rather than using the former valid-answer denominator.

Tax/benefit-justifiability means are reversed so higher values indicate stronger rejection; democracy-characteristic means exclude spontaneous nonnumeric “against democracy” responses (source code 0), whose weighted share is exported. An option introduced only in a later wave is absent before introduction, never zero. Published percentages retain their original rounding and do not have fabricated confidence intervals. No eligible multiple-answer question meets both selection rules: repeated crisis-policy choices end in 2017 and business responsibilities have only 2019. Battery subquestions remain separate.

Each question has a 300-dpi PNG, editable SVG and CSV; the HTML is self-contained and supports search, survey/type filters and downloads. `question_trend_definitions.csv` documents all response mappings; `question_trend_source_cells.csv` traces published categories. `question_trend_selection.csv` maps all 294 audited indicators into included/excluded complete questions. Existing numeric means are reproduced, categorical shares sum to 100 within source rounding, and every source option is assigned exactly once. The export package contains no respondent-level data. Obsolete option-only chart files are archived under `archive/cleanup-2026-09-28/temporary_files/question_trend_superseded/`.

## Geographic comparisons

Remove Crimea/Sevastopol and all of Donetsk/Luhansk consistently when verified geographic identifiers permit it. The remaining sample defines a geographic domain; keep the original weights and do not claim that recalibration has removed displacement or migration changes.

- EVS 1999: `X048_EVS`, country-specific numeric labels.
- WVS 1996: `X048WVS`. The ISO region field has inconsistent mappings, including Donetsk assigned to Vinnytsia, and is not used. No separate Sevastopol category is observed.
- WVS 2011/2020: `X048ISO`; explicitly match Crimea's `Krym` label. The 2020 survey excludes occupied areas; the sensitivity domain additionally removes the entire Donetsk/Luhansk oblasts.
- WVS 2006: four broad regions only; geographic sensitivity unavailable.
- EVS 2008: `x048b_n2`, labels distinguish city and oblast codes.
- EVS 2020: `X048I_N2`, a different NUTS-style coding scheme. Never apply 2008 codes to 2020.
- LiTS 2010/2016: verified region names. No observations from Crimea/Donetsk/Luhansk occur in 2016.
- LiTS 2006: numeric regions have no verified oblast mapping in the acquired materials, so geographic sensitivity is withheld.

## SPSS compatibility workaround

The unaltered GESIS SAV is rejected by pyreadstat 1.3.4 because of an invalid optional multiple-response-set dictionary extension. `readable_sav()` in `scripts/analyze.py` makes a temporary copy that omits only that metadata record (byte offset 5,311,744; total length 2,320 bytes). It preserves the entire case-data byte stream, variable definitions and value labels. Latin-1 decoding accommodates mixed legacy metadata; the analytical fields are numeric. Source-hash and dictionary-location checks reject unexpected versions. The original SAV is never edited. A `.dta` acquisition could remove the need for this workaround after a separate source audit.

## Reproducibility checks

The pipeline verifies study identity, Ukrainian fieldwork years, unique IDs, duplicate flags where available, eligible ages, positive weights, response ranges and complete distributions. It checks invariance to rescaling weights and agreement with the ordinary mean variance under equal independent weights. It reproduces the EBRD 2016 Ukraine profile's rounded 37% market-preference and 27% indifference shares using substantive-response denominators. Every manuscript estimate is selected from generated tables and logged to `note_number_trace.csv`.

At the user's explicit request, mean/share plots show approximate 95% confidence intervals, overriding the house-style default. The ten-category and stacked distribution charts have been removed from the current note and package; category tables remain for audit. Small display offsets separate groups within the same labelled fieldwork year; they do not represent different dates. Age bands are 18–34, 35–54 and 55+.

The WVS 2020 income-incentive mean of 6.16 and three rounded grouped shares reproduce the published report. Two responsibility shares differ by about 0.1 percentage point; both values and the unresolved differences are retained in `published_crosschecks.csv`. WVS wave 7 shortens competition endpoint wording. Translated country questionnaires were not all independently verified. Within-programme comparisons retain the shared constructs with these qualifications.

## Source citation and interpretation

Inglehart, R., C. Haerpfer, A. Moreno, C. Welzel, K. Kizilova, J. Diez-Medrano, M. Lagos, P. Norris, E. Ponarin and B. Puranen (eds., 2022). *World Values Survey: All Rounds — Country-Pooled Datafile*. Madrid/Vienna: JD Systems Institute/WVSA Secretariat. The archive's recommended longitudinal citation is DOI [10.14281/18241.17](https://doi.org/10.14281/18241.17); the exact acquired file is SPSS v5.0. The archive landing-page narrative still mentions an older version; file identity comes from the download and hash.

EVS (2022). *EVS Trend File 1981–2017*. GESIS Data Archive, Cologne, ZA7503 v3.0.0, DOI [10.4232/1.14021](https://doi.org/10.4232/1.14021). EBRD: *Life in Transition Survey*, rounds I (2006), II (2010), III (2016), original releases identified in manifests.

Core survey choice follows Nye, Litman, Bryukhanov and Polyachenko (2020), [The Universal Link between Higher Education and Pro-Market Values](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3560072). This study asks a descriptive Ukraine-only question and does not estimate education effects. The main conclusions concern attitudes before the full-scale invasion; the explicitly dated Monitoring and ESS extensions cover later observations.


## ESS extension (25 September 2026)

Place the supplied ESS rounds 2–6/11 subset ZIP (including its HTML codebook) and `ESS10UAe4.sav` in `data/raw/ess/`. `scripts/ess_analysis.py` extracts without altering originals, audits the Ukrainian variables and generates weighted adult estimates, all categorical responses, means, age groups, design intervals, sensitivity tables and within-person comparisons. It is included in `scripts/run.py` before the latest-response appendix and chart stages.

Actual fieldwork: 2005, 2006–07 (stored as year 2007), 2009, 2011, 2013, 2022 and 2024. ESS10 is the separate Ukrainian related study; ESS11 is the 2024 integrated-round sample. See `output/ess_variable_audit.md`, `docs/ess_question_crosswalk.csv` and `data/source_manifests/ess.json`. The extension adds 47 questions to the note/appendix and six eligible recent trends to the HTML. ESS numeric scales retain 0–10 means. Categorical shares include nonresponse; 2022/2024 intervals use strata and PSUs, earlier intervals are approximate. No microdata are redistributed.


## ISSP extension (28 September 2026)

Download SPSS archives for ZA4950 v2.3.0 (Religion III 2008), ZA5400 v4.0.0 (Social Inequality IV 2009) and ZA7810 v1.0.0 (Ukraine Social Inequality V 2019) from authenticated GESIS access into `data/raw/issp`. Ukraine 2019 is not in ZA7600. Run `python scripts/acquire_issp_sources.py` to retrieve public documentation and inventory originals, then `python scripts/run.py` to reproduce the complete study. The run includes `issp_analysis.py` and `issp_documentation.py` before the common appendix/chart/note stages.

The ISSP audit covers 851 fields and retains 59 economic attitudes and related beliefs: 95 question-wave observations, 36 eligible HTML trends, 49 latest affirmative rows and 10 monetary questions with means. The full gallery now has 95 charts. `output/issp_variable_audit.md` documents inclusion, exclusions and national-wording corrections; `docs/issp_question_crosswalk.csv` provides codes, scales, missingness and source hashes. `issp_published_checks.csv` reproduces 15 published Ukrainian response counts and rounded percentages across three 2009 codebook tables.

All ISSP estimates use adults 18+ and supplied WEIGHT. Categorical shares retain nonresponse; numeric means use valid answers. Confidence intervals are approximate because released sampling identifiers are unavailable. The 2019 national release flags sampling deviations and excludes occupied territories. Weighted/unweighted and common-territory checks, pairwise attitude correlations and joint endorsement are exported. Earnings means are respondents' estimated or desired pay in nominal monthly UAH after tax, not observed wages or inflation-adjusted attitudes. Raw records are never included in the delivery ZIPs.


## Folder guide

- `output/`: current research note, HTML gallery, charts, aggregate tables and delivery ZIPs.
- `data/raw/`: original survey files and download archives; ESS and ISSP have their own subfolders.
- `data/documentation/` and `data/source_manifests/`: questionnaires, source versions and checksums.
- `scripts/` and `docs/`: reproducible analysis, question crosswalks and verification records.
- `archive/cleanup-2026-09-28/`: recoverable interim outputs, duplicate download, temporary previews and caches. `moves.json` records the original and new locations. This archive is excluded from delivery packages and version control.
- `tmp/`: regenerated automatically when the pipeline needs working files.


## Reproducing from GitHub

1. Install Python 3.12 and the dependencies listed above.
2. Acquire the original survey files using the programme-specific instructions in this README. Keep raw data local in `data/raw/` and its ESS/ISSP subfolders.
3. Acquire the questionnaires and published reports named in `data/source_manifests/`; each manifest records its URL, expected path and checksum. Save them at the recorded local paths. Source PDFs are deliberately not redistributed here. The `acquire.py`, `monitoring_acquire.py` and `acquire_issp_sources.py` helpers support acquisition as documented in their scripts.
4. Run `python scripts/run.py`. The pipeline regenerates aggregate tables, charts, the Markdown/PDF note and local delivery ZIPs. The website itself is the self-contained `output/question_trends/index.html`.

Survey data and third-party materials remain subject to their original owners' terms. Publishing the analysis does not grant permission to redistribute the underlying microdata. The source manifests and research note contain programme-specific citations.

## Citation

Hatsko, Valentyn (2026). *Market attitudes in Ukraine*. Research note, aggregate results and reproducible analysis. https://github.com/velgaks/promarket-attitudes
