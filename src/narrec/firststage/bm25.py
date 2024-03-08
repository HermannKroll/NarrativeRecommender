import string

import pyterrier as pt

from narrec.firststage.base import FirstStageBase
from narrec.run_config import FS_DOCUMENT_CUTOFF


class BM25Base(FirstStageBase):

    def __init__(self, name, index_path):
        super().__init__(name=name)
        if not pt.started():
            pt.init()
        self.index = pt.IndexFactory.of(index_path, memory=True)

    def filter_query_string(self, query):
        return "".join([x if x.isalnum() else " " for x in query])

    def do_bm25_retrieval(self, query: str):
        # Replace punctuation
        bm25 = pt.BatchRetrieve(self.index, wmodel="BM25")
        rtr = bm25.search(self.filter_query_string(query))
        scored_docs = []

        for index, row in rtr.iterrows():
            # dont allow negative bm25 scores
            scored_docs.append((row["docno"], max(0.0, float(row["score"]))))

        scored_docs = sorted(scored_docs, key=lambda x: (x[1], x[0]), reverse=True)
        if len(scored_docs) > 0:
            max_score = scored_docs[0][1]
            scored_docs = [(d, score / max_score) for d, score in scored_docs]

        scored_docs = scored_docs[:FS_DOCUMENT_CUTOFF]
        return scored_docs
