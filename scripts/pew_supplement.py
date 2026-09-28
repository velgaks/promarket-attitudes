"""Extract published Pew Ukraine results, without representing them as microdata.

The national input is Q16a on PDF page 35 (printed p. 150) of the
2019 topline. The 1991 observation is a benchmark with prospective wording.
2019 age values are visually audited transcriptions of a raster chart.
"""
import hashlib
import json
import re
import pandas as pd
import pdfplumber
from analyze import ROOT
from acquire import download

TOPLINE_URL = 'https://www.pewresearch.org/global/wp-content/uploads/sites/2/2019/10/Pew-Research-Center-Value-of-Europe-Topline-for-Release-FINAL.pdf'
REPORT_URL = 'https://www.pewresearch.org/global/wp-content/uploads/sites/2/2019/10/Pew-Research-Center-Value-of-Europe-report-FINAL-UPDATED.pdf'
METHOD_URL = 'https://www.pewresearch.org/global/2019/10/15/methodology-43/'
TOPLINE_HASH = '63d849917258b912ed7543e05cec3770f400de2d3726f5d0506c4e9f41141b98'
REPORT_HASH = 'c7401779a9f9f9ec3ec499b58faf34cf75f914f63383ca6546aabddb3e2ead27'


def source(url, filename, expected_hash):
    path = ROOT / 'data/documentation' / filename
    if not path.exists():
        download(url, path.relative_to(ROOT).as_posix(), 'Pew published aggregate source')
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected_hash:
        raise ValueError(f'Pew source version changed; review before using: {filename}')
    return path


def main():
    topline = source(TOPLINE_URL, 'pew_2019_europe_topline.pdf', TOPLINE_HASH)
    source(REPORT_URL, 'pew_2019_europe_report.pdf', REPORT_HASH)
    with pdfplumber.open(topline) as pdf:
        text = pdf.pages[34].extract_text()
    question = text.split('Q16a.', 1)[1]
    assert 'state-controlled economy' in question and 'In 1991' in question
    ukraine = question.split('Ukraine', 1)[1].split('In 1991', 1)[0]
    pattern = r'^\s*(Spring|Fall),\s+(\d{4})\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*$'
    rows = []
    for match in re.finditer(pattern, ukraine, re.MULTILINE):
        season, year, *values = match.groups()
        strong, approve, disapprove, strong_disapprove, missing, total = map(int, values)
        assert total == 100 and abs(sum(map(int, values[:-1])) - 100) <= 2
        rows.append(dict(survey='Pew', year=int(year), season=season,
            item='transition_approval', age_group='All', denominator='all_adults',
            estimate=strong+approve, strongly_approve=strong, approve=approve,
            disapprove=disapprove, strongly_disapprove=strong_disapprove,
            missing_pct=missing, ci_low=None, ci_high=None,
            estimate_origin='sum of rounded published approval categories',
            source_url=TOPLINE_URL, pdf_page=35, printed_page=150,
            source_sha256=TOPLINE_HASH))
    national = pd.DataFrame(rows).sort_values('year')
    # Independent published net checks: 1991/2009/2019 in the 2019 report p.22;
    # 2011 in Pew's 2011 economic-changes chapter. These also check extraction order.
    published_nets = {1991:52, 2009:36, 2011:34, 2019:47}
    assert dict(zip(national.year, national.estimate)) == published_nets
    ages = pd.read_csv(ROOT / 'docs/pew_published_age_values.csv')
    assert ages.source_sha256.eq(REPORT_HASH).all()
    assert set(ages.age_group) == {'18-34', '35-59', '60+'}
    assert ages.estimate.between(0, 100).all() and len(ages) == 3
    ages['estimate_origin'] = 'published rounded net, chart transcription'
    ages['ci_low'] = None
    ages['ci_high'] = None
    out = ROOT / 'output/tables'
    pd.concat([national, ages], ignore_index=True).to_csv(out / 'pew_published_results.csv', index=False)
    crosswalk = []
    for year in national.year:
        benchmark = year == 1991
        crosswalk.append(dict(survey='Pew', fieldwork_year=year, question='Q16a in 2019 trend topline',
            wording_summary='Approval of efforts to establish a free-market economy' if benchmark else 'Approval of the move from a state-controlled economy to a market economy',
            responses='Strongly approve; approve; disapprove; strongly disapprove; do not know/refused',
            analysis='Sum first two published percentage categories',
            denominator='All sampled adults, including missing answers',
            missing='Published DK/refused retained in denominator',
            weight='Pew published weighted percentages; respondent weights not acquired',
            territorial_coverage='Excludes Crimea and conflict areas in Donetsk/Luhansk' if year == 2019 else 'Includes Crimea and eastern regions',
            comparability_status='Historical benchmark: prospective wording differs' if benchmark else 'Comparable retrospective approval wording in trend topline',
            uncertainty='No item-specific intervals in topline; not estimated from rounded aggregates',
            microdata_verified=False, source_url=TOPLINE_URL, methodology_url=METHOD_URL,
            pdf_page=35, printed_page=150))
    pd.DataFrame(crosswalk).to_csv(ROOT / 'docs/pew_question_crosswalk.csv', index=False)
    check = dict(status='passed', evidence_type='published aggregate supplement',
        national_waves=4, published_age_groups=3, microdata_acquired=False,
        source_page='2019 topline PDF page 35, printed page 150, Q16a',
        national_net_checks=published_nets,
        net_check_sources=[REPORT_URL+'#page=23',
            'https://www.pewresearch.org/global/2011/12/05/chapter-2-views-of-economic-changes-and-national-conditions/'],
        age_source='2019 report PDF page 24, printed page 23; labels kept as published',
        ci_status='Unavailable for these published items; no CI fabricated',
        age_harmonisation='Published 35-59 and 60+ groups are not relabelled as 35-54 and 55+',
        microdata_access='Pew account required at /dataset/spring-2019-survey-data/ and /dataset/fall-2009-survey-data/')
    (out / 'pew_validation.json').write_text(json.dumps(check, indent=2)+'\n', encoding='utf8')
    print('Pew published supplement: four national observations and three 2019 age groups verified.')


if __name__ == '__main__':
    main()
