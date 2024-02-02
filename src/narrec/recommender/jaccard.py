from narrec.citation.graph import CitationGraph
from narrec.document.core import NarrativeCoreExtractor
from narrec.document.document import RecommenderDocument
from narrec.recommender.base import RecommenderBase


class Jaccard(RecommenderBase):

    def __init__(self, name="Jaccard"):
        super().__init__(name=name)

    def compute_document_score(self, doc: RecommenderDocument, candidate: RecommenderDocument,
                               citation_graph: CitationGraph) -> float:
        if len(doc.graph) == 0 or len(candidate.graph) == 0:
            return 0.0

        graph_inter = doc.graph.intersection(candidate.graph)
        graph_union = doc.graph.union(candidate.graph)
        score = len(graph_inter) / len(graph_union)
        return score
