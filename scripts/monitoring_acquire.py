"""Acquire the Institute of Sociology's public monitoring volumes and catalog.

Run independently of the main research-note pipeline. Original PDFs stay in
data/documentation/monitoring; each download receives the standard SHA256 manifest.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin
import csv
import re
from bs4 import BeautifulSoup
from acquire import ROOT, download, session

CATALOG = 'https://isnasu.org.ua/publish/ukrainske-suspilstvo/issues.php'
METHODS = 'https://www.isnasu.org.ua/monitoring/index.php'
DEST = ROOT / 'data/documentation/monitoring'


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    records = []
    for name, url in [('catalog', CATALOG), ('methods', METHODS)]:
        r = session().get(url, timeout=60)
        r.raise_for_status()
        r.encoding = 'utf-8'
        (DEST / f'{name}.html').write_text(r.text, encoding='utf-8')
        for a in BeautifulSoup(r.text, 'html.parser').find_all('a', href=True):
            link = urljoin(url, a['href'])
            if '.pdf' not in link.lower() and 'drive.google.com/file/d/' not in link:
                continue
            title = a.get_text(' ', strip=True)
            if 'drive.google.com' in link:
                file_id = link.split('/d/')[1].split('/')[0]
                year = re.search(r'202[45]', title)
                filename = f'monitoring-{year.group()}.pdf' if year else 'monitoring-2024-presentation.pdf'
                download_url = f'https://drive.google.com/uc?export=download&id={file_id}'
            else:
                filename = link.rsplit('/', 1)[-1]
                download_url = link
            records.append(dict(title=title, catalog_url=url, source_url=link,
                                download_url=download_url,
                                local_path=f'data/documentation/monitoring/{filename}'))
    extras = [
        ('https://isnasu.org.ua/assets/files/monitoring/presentation_monitoring_2025.pdf', 'presentation_monitoring_2025.pdf'),
        ('https://isnasu.org.ua/assets/files/books/2023/prezentaciya-monitoringu-2023.pdf', 'prezentaciya-monitoringu-2023.pdf'),
        ('https://oca.com.ua/arc/ukrmonit.pdf', 'oca-ukrmonit.pdf'),
        ('https://i-soc.com.ua/assets/files/book/rakhmanov/rakhmanov_mon_2010.pdf', 'rakhmanov_mon_2010.pdf'),
        ('https://dif.org.ua/uploads/pdf/40574543644fd4df61d653.39323866.pdf', 'panina-1994-2005.pdf'),
        ('https://i-soc.com.ua/assets/files/monitoring/us-2014.pdf', 'us-2014.pdf'),
        ('https://i-soc.com.ua/assets/files/monitoring/2014monitoringist1.pdf', '2014monitoringist1.pdf'),
        ('https://i-soc.com.ua/assets/files/monitoring/us-2015.pdf', 'us-2015.pdf'),
    ]
    for url, filename in extras:
        records.append(dict(title=filename, catalog_url='Public supplementary source', source_url=url,
                            download_url=url, local_path=f'data/documentation/monitoring/{filename}'))
    with (ROOT / 'docs/monitoring_sources.csv').open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)

    def fetch(record):
        try:
            download(record['download_url'], record['local_path'], record['title'])
            return record['local_path'], 'ok'
        except Exception as exc:
            return record['local_path'], str(exc)

    with ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(fetch, records):
            print(result, flush=True)


if __name__ == '__main__':
    main()
