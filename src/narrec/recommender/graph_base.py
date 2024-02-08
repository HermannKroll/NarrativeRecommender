from narrec.citation.graph import CitationGraph
from narrec.document.document import RecommenderDocument
from narrec.recommender.base import RecommenderBase


class GraphBase(RecommenderBase):
    def __init__(self, threshold, name):
        super().__init__(name=name)
        self.threshold = threshold

    @staticmethod
    def ont_path(node_j, node_k):
        #TODO
        return 1

    def ontological_similarity(self, node_j, node_k):
        op = self.ont_path(node_j, node_k)
        if node_j == node_k:
            return 1
        elif op:
            return 1 / abs(op)
        else:
            return 0

    def node_candidates(self, document_i: RecommenderDocument, document_k: RecommenderDocument):
        candidates = []
        nodes_i = document_i.concepts
        nodes_k = document_k.concepts

        for node_a in nodes_i:
            for node_b in nodes_k:
                similarity = self.ontological_similarity(node_a, node_b)
                if similarity >= self.threshold:
                    candidates.append((node_a, node_b, similarity))

        return candidates

    def greedy_node_matching(self, document_i: RecommenderDocument, document_k: RecommenderDocument):
        candidates = self.node_candidates(document_i, document_k)
        candidates.sort(key=lambda x: x[2], reverse=True)

        matchings = []
        mapped = set()

        for node_a, node_b, similarity in candidates:
            if node_a not in mapped and node_b not in mapped:
                mapped.add(node_a)
                mapped.add(node_b)
                matchings.append((node_a, node_b))

        return matchings

    def compute_document_score(self, doc: RecommenderDocument, candidate: RecommenderDocument,
                               citation_graph: CitationGraph) -> float:
        raise NotImplementedError
