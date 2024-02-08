from narrec.citation.graph import CitationGraph
from narrec.document.corpus import DocumentCorpus
from narrec.recommender.graph_base import GraphBase
from narrec.document.scoring import score_edge
from narrec.document.document import RecommenderDocument


class AlignedCoresRecommender(GraphBase):
    def __init__(self, threshold, corpus: DocumentCorpus):
        super().__init__(threshold)
        self.corpus = corpus

    def compute_document_score(self, doc: RecommenderDocument, candidate: RecommenderDocument,
                               citation_graph: CitationGraph) -> float:
        node_matchings = self.greedy_node_matching(doc, candidate)

        similarity_score = 0

        for (node_a1, node_b1) in node_matchings:
            sim_sum = 0
            count_sum = 0

            for (node_a2, node_b2) in node_matchings:
                for edge in candidate.extracted_statements:
                    if edge.subject_id == node_b1 and edge.object_id == node_b2:
                        sim_sum += self.ontological_similarity(node_a1, node_b1) * self.ontological_similarity(node_a2,
                                                                                                               node_b2) * score_edge(
                            edge, candidate, self.corpus)
                        count_sum += 1

            if count_sum > 0:
                similarity_score += sim_sum / count_sum

        return similarity_score / len(node_matchings)