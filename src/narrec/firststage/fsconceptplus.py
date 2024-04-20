import ast

from narrec.backend.database import SessionRecommender
from narrec.backend.models import TagInvertedIndexScored
from narrec.benchmark.benchmark import Benchmark
from narrec.document.core import NarrativeCoreExtractor, NarrativeConceptCore
from narrec.document.document import RecommenderDocument
from narrec.firststage.base import FirstStageBase
from narrec.run_config import FS_DOCUMENT_CUTOFF


class FSConceptPlus(FirstStageBase):

    def __init__(self, extractor: NarrativeCoreExtractor, benchmark: Benchmark, name="FSConceptPlus"):
        super().__init__(name=name)
        self.extractor = extractor
        self.benchmark = benchmark
        self.session = SessionRecommender.get()
        self.concept2documents = dict()

    def retrieve_documents(self, concept: str):
        if concept in self.concept2documents:
            return self.concept2documents[concept]

        q = self.session.query(TagInvertedIndexScored)
        # Search for matching nodes but not for predicates (ignore direction)
        q = q.filter(TagInvertedIndexScored.entity_id == concept)
        q = q.filter(TagInvertedIndexScored.document_collection == self.benchmark.document_collection)

        doc_scores = list()
        for row in q:
            scored_docs = ast.literal_eval(row.scored_document_ids)
            for did, tf, score in scored_docs:
                # if its pubmed use the filter for possible benchmark documents
                if self.benchmark.document_collection == "PubMed" and self.benchmark.get_documents_for_baseline():
                    if did not in self.benchmark.get_documents_for_baseline():
                        continue
                doc_scores.append((did, tf, score))

        # add to cache
        self.concept2documents[concept] = doc_scores
        return doc_scores

    def score_document_ids_with_core(self, core: NarrativeConceptCore):
        # Core statements are also sorted by their score
        document_ids_scored = {}
        # If a statement of the core is contained within a document, we increase the score
        # of the document by the score of the corresponding edge
        for idx, concept in enumerate(core.concepts):
            # retrieve matching documents
            doc2score = self.retrieve_documents(concept.concept)

            for doc_id, tf, score in doc2score:
                if doc_id not in document_ids_scored:
                    document_ids_scored[doc_id] = score
                else:
                    document_ids_scored[doc_id] += score

        return FirstStageBase.normalize_and_sort_document_scores(document_ids_scored)

    def retrieve_documents_for(self, document: RecommenderDocument):
        # Compute the cores
        core = self.extractor.extract_concept_core(document)

        # We dont have any core
        if not core:
            return []

        # score documents with this core
        document_ids_scored = self.score_document_ids_with_core(core)

        # We did not find any documents
        if len(document_ids_scored) == 0:
            return []

        # Ensure cutoff
        return document_ids_scored[:FS_DOCUMENT_CUTOFF]
