from typing import List

import pandas as pd
import pyterrier as pt

from narrec.document.document import RecommenderDocument


class BM25Scorer:

    def __init__(self, bm25_index):
        self.cache = {}
        if not pt.started():
            pt.init()

        self.bm25pipeline = None
        if bm25_index:
            self.set_index(bm25_index)

    def set_index(self, bm25_index):
        bm25_index = pt.IndexFactory.of(bm25_index, memory=True)
        self.bm25pipeline = pt.BatchRetrieve(
            bm25_index,
            wmodel='BM25',
            properties={'termpipelines': 'Stopwords,PorterStemmer'}
        )

    @staticmethod
    def filter_query_string(query):
        return "".join([x if x.isalnum() else " " for x in query])

    def score_document_ids_with_bm25(self, document: RecommenderDocument, document_ids: List[int]):
        key = (document.id, '_'.join([str(d) for d in document_ids]))
        if key in self.cache:
            return self.cache[key]

        doc_vals = [["q0", BM25Scorer.filter_query_string(document.get_text_content()), str(docid)]
                    for docid in document_ids]
        df = pd.DataFrame(doc_vals, columns=["qid", "query", "docno"])
        rtr = self.bm25pipeline(df)

        scored_docs = []
        for index, row in rtr.iterrows():
            scored_docs.append(((int(row["docno"])), max(float(row["score"]), 0.0)))

        max_score = max(sd[1] for sd in scored_docs)
        if max_score > 0.0:
            scored_docs = {sd[0]: (sd[1] / max_score) for sd in scored_docs}
        else:
            scored_docs = {sd[0]: sd[1] for sd in scored_docs}

        self.cache[key] = scored_docs
        return scored_docs
