from narrec.citation.graph import CitationGraph
from narrec.document.core import NarrativeCoreExtractor
from narrec.document.corpus import DocumentCorpus
from narrec.document.document import RecommenderDocument
from narrec.recommender.graph_base import GraphBase


class AlignedCoresRecommender(GraphBase):
    def __init__(self, corpus: DocumentCorpus, name="AlignedCoresRecommender"):
        super().__init__(name=name)
        self.corpus = corpus
        self.extractor = NarrativeCoreExtractor(corpus=self.corpus)

    def compute_document_score(self, doc: RecommenderDocument, candidate: RecommenderDocument,
                               citation_graph: CitationGraph) -> float:
        node_matchings = self.greedy_node_matching(doc, candidate)
        if len(node_matchings) == 0:
            return 0.0

        similarity_score = 0

        # compute the core of the candidate document
        candidate_core = self.extractor.extract_narrative_core_from_document(candidate)
        if not candidate_core:
            return 0.0

        for node_a1, node_b1, osim1 in node_matchings:
            for node_a2, node_b2, osim2 in node_matchings:
                for stmt in candidate_core.statements:
                    edge = stmt.get_triple()
                    if edge[0] == node_b1 and edge[2] == node_b2:
                        similarity_score += osim1 * osim2 * stmt.score

        return similarity_score
