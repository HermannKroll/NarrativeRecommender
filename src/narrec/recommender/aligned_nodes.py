from narrec.citation.graph import CitationGraph
from narrec.document.core import NarrativeCoreExtractor, NarrativeCore
from narrec.document.corpus import DocumentCorpus
from narrec.document.document import RecommenderDocument
from narrec.recommender.graph_base import GraphBase


class AlignedNodesRecommender(GraphBase):
    def __init__(self, corpus: DocumentCorpus, name="AlignedNodesRecommender"):
        super().__init__(name=name)
        self.corpus = corpus
        self.extractor = NarrativeCoreExtractor(corpus=self.corpus)

    def node_score(self, node, candidate_core: NarrativeCore):
        scores = [statement.score
                  for statement in candidate_core.statements
                  if statement.subject_id == node or statement.object_id == node]
        if len(scores) == 0:
            return 0.0
        return sum(scores) # / len(scores)

    def compute_document_score(self, doc: RecommenderDocument, candidate: RecommenderDocument,
                               citation_graph: CitationGraph) -> float:
        node_matchings = self.greedy_node_matching(doc, candidate)
        if len(node_matchings) == 0:
            return 0.0

        candidate_core = self.extractor.extract_narrative_core_from_document(candidate)
        if not candidate_core:
            return 0.0

        total_score = 0
        for node_a, node_b, osim in node_matchings:
            total_score += osim * self.node_score(node_b, candidate_core)
        return total_score
