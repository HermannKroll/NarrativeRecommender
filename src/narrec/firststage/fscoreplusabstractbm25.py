from narrec.benchmark.benchmark import Benchmark
from narrec.document.core import NarrativeCoreExtractor
from narrec.document.document import RecommenderDocument
from narrec.firststage.bm25abstract import BM25Abstract
from narrec.firststage.fscore import FSCore


class FSCorePlusAbstractBM25(FSCore):

    def __init__(self, extractor: NarrativeCoreExtractor, benchmark: Benchmark,
                 bm25_index_path: str):
        super().__init__(name="FSCorePlusAbstractBM25", extractor=extractor, benchmark=benchmark)
        self.bm25 = BM25Abstract(bm25_index_path)

    def retrieve_documents_for(self, document: RecommenderDocument):
        document_ids_scored = super().retrieve_documents_for(document)
        if not document_ids_scored:
            # We dont have any core
            return self.bm25.retrieve_documents_for(document)
        return document_ids_scored