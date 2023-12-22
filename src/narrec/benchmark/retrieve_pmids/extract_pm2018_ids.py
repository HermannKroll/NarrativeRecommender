import ir_datasets
import os
import logging

from narrec.config import DATA_DIR


def main():
    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.DEBUG)
    output_file_path = os.path.join(DATA_DIR, "pmids_tg2005.txt")
    dataset = ir_datasets.load("medline/2004/trec-genomics-2005")

    with open(output_file_path, 'w') as output_file:
        for doc in dataset.docs_iter():
            output_file.write(doc.doc_id + '\n')

    with open(output_file_path, 'r') as file:
        num_documents = sum(1 for line in file)
    logging.info(f"{num_documents} PMIDs written to '{output_file_path}'")


if __name__ == "__main__":
    main()
