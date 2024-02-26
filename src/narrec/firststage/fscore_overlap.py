from narrec.backend.retriever import DocumentRetriever
from narrec.benchmark.benchmark import Benchmark
from narrec.config import GLOBAL_DB_DOCUMENT_COLLECTION
from narrec.document.core import NarrativeCoreExtractor
from narrec.document.document import RecommenderDocument
from narrec.firststage.bm25abstract import BM25Abstract
from narrec.firststage.fscore import FSCore
from narrec.run_config import FS_DOCUMENT_CUTOFF


class FSCoreOverlap(FSCore):

    def __init__(self, extractor: NarrativeCoreExtractor, benchmark: Benchmark, bm25_index_path: str,
                 retriever: DocumentRetriever):
        super().__init__(name="FSCoreOverlap", extractor=extractor, benchmark=benchmark)
        self.bm25 = BM25Abstract(bm25_index_path)
        self.retriever = retriever

    def retrieve_documents_for(self, document: RecommenderDocument):
        # Compute the cores
        core_a = self.extractor.extract_narrative_core_from_document(document)

        # We dont have any core
        if not core_a:
            return []

        # compute a list of bm25 candidate matches
        bm25_candidates = self.bm25.retrieve_documents_for(document)

        # search for the first document that has a core
        core_b = None
        for candidate_id, _ in bm25_candidates:
            candidate = self.retriever.retrieve_narrative_documents([candidate_id],
                                                                    GLOBAL_DB_DOCUMENT_COLLECTION)[0]

            core_b = self.extractor.extract_narrative_core_from_document(candidate)
            if core_b:
                break

        # if we do not have a core b, search with a
        if not core_b:
            return self.score_document_ids_with_core(core_a)[:FS_DOCUMENT_CUTOFF]

        # compute the intersection between both cores
        core_inter = core_a.intersect(core_b)

        # score with core intersection
        docs_inter = self.score_document_ids_with_core(core_inter)

        # We did not find any documents
        if len(docs_inter) == 0:
            return []

        if len(docs_inter) >= FS_DOCUMENT_CUTOFF:
            return docs_inter[:FS_DOCUMENT_CUTOFF]

        # otherwise fill list with normal core computation
        contained_ids = {d[0] for d in docs_inter}
        docs_with_core_a = [d for d in self.score_document_ids_with_core(core_a)
                            if d[0] not in contained_ids]

        # rescale list
        docs_inter = [(d[0], d[1] * 0.5 + 0.5) for d in docs_inter]
        docs_inter += [(d[0], d[1] * 0.5) for d in docs_with_core_a]

        # Ensure cutoff
        return docs_inter[:FS_DOCUMENT_CUTOFF]
