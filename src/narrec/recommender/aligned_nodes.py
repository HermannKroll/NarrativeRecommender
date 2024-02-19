from narrec.citation.graph import CitationGraph
from narrec.document.core import NarrativeCoreExtractor
from narrec.document.corpus import DocumentCorpus
from narrec.recommender.graph_base import GraphBase
from narrec.scoring.edge import score_edge
from narrec.document.document import RecommenderDocument


class AlignedNodesRecommender(GraphBase):
    def __init__(self, threshold, corpus: DocumentCorpus):
        super().__init__(threshold)
        self.corpus = corpus
        self.extractor = NarrativeCoreExtractor(corpus=self.corpus)

    def node_score(self, node_a, document_i: RecommenderDocument):
        cores = self.extractor.extract_narrative_core_from_document(document_i)
        if not cores:
            return 0
        core = cores[0]
        scores = [score_edge(statement, document_i, self.corpus) for statement in core.statements if
                  statement.subject_id == node_a]
        avg_score = sum(scores) / len(scores)
        return avg_score

    def compute_document_score(self, doc: RecommenderDocument, candidate: RecommenderDocument,
                               citation_graph: CitationGraph) -> float:
        node_matchings = self.greedy_node_matching(doc, candidate)
        if not node_matchings:
            return 0
        total_score = 0
        for node_a, node_b in node_matchings:
            similarity = self.ontological_similarity(node_a, node_b)
            score = self.node_score(node_b, candidate)
            total_score += similarity * score
        return total_score / len(node_matchings)
