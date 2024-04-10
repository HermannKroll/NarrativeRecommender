from narrec.citation.graph import CitationGraph
from narrec.document.corpus import DocumentCorpus
from narrec.document.document import RecommenderDocument
from narrec.recommender.aligned_nodes import AlignedNodesRecommender
from narrec.run_config import NODE_SIMILARITY_THRESHOLD


class AlignedNodesFallbackRecommender(AlignedNodesRecommender):
    def __init__(self, corpus: DocumentCorpus, threshold=NODE_SIMILARITY_THRESHOLD):
        super().__init__(threshold=threshold, name="AlignedNodesFallbackRecommender", corpus=corpus)

    def compute_document_score(self, doc: RecommenderDocument, candidate: RecommenderDocument,
                               citation_graph: CitationGraph) -> float:
        core_a = self.extractor.extract_narrative_core_from_document(doc)
        core_b = self.extractor.extract_narrative_core_from_document(candidate)

        if core_a and core_b and len(core_a.intersect(core_b).statements) > 0:
            return super().compute_document_score(doc, candidate, citation_graph)
        else:
            return candidate.first_stage_score
