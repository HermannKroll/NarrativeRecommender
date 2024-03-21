from narrec.citation.graph import CitationGraph
from narrec.document.core import NarrativeCoreExtractor
from narrec.document.corpus import DocumentCorpus
from narrec.document.document import RecommenderDocument
from narrec.recommender.graph_base import GraphBase
from narrec.run_config import NODE_SIMILARITY_THRESHOLD
from narrec.scoring.edge import score_edge_by_tf_and_concept_idf


class AlignedCoresRecommender(GraphBase):
    def __init__(self, corpus: DocumentCorpus, name="AlignedCoresRecommender", threshold=NODE_SIMILARITY_THRESHOLD):
        super().__init__(threshold, name=name)
        self.corpus = corpus
        self.extractor = NarrativeCoreExtractor(corpus=self.corpus)

    def compute_document_score(self, doc: RecommenderDocument, candidate: RecommenderDocument,
                               citation_graph: CitationGraph) -> float:
        node_matchings = self.greedy_node_matching(doc, candidate)
        if len(node_matchings) == 0:
            return 0.0

        similarity_score = 0

        # compute the core of the candidate document
        core = self.extractor.extract_narrative_core_from_document(candidate)
        for (node_a1, node_b1) in node_matchings:
            sim_sum = 0
            count_sum = 0

            for (node_a2, node_b2) in node_matchings:
                for stmt in core.statements:
                    edge = stmt.get_triple()
                    if (edge[0] == node_b1 and edge[2] == node_b2) or (edge[2] == node_b1 and edge[0] == node_b2):
                        osim1 = self.ontological_node_similarity(node_a1, node_b1)
                        osim2 = self.ontological_node_similarity(node_a2, node_b2)
                        tfidf = score_edge_by_tf_and_concept_idf(edge, candidate, self.corpus)
                        sim_sum += osim1 * osim2 * tfidf
                        count_sum += 1

            if count_sum > 0:
                similarity_score += sim_sum #/ count_sum

        return similarity_score #/ len(doc.nodes)
