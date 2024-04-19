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
            # we already found enough documents
            if len(document_ids_scored) >= FS_DOCUMENT_CUTOFF:
                # get the remaining reachable score
                # if all documents that we found are above the reachable score, we can stop
                max_reachable_scores = sum(c.score for c in core.concepts[idx:])
                count = len([d for d, s in document_ids_scored.items()
                             if s >= max_reachable_scores])
                if count >= FS_DOCUMENT_CUTOFF:
                    # we can't find better documents, stop here
                    # the first K documents are filled
                    break
            # retrieve matching documents
            doc2score = self.retrieve_documents(concept.concept)

            for doc_id, tf, score in doc2score:
                if doc_id not in document_ids_scored:
                    document_ids_scored[doc_id] = concept.score * score
                else:
                    document_ids_scored[doc_id] += concept.score * score

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
        document_ids_scored.sort(key=lambda x: (x[1], int(x[0])), reverse=True)

        return document_ids_scored

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
