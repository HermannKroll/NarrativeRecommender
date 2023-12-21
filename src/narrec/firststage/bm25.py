import os.path
import pyterrier as pt

from narrec.firststage.base import FirstStageBase
from narrec.document.document import RecommenderDocument
# TODO: set new index path and document cutoff

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
            scored_docs = scored_docs[:RANKED_DOCUMENT_CUTOFF]

            max_score = scored_docs[0][1]
            rank = 0

            for doc, score in scored_docs:
                norm_score = score / max_score
                result_lines.append(f'{topic.query_id}\tQ0\t{doc}\t{rank + 1}\t{norm_score}\tBM25')
                rank += 1

        result_file_path = os.path.join(PYTERRIER_INDEX_PATH,
                                        f'{self.benchmark_index.name}_FirstStageBM25Own.txt')
        print(f'Writing results to {result_file_path}')

        with open(result_file_path, 'wt') as f:
            f.write('\n'.join([l for l in result_lines]))

        print('Finished')



def main():



if __name__ == '__main__':
    main()
