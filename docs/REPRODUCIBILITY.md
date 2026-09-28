# Reproducing the analysis

The repository contains Python code, question crosswalks, source manifests, aggregate tables and chart exports. Original microdata and downloaded publications remain local and are not redistributed.

## Acquire the sources

Use the releases listed in [Sources](SOURCES.md). [Source manifests](../data/source_manifests/) record acquisition URLs, filenames, versions and SHA-256 hashes.

- **WVS:** Download the WVS-only Time Series 1981–2022 SPSS v5.0 file from the registered archive. Extract `WVS_Time_Series_1981-2022_spss_v5_0.sav` into `data/raw/` and retain the original ZIP.
- **EVS:** Download ZA7503 v3.0.0 from GESIS; extract its SPSS file into `data/raw/`. Do not substitute an integrated WVS/EVS file, which would duplicate samples.
- **LiTS:** Save the original Stata files as `data/raw/LITS-2006-data.dta`, `data/raw/lits2.dta` and `data/raw/lits_iii.dta`.
- **ESS:** Place the Ukraine SPSS subset and codebook for rounds 2–6 and 11, with its original ZIP, in `data/raw/ess/`. Use the editions in the source citation table. Add the national study’s `ESS10UAe4.sav` to that folder.
- **ISSP:** Download ZA4950 v2.3.0, ZA5400 v4.0.0 and ZA7810 v1.0.0 from GESIS into `data/raw/issp/`, preserving the filenames in the manifests. Supporting questionnaires and codebooks belong in `data/documentation/issp/`.
- **Pew and Monitoring:** Retrieve the exact PDFs recorded in the manifests. Pew files belong in `data/documentation/`; Monitoring volumes in `data/documentation/monitoring/`. The source registers and extraction scripts retain page/table references.

Registered downloads may require accepting the original provider’s terms. All local source paths and checksums are recorded in the manifests; use those records to resolve filenames rather than renaming source files arbitrarily.

## Run

Python 3.12 was used. From the repository root:

```sh
python -m pip install -r requirements.txt
python scripts/run.py --no-note
```

This rebuilds the estimates, checks and charts, including the HTML. Dependency versions are pinned in `requirements-lock.txt`. Omitting `--no-note` also builds the working research note and runs its publication checks; a changed PDF requires a new visual review.

To rebuild only the gallery from existing aggregate tables:

```sh
python scripts/question_trend_data.py
python scripts/question_trends.py
```

## Trace an estimate

1. Find the chart and its downloadable CSV in [the gallery](../output/question_trends/index.html).
2. Use [all_chart_data.csv](../output/question_trends/all_chart_data.csv) and [manifest.json](../output/question_trends/manifest.json) to identify its generated source table and checksum.
3. Consult the [question definitions](question_trend_definitions.csv), programme crosswalks and source manifests for coding, weights and original wording. Published margins have a separate [source-cell trace](../output/tables/question_trend_source_cells.csv).

The [selection audit](../output/question_trends/selection_audit.csv) records included and excluded series. Validation tables check counts, missing responses, valid ranges, weighting, scale direction and agreement between plotted values and source estimates.
