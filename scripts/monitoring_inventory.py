"""Build a readable source inventory and explicit year-by-question coverage grid."""
from pathlib import Path
import json
import pandas as pd
import pymupdf
from acquire import ROOT

LABELS = {
 'private_business':('Approval of developing private business','Five ordered categories from strong disapproval to strong approval; ambivalence in middle.'),
 'privatise_large':('Privatisation of large enterprises','Three categories: negative, ambivalent, positive.'),
 'privatise_small':('Privatisation of small enterprises','Three categories: negative, ambivalent, positive.'),
 'privatise_land':('Privatisation of land','Three categories: negative, ambivalent, positive. Do not append the different 2020 existing-ownership item.'),
 'land_sales_general':('Allow buying and selling land','Yes/no/undecided. General land wording.'),
 'land_sales_agricultural':('Allow buying and selling agricultural land','Yes/no/undecided. Explicitly agricultural land; separate from the general land item.'),
 'state_market_role':('Preferred role of the state in the economy','Minimal state / mixed state and market / return to planning / undecided. Preserve the mixed option.'),
 'socialism_capitalism_political_support':('Support for political forces favouring capitalism or socialism','Political support, rather than a direct choice of economic systems; both/neither options retained.'),
 'work_private_employer':('Willingness to work for a private employer','Five categories from no to yes; employment preference, not a general policy attitude.'),
 'land_ownership_rights':('Preferred land-ownership regime','Full ownership with sale / inheritable use without sale / communal / state ownership / undecided.'),
 'ownership_policy':('Nationalisation versus further privatisation','Four policy alternatives plus undecided/nonresponse. The 2025 publication simplifies response wording; retain source version and survey mode.'),
}
for object_id, label in [('small','small enterprises'),('large','large enterprises'),('land','land')]:
    LABELS['retrospective_'+object_id]=(f'Was past privatisation of {label} worthwhile?','Five categories from no to yes; retrospective wording, distinct from the original three-category privatisation item.')
    LABELS['existing_private_'+object_id]=(f'Attitude to existing private ownership of {label}','Five categories from negative to positive; asks about existing ownership, rather than transferring ownership.')
    LABELS['renationalise_'+object_id]=(f'Return privately owned {label} to the state','Five categories from yes to no; rejection of nationalisation is the pro-private position.')


def years_text(years):
    years=sorted(set(map(int,years)))
    runs=[]
    for year in years:
        if runs and year==runs[-1][-1]+1:
            runs[-1].append(year)
        else:
            runs.append([year])
    return ', '.join(str(r[0]) if len(r)==1 else f'{r[0]}–{r[-1]}' for r in runs)


