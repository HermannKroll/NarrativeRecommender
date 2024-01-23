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
        # Compute the cores
        cores = self.extractor.extract_narrative_core_from_document(document)

        # We dont have any core
        if not cores:
            return self.bm25.retrieve_documents_for(document)

        # scores are sorted by their size
        max_core = cores[0]

        # Core statements are also sorted by their score
        document_ids_scored = []
        for stmt in max_core.statements:
            # retrieve matching documents
            document_ids = self.retrieve_documents((stmt.subject_id, stmt.relation, stmt.object_id))
            # add all documents with the statement score to our list
            document_ids_scored.extend([(d, stmt.score) for d in document_ids])

        return document_ids_scored
