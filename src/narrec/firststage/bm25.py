import os.path

import pyterrier as pt

from narrec.config import BM25_DOCUMENT_CUTOFF, RESULT_DIR
from narrec.document.document import RecommenderDocument
from narrec.firststage.base import FirstStageBase


class BM25(FirstStageBase):

    def __init__(self, benchmark_index):
        super().__init__()
        self.benchmark_index = benchmark_index

    def retrieve_document_for(self, document: RecommenderDocument):
        print(f'Performing BM25 Retrieval on {document}...')
        bm25 = pt.BatchRetrieve(self.benchmark_index.index, wmodel="BM25")
        result_lines = []

        # TODO: search with document
        for topic in self.benchmark_index.benchmark.topics:
            rtr = bm25.search(topic.get_benchmark_string())
            scored_docs = []

            for index, row in rtr.iterrows():
                scored_docs.append((row["docno"], row["score"]))

            scored_docs = sorted(scored_docs, key=lambda x: x[1], reverse=True)
            scored_docs = scored_docs[:BM25_DOCUMENT_CUTOFF]

            max_score = scored_docs[0][1]
            rank = 0

            for doc, score in scored_docs:
                norm_score = score / max_score
                result_lines.append(f'{topic.query_id}\tQ0\t{doc}\t{rank + 1}\t{norm_score}\tBM25')
                rank += 1

        result_file_path = os.path.join(RESULT_DIR,
                                        f'{self.benchmark_index.name}_FirstStageBM25.txt')
        print(f'Writing results to {result_file_path}')

        with open(result_file_path, 'wt') as f:
            f.write('\n'.join([l for l in result_lines]))

        print('Finished')
