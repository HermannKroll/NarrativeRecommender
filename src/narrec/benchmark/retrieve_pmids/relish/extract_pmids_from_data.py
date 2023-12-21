import tarfile
import os
import shutil
import gzip
import subprocess
import logging
import concurrent.futures
import xml.etree.ElementTree as ET

from narrec.config import PMIDS_DIR


def download_data():
    current_directory = os.getcwd()
    data_path = os.join(current_directory, "path")
    if not os.path.exists(data_path):
        os.makedirs(data_path)
    subprocess.run(['cd', data_path])

    def download_url(url):
        logging.info(f"Downloading from {url}")
        subprocess.run(["wget", url])

    urls_to_download = ["https://bionlp.nlm.nih.gov/trec2017precisionmedicine/medline_xml.part1.tar.gz",
                        "https://bionlp.nlm.nih.gov/trec2017precisionmedicine/medline_xml.part2.tar.gz",
                        "https://bionlp.nlm.nih.gov/trec2017precisionmedicine/medline_xml.part3.tar.gz",
                        "https://bionlp.nlm.nih.gov/trec2017precisionmedicine/medline_xml.part4.tar.gz",
                        "https://bionlp.nlm.nih.gov/trec2017precisionmedicine/medline_xml.part5.tar.gz"]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(download_url, urls_to_download)

    logging.info("Finished downloading")


def extract_pmids_from_xml(xml_content):
    root = ET.fromstring(xml_content)
    pmid_elements = root.findall('.//PMID')

    return {pmid.text for pmid in pmid_elements}


def unpack_data(data_folder, tar_files, unpacked_folder):
    for file in tar_files:
        logging.info(f"Processing {file}...")
        with tarfile.open(os.path.join(data_folder, file), "r:gz") as tar:
            tar.extractall(path=unpacked_folder)

    for file in os.listdir(unpacked_folder):
        if file.endswith(".gz"):
            logging.info(f"Processing {file}...")
            with gzip.open(os.path.join(unpacked_folder, file), 'rb') as f_in:
                with open(os.path.join(unpacked_folder, file[:-3]), 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            os.remove(os.path.join(unpacked_folder, file))
        if file.endswith(".md5"):
            os.remove(os.path.join(unpacked_folder, file))


def process_folder(folder_path, output_file):
    all_pmids = set()
    for filename in os.listdir(folder_path):
        if filename.endswith('.xml'):
            logging.info(f"Processing {filename}...")
            file_path = os.path.join(folder_path, filename)

            with open(file_path, 'r', encoding='utf-8') as file:
                xml_content = file.read()
                pmids = extract_pmids_from_xml(xml_content)
                logging.info(f"{len(pmids)} found")
                all_pmids.update(pmids)

    logging.info(f"{len(all_pmids)} were found")
    logging.info(f"writing to txt file...")
    with open(output_file, 'w') as output:
        for pmid in all_pmids:
            output.write(f"{pmid}\n")


def main():
    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.DEBUG)
    download_data()
    data_folder = "data/"
    tar_files = ["medline_xml.part1.tar.gz", "medline_xml.part2.tar.gz", "medline_xml.part3.tar.gz",
                 "medline_xml.part4.tar.gz", "medline_xml.part5.tar.gz"]
    unpacked_folder = os.path.join(data_folder, "unpacked_data")
    os.makedirs(unpacked_folder, exist_ok=True)

    unpack_data(data_folder, tar_files, unpacked_folder)

    output_file = os.path.join(PMIDS_DIR, 'pmids_pm2018.txt')

    process_folder(unpacked_folder, output_file)


if __name__ == "__main__":
    main()
