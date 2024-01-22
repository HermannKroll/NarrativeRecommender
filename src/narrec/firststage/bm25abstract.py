from narrec.document.document import RecommenderDocument
from narrec.firststage.bm25 import BM25Base


class BM25Abstract(BM25Base):

    def __init__(self, index_path):
        super().__init__(name="BM25Abstract", index_path=index_path)

    def retrieve_documents_for(self, document: RecommenderDocument):
        if document.abstract and document.abstract.strip():
            return self.do_bm25_retrieval(document.abstract)
        else:
            return self.do_bm25_retrieval(document.title)
