import string

import pyterrier as pt

from narrec.config import BM25_DOCUMENT_CUTOFF
from narrec.firststage.base import FirstStageBase


class BM25Base(FirstStageBase):

    def __init__(self, name, index_path):
        super().__init__(name=name)
        if not pt.started():
            pt.init()
        self.index = pt.IndexFactory.of(index_path)
        self.translator = str.maketrans("", "", string.punctuation)

    def do_bm25_retrieval(self, query: str):
        # Replace punctuation
        query = query.translate(self.translator)
        bm25 = pt.BatchRetrieve(self.index, wmodel="BM25")
        rtr = bm25.search(query)
        scored_docs = []

        for index, row in rtr.iterrows():
            scored_docs.append((row["docno"], row["score"]))

        scored_docs = sorted(scored_docs, key=lambda x: (x[1], x[0]), reverse=True)
        scored_docs = scored_docs[:BM25_DOCUMENT_CUTOFF]
        return scored_docs
