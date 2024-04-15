import glob
import gzip
import logging
import os
import re

import requests
from lxml import etree
from tqdm import tqdm

from narrec.config import DATA_DIR


# First of all, MEDLINE data 2018 must be crawled
# wget -m https://lhncbc.nlm.nih.gov/ii/information/MBR/Baselines/ -P 2018

# wget -m -r https://data.lhncbc.nlm.nih.gov/public/ii/information/MBR/Baselines/2018

def crawl_pubmed_medline_data(medline_directory):
    MASTER_URL = "https://lhncbc.nlm.nih.gov/ii/information/MBR/Baselines/2018.html"

    r = requests.get(MASTER_URL)
    content = str(r.content)

    # extract all downloadable medlines files from URL
    regex = re.compile('href="[\w\\\/:.]+"')
    matches = regex.findall(content)
    for match in tqdm(matches, total=len(matches)):
        # dissemble url
        file_url = match.split('"')[1]
        file_name = file_url.split('/')[-1]

        file_path = os.path.join(medline_directory, file_name)
        if os.path.exists(file_path):
            print(f'Skipping existing file {file_path}')
            continue

        with open(file_path, 'wb') as f_out:
            medline_data = requests.get(file_url).content
            f_out.write(medline_data)

    print("Finished crawling medline data")


def pubmed_medline_extract_document_ids(directory, output):
    print(f'Collecting all PubMed ids in {directory}')
    if directory[-1] == '/':
        directory = directory[:-1]
    files = list(glob.glob(f'{directory}/**/*.xml.gz', recursive=True) +
                 glob.glob(f'{directory}/**/*.xml', recursive=True))
    all_pmids = set()
    for idx, filename in tqdm(enumerate(files), total=len(files)):
        if filename.endswith('.xml'):
            with open(filename) as f:
                tree = etree.parse(f)
        elif filename.endswith('.xml.gz'):
            with gzip.open(filename) as f:
                tree = etree.parse(f)

        for article in tree.iterfind("PubmedArticle"):
            # Get PMID
            pmids = article.findall("./MedlineCitation/PMID")
            for pmid in pmids:
                all_pmids.add(int(pmid.text))

    print('Finished')

    print(f"{len(all_pmids)} were found")
    print(f"writing to txt file...")
    with open(output, 'w') as f_out:
        f_out.write('\n'.join([str(p) for p in all_pmids]))


def main():
    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.DEBUG)
    input_dir = os.path.join(DATA_DIR, "medline_2018")
    output_file = os.path.join(DATA_DIR, 'pmids_pm2018.txt')
    crawl_pubmed_medline_data(input_dir)
    pubmed_medline_extract_document_ids(input_dir, output_file)


if __name__ == "__main__":
    main()