def main():
    out=ROOT/'output/tables'
    inventory=pd.read_csv(out/'monitoring_wave_inventory.csv')
    values=pd.read_csv(out/'monitoring_published_results.csv')
    gaps=pd.read_csv(out/'monitoring_explicit_table_gaps.csv')
    locations=pd.read_csv(ROOT/'docs/monitoring_table_locations.csv')
    sources=pd.read_csv(ROOT/'docs/monitoring_sources.csv')
    observed=set(zip(inventory.item,inventory.year))
    explicit=set(zip(gaps.item,gaps.year))
    grid=[]
    for item in LABELS:
        for year in range(1992,2026):
            status=('verified_published_response_table' if (item,year) in observed
                    else 'dash_in_published_table' if (item,year) in explicit
                    else 'no_1993_monitoring_wave_in_programme_history' if year==1993
                    else 'not_located_in_examined_sources')
            grid.append(dict(item=item,year=year,status=status,within_note_period=year<=2020))
    pd.DataFrame(grid).to_csv(out/'monitoring_coverage_grid.csv',index=False)

    crosswalk=[]
    for item,(label,meaning) in LABELS.items():
        v=values[values.item.eq(item)]
        crosswalk.append(dict(item=item,english_description=label,measurement=meaning,
            verified_years=years_text(v.year),response_codes=';'.join(v.response.unique()),
            denominator='All respondents in source table, including undecided and nonresponse',
            missing_values='Source table dashes are not observations; no_answer is reported separately where available',
            weights='Published aggregate; source weighting retained, no new weights applied',
            uncertainty='No item-specific confidence intervals published in these tables',
            territorial_coverage='Changes across waves; consult year-specific volume; cannot harmonise geography from national aggregates',
            source_locations='; '.join(f'{r.source_file} PDF p.{r.pdf_page}, {r.question_code}' for r in locations[locations.item.eq(item)].itertuples())))
    pd.DataFrame(crosswalk).to_csv(ROOT/'docs/monitoring_question_crosswalk.csv',index=False,encoding='utf-8-sig')

    archive=[]
    for r in sources.itertuples():
        path=ROOT/r.local_path
        with pymupdf.open(path) as doc:
            pages=len(doc)
        manifest=json.loads((ROOT/'data/source_manifests'/f'{path.name}.json').read_text(encoding='utf8'))
        archive.append(dict(filename=path.name,pdf_pages=pages,bytes=path.stat().st_size,
            sha256=manifest['sha256'],retrieved_utc=manifest['retrieved_utc'],source_url=r.source_url,
            local_path=r.local_path,used_in_extracted_tables=path.name in set(values.source_file)))
    pd.DataFrame(archive).to_csv(ROOT/'docs/monitoring_archive.csv',index=False)
    assert len(archive)==len(list((ROOT/'data/documentation/monitoring').glob('*.pdf')))

    lines=['# Ukrainian Society monitoring: market-attitude source inventory',
       '', 'Search completed 25 September 2026. These sources feed the integrated monitoring analysis in the research note.', '',
       f'Located and downloaded **{len(archive)} PDFs**. Extracted **{len(inventory)} question–year observations**, '
       f'covering **{len(LABELS)} distinct questions** and **{inventory.year.nunique()} survey years**. '
       f'The machine-readable table contains **{len(values)} response percentages** with exact source pages.', '',
       'The survey programme began with a 1992 pilot and annual monitoring from 1994. '
       'Question coverage varies across years. The latest annual volume found is 2025. '
       '[Programme history](https://www.isnasu.org.ua/monitoring/index.php); '
       '[current volume catalogue](https://isnasu.org.ua/publish/ukrainske-suspilstvo/issues.php); '
       '[older public file archive](https://i-soc.com.ua/assets/files/monitoring/).', '',
       '## Verified waves by question', '',
       'Year ranges below include every year within the range; commas indicate gaps. '
       'The three objects in the repeated ownership modules each remain separate variables.', '',
       '| Question | Number of waves | Verified fieldwork years |', '|---|---:|---|']
    for item,(label,_) in LABELS.items():
        years=inventory.loc[inventory.item.eq(item),'year']
        lines.append(f'| {label} | {len(years)} | {years_text(years)} |')
    lines += ['', '## Where to find the tables', '',
       '| Source | PDF / printed pages | Contribution |', '|---|---|---|',
       '| [Panina, 1994–2005](https://dif.org.ua/uploads/pdf/40574543644fd4df61d653.39323866.pdf) | 20–22, 25 / same | Full annual coverage of the 1990s and early 2000s, including years dropped from later summaries. |',
       '| [2012 volume](https://isnasu.org.ua/assets/files/monitoring/soc-mon-2012.pdf) | 529–533 / same | Adds the 1992 private-business baseline and later business and political-support observations. |',
       '| [2013 volume](https://isnasu.org.ua/assets/files/monitoring/soc-mon-2013.pdf) | 447–450 / same | First verified retrospective-privatisation, existing-ownership and renationalisation modules. |',
       '| [2014 original tables](https://i-soc.com.ua/assets/files/monitoring/us-2014.pdf) | 1 / unpaginated | Private-business question: counts and separate percentages of all respondents and of answers. |',
       '| [2016 appendix](https://isnasu.org.ua/assets/files/monitoring/dodatki2016.pdf) | 6 / 430 | Extends capitalism/socialism political support to 2016. |',
       '| [2017 appendix](https://isnasu.org.ua/assets/files/monitoring/dodatki2017.pdf) | 3–6 / 489–492 | Repeats the ownership modules and introduces the agricultural-land-sales wording. |',
       '| [2018 appendix](https://isnasu.org.ua/assets/files/monitoring/dodatki2018.pdf) | 4 / 418 | Latest general land-sales observation. |',
       '| [2020 volume](https://isnasu.org.ua/assets/files/monitoring/mon2020.pdf) | 443–447 / same | Repeated ownership modules, state/market preferences and land-rights alternatives. |',
       '| [2021 full volume](https://isnasu.org.ua/assets/files/monitoring/monitoring-2021dlya-tipografii.pdf) | 624–625 / same | Latest original privatisation and state/market-role series. Use the full 715-page file; the version without appendices omits these tables. |',
       '| [2024 volume](https://drive.google.com/file/d/1bqw3rZ3ajsNJ2l7zBQL5uRjAWO030EYk/view) | 416 / same | Nationalisation/privatisation policy in 2023 and 2024. |',
       '| [2025 volume](https://drive.google.com/file/d/1CeJIiK0ZLNJ0aHyPbXHrWO21ykIB6m7W/view) | 394 / same | Extends the new policy question to 2025. |',
       '', 'All downloaded volumes, presentations and supplementary sources appear in '
       '[the archive register](../docs/monitoring_archive.csv). Original PDFs are in `data/documentation/monitoring/`.', '',
       '## Additional material for age comparisons', '',
       'The 2021 volume, printed/PDF page 67, Table 2, publishes age-group balance indices for private business '
       '(1994, 1996, 2000, 2004, 2006, 2010, 2014) and privatisation of large firms, small firms and land '
       '(the same years plus 2016 and 2018). Page 69, Table 3, reports land-sales indices for 1994, 1996, 1998, '
       '2000, 2005, 2006, 2014 and 2018. Their groups are under 30, 30–54 and 55+. '
       'These are published positive-minus-negative balances plus 100, on a 0–200 scale; they are indexed here '
       'as additional sources, rather than included in the extracted national response table.', '',
       '## Limitations and source corrections', '',
       '- **Different questions stay separate.** In the 2021 volume, page 87 includes a 2020 land figure '
       'alongside the older privatisation series. The original 2020 table (page 445, a8r) shows that it comes '
       'from approval of existing private land ownership. The acquisition files preserve the original question identity. '
       'General land sales and explicitly agricultural land sales are also separate.',
       '- **All-respondent denominators are retained.** The 2014 private-business table gives both all-sample '
       'and valid-answer percentages. The extract uses the former; its nonresponse percentage is calculated '
       'from the printed total and answered counts. Published commentary sometimes uses valid answers instead.',
       '- **Small publication discrepancies are recorded.** The 2017 small-firm renationalisation nonresponse '
       'cell differs by 0.1 percentage point between the 2017 and 2020 appendices. The later appendix is preferred. '
       'The 2023/2024 presentations also differ by 0.1 point in selected cells from the annual-volume tables; '
       'the annual-volume tables supply the extracted 2023–2025 series. Earlier duplicates remain in the source-cell file.',
       '- **Unlocated years remain visible.** The coverage grid distinguishes a dash explicitly printed in a table '
       'from a question–year observation not located in the examined sources. No relevant observations were '
       'located for 2007, 2009 or 2022 among the 20 selected questions; this does not establish that those '
       'years had no survey or no other relevant item. No 1993 monitoring wave appears in the programme history.',
       '- **Geography and mode change.** National aggregates cannot be re-estimated for a constant territory. '
       'The wartime series also changes mode: CATI in 2023, CATI recruitment followed by smartphone CAWI in '
       '2024, and CATI in 2025 (2025 volume, page 392). The 2025 response wording is simplified relative to 2024.',
       '- **Age bands and uncertainty require respondent data.** Published age bands do not match this project’s '
       '18–34, 35–54 and 55+ groups. Item-specific confidence intervals and respondent-level index uncertainty '
       'cannot be recovered from these national percentage tables. Some published age-index totals also disagree '
       'with the response tables and need checking before use. The '
       '[OCA project page](https://oca.com.ua/index.php?t=132) describes the integrated respondent data as '
       'available by contacting the Institute; it does not provide an open download.',
       '', '## Reproduce and use', '',
       'Run from the project directory:', '', '```powershell',
       'python scripts/monitoring_acquire.py', 'python scripts/monitoring_extract.py',
       'python scripts/monitoring_inventory.py', 'python scripts/monitoring_analysis.py', '```', '',
       'The full `python scripts/run.py` pipeline includes these stages and rebuilds the charts and note. '
       'Its extraction stage downloads missing sources from the recorded archive; acquisition above is for an intentional catalogue refresh.', '',
       'Dependencies: the existing project environment plus PyMuPDF and Beautiful Soup. '
       'Downloads retain their URLs, retrieval times and SHA256 hashes. Extraction checks source hashes, '
       'column counts, valid ranges, duplicate estimates and response totals. Every retained percentage points '
       'to a source file, PDF page and question code. Dashes are never converted to zero.', '',
       '- [Published response percentages](tables/monitoring_published_results.csv)',
       '- [Analytical indicators and index](tables/monitoring_estimates.csv)',
       '- [Indicator-to-source-cell trace](tables/monitoring_analysis_trace.csv)',
       '- [Question–wave inventory and exact pages](tables/monitoring_wave_inventory.csv)',
       '- [Complete coverage grid, including gaps](tables/monitoring_coverage_grid.csv)',
       '- [Question crosswalk](../docs/monitoring_question_crosswalk.csv)',
       '- [Validation results](tables/monitoring_validation.json)', '',
       'The main cross-survey analysis retains its 2020 endpoint. The note includes a separately dated '
       'extension for 2021 and the 2023–2025 wartime ownership-policy series.']
    (ROOT/'output/monitoring_inventory.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    print(f'Created inventory: {len(archive)} PDFs; {len(grid)} coverage cells; {len(crosswalk)} questions.')


if __name__=='__main__':
    main()
