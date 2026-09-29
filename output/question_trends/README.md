# Market and state attitudes in Ukraine

95 separate chart sets (PNG, editable SVG and data CSV), drawn from audited national estimates.
Open index.html for the searchable, offline gallery. Download PNG files alongside the HTML.

## Selection

- At least two distinct observed fieldwork years within a survey/question series.
- Latest available observation is **2019 or later**, inclusive.
- All observed years of an eligible series are retained, including those before 2019.
- One chart per complete question **within each survey**. WVS and EVS remain separate; the three state-role options and four ownership-policy options are now grouped into their two original questions.
- The selection audit covers all 294 previously audited indicators. LiTS is excluded because its latest Ukrainian observation is 2016. Composite indices are not individual questions.

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
