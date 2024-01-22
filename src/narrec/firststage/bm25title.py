from narrec.document.document import RecommenderDocument
from narrec.firststage.bm25 import BM25Base


class BM25Title(BM25Base):

    def __init__(self, index_path):
        super().__init__(name="BM25Title", index_path=index_path)

    def retrieve_documents_for(self, document: RecommenderDocument):
        return self.do_bm25_retrieval(document.title)
