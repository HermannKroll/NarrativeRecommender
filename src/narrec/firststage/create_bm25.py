import os.path
import pyterrier as pt
import pandas as pd
from tqdm import tqdm
from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.models import Document


class BenchmarkIndex:

    def __init__(self, benchmark):
        self.collection = 'Pubmed'
        self.benchmark = benchmark
        self.name = benchmark.name
        self.path = os.path.join(PYTERRIER_INDEX_PATH, self.name) # TODO: set index path
        self.index = None
        if os.path.isdir(self.path):
            print(f'Loading index from {self.path}')
            self.index = pt.IndexFactory.of(self.path)
        else:
            self.create_index()

    def create_index(self):
        values = []
        session = Session.get()
        print(f'Create index for {self.name} (collections = {self.collection})')
        print(f'\nIterating over all documents in {self.collection}')

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
        print(f'{len(values)} documents retrieved...')
        print('Creating dataframe...')
        df = pd.DataFrame(values, columns=['docno', 'text'])
        print('Creating index...')
        pd_indexer = pt.DFIndexer(self.path, verbose=True)
        self.index = pd_indexer.index(df["text"], df["docno"])
        print('Finished!')