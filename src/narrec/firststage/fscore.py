import json
from sqlalchemy import or_, and_

from narraint.backend.database import SessionExtended
from narraint.backend.models import PredicationInvertedIndex
from narrec.benchmark.benchmark import Benchmark
from narrec.document.core import NarrativeCoreExtractor, NarrativeCore
from narrec.document.document import RecommenderDocument
from narrec.firststage.base import FirstStageBase
from narrec.run_config import FS_DOCUMENT_CUTOFF, CORE_TOP_K


class FSCore(FirstStageBase):

    def __init__(self, extractor: NarrativeCoreExtractor, benchmark: Benchmark, name="FSCore"):
        super().__init__(name=name)
        self.extractor = extractor
        self.benchmark = benchmark
        self.session = SessionExtended.get()

    def retrieve_documents(self, spo: tuple):
        q = self.session.query(PredicationInvertedIndex)
        # Search for matching nodes but not for predicates (ignore direction)
        q = q.filter(or_(and_(PredicationInvertedIndex.subject_id == spo[0], PredicationInvertedIndex.object_id == spo[2]),
                         and_(PredicationInvertedIndex.subject_id == spo[2], PredicationInvertedIndex.object_id == spo[0])))
    #    q = q.filter(PredicationInvertedIndex.relation == spo[1])
        q = q.filter(PredicationInvertedIndex.document_collection == self.benchmark.document_collection)

        document_ids = set()
        for row in q:
            prov_mapping = json.loads(row.provenance_mapping)
            for doc_id in prov_mapping:
                doc_id_int = int(doc_id)
                if self.benchmark.document_collection == "PubMed" and self.benchmark.get_documents_for_baseline():
                    if doc_id_int not in self.benchmark.get_documents_for_baseline():
                        continue
                    document_ids.add(doc_id_int)

        return document_ids

    def score_document_ids_with_core(self, core: NarrativeCore):
        # Core statements are also sorted by their score
        document_ids_scored = {}
        # If a statement of the core is contained within a document, we increase the score
        # of the document by the score of the corresponding edge
        for idx, stmt in enumerate(core.statements[:CORE_TOP_K]):
            # we already found enough documents
            if len(document_ids_scored) >= FS_DOCUMENT_CUTOFF:
                # get the remaining reachable score
                # if all documents that we found are above the reachable score, we can stop
                max_reachable_scores = sum(c.score for c in core.statements[idx:])
                count = len([d for d, s in document_ids_scored.items()
                             if s >= max_reachable_scores])
                if count >= FS_DOCUMENT_CUTOFF:
                    # we can't find better documents, stop here
                    # the first K documents are filled
                    break

            # retrieve matching documents
            document_ids = self.retrieve_documents((stmt.subject_id, stmt.relation, stmt.object_id))

            for doc_id in document_ids:
                if doc_id not in document_ids_scored:
                    document_ids_scored[doc_id] = stmt.score
                else:
                    document_ids_scored[doc_id] += stmt.score

         # We did not find any documents
        if len(document_ids_scored) == 0:
            return []

        # Get the maximum score to normalize the scores
        max_score = max(document_ids_scored.values())
        if max_score > 0.0:
            # Convert to list
            document_ids_scored = [(k, v / max_score) for k, v in document_ids_scored.items()]
        else:
            document_ids_scored = [(k, v) for k, v in document_ids_scored.items()]
        # Sort by score and then doc desc
        document_ids_scored.sort(key=lambda x: (x[1], x[0]), reverse=True)

        return document_ids_scored

    def retrieve_documents_for(self, document: RecommenderDocument):
        # Compute the cores
        max_core = self.extractor.extract_narrative_core_from_document(document)

        # We dont have any core
        if not max_core:
            return []

        # score documents with this core
        document_ids_scored = self.score_document_ids_with_core(max_core)

        # We did not find any documents
        if len(document_ids_scored) == 0:
            return []

        # Ensure cutoff
        return document_ids_scored[:FS_DOCUMENT_CUTOFF]
