import logging
import os
import shutil

import pandas as pd
import pyterrier as pt
from tqdm import tqdm

from kgextractiontoolbox.backend.models import Document
from narrec.backend.database import SessionRecommender
from narrec.benchmark.benchmark import Benchmark
from narrec.benchmark.benchmarks import Benchmarks
from narrec.config import INDEX_DIR


class BenchmarkIndex:

    def __init__(self, benchmark: Benchmark):
        self.collection = 'PubMed'
        self.benchmark = benchmark
        self.name = benchmark.name
        self.path = os.path.join(INDEX_DIR, self.name)
        self.index = None
        if os.path.isdir(self.path):
            print(f'Loading index from {self.path}')
            self.index = pt.IndexFactory.of(self.path)
        else:
            self.create_index()

    def create_index(self):
        values = []
        session = SessionRecommender.get()
        logging.info(f'Create index for {self.name} (collections = {self.collection})')
        logging.info(f'Iterating over all documents in {self.collection}')

        total = session.query(Document).filter(Document.collection == self.collection).count()
        doc_query = session.query(Document).filter(Document.collection == self.collection)
        for d in tqdm(doc_query, total=total):
            # Filter on PubMed documents
            if self.collection == 'PubMed' and self.benchmark.get_documents_for_baseline():
                if int(d.id) not in self.benchmark.get_documents_for_baseline():
                    # Skip documents that are not relevant for that baseline
                    continue

            text = f'{d.title} {d.abstract}'
            if text.strip():
                values.append([str(d.id), text])

        print()
        logging.info(f'{len(values)} documents retrieved...')
        logging.info('Creating dataframe...')
        df = pd.DataFrame(values, columns=['docno', 'text'])
        logging.info('Creating index...')
        pd_indexer = pt.DFIndexer(self.path, verbose=True)
        self.index = pd_indexer.index(df["text"], df["docno"])
        logging.info('Finished!')


def main():
    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.INFO)

    logging.info('Removing old index directory...')
    shutil.rmtree(INDEX_DIR)
    logging.info('Creating benchmark pyterrier indexes...')

    pt.init()
    for benchmark in Benchmarks():
        logging.info(f'Creating index for {benchmark.name}')
        index = BenchmarkIndex(benchmark)
    logging.info('Finished')


if __name__ == '__main__':
    main()
