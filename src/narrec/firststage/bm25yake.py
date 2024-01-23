from yake import KeywordExtractor

from narrec.document.document import RecommenderDocument
from narrec.firststage.bm25 import BM25Base


class BM25Yake(BM25Base):

    def __init__(self, index_path):
        super().__init__(name="BM25Yake", index_path=index_path)
        self.extractor = KeywordExtractor()

    def retrieve_documents_for(self, document: RecommenderDocument):
        text = f'{document.title} {document.abstract}'
        raw_keywords = self.extractor.extract_keywords(text)
        query_str = ' '.join([k[0] for k in raw_keywords])
        return self.do_bm25_retrieval(query_str)
