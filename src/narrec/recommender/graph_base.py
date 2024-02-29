from narrant.entity.meshontology import MeSHOntology
from narrec.citation.graph import CitationGraph
from narrec.document.document import RecommenderDocument
from narrec.ontology.ontology import Ontology
from narrec.recommender.base import RecommenderBase


class GraphBase(RecommenderBase):
    def __init__(self, threshold, name):
        super().__init__(name=name)
        self.threshold = threshold
        self.ontology = Ontology()

    def ontological_node_similarity(self, node_j, node_k):
        if node_j == node_k:
            return 1.0

        distance = self.ontology.ontological_mesh_distance(node_j, node_k)
        # no distance -> perfect similarity
        if distance == 0:
            return 1.0
        # there is no path between j and k
        elif distance == -1:
            return 0.0
        else:
        # compute similarity
            return 1.0 / distance

    def node_candidates(self, document_i: RecommenderDocument, document_k: RecommenderDocument):
        candidates = []
        nodes_i = document_i.concepts
        nodes_k = document_k.concepts

        for node_a in nodes_i:
            for node_b in nodes_k:
                similarity = self.ontological_node_similarity(node_a, node_b)
                if similarity >= self.threshold:
                    candidates.append((node_a, node_b, similarity))

        return candidates

    def greedy_node_matching(self, document_i: RecommenderDocument, document_k: RecommenderDocument):
        candidates = self.node_candidates(document_i, document_k)
        candidates.sort(key=lambda x: x[2], reverse=True)

        matchings = []
        mapped = set()

        for node_a, node_b, similarity in candidates:
            # we need to distinguish between the same concept nodes in a and b
            node_a_pref = 'a_' + node_a
            node_b_pref = 'b_' + node_b
            if node_a_pref not in mapped and node_b_pref not in mapped:
                mapped.add(node_a_pref)
                mapped.add(node_b_pref)
                matchings.append((node_a, node_b))

        return matchings

    def compute_document_score(self, doc: RecommenderDocument, candidate: RecommenderDocument,
                               citation_graph: CitationGraph) -> float:
        raise NotImplementedError
