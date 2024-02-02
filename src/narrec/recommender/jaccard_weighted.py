from narrec.citation.graph import CitationGraph
from narrec.document.corpus import DocumentCorpus
from narrec.document.document import RecommenderDocument
from narrec.document.scoring import score_edge
from narrec.recommender.base import RecommenderBase


class JaccardWeighted(RecommenderBase):

    def __init__(self, corpus: DocumentCorpus, name="JaccardWeighted"):
        super().__init__(name=name)
        self.corpus = corpus

    def compute_document_score(self, doc: RecommenderDocument, candidate: RecommenderDocument,
                               citation_graph: CitationGraph) -> float:
        if len(doc.graph) == 0 or len(candidate.graph) == 0:
            return 0.0

        graph_inter = doc.graph.intersection(candidate.graph)
        graph_union = doc.graph.union(candidate.graph)

        assert graph_inter <= graph_union
        assert len(graph_inter) <= len(doc.graph)
        assert len(graph_union) <= len(doc.graph) + len(candidate.graph)

        # Score each edge by its mean between the edge score of both documents
        # It is sure that the edge belongs to both documents
        score_inter = sum([(0.5 * (score_edge(spo, doc, self.corpus)
                                   + score_edge(spo, candidate, self.corpus)))
                           for spo in graph_inter])

        score_union = sum([(0.5 * (score_edge(spo, doc, self.corpus)
                                   + score_edge(spo, candidate, self.corpus)))
                           for spo in graph_union
                           if spo in doc.graph and spo in candidate.graph])

        score_union += sum(score_edge(spo, doc, self.corpus) for spo in graph_union
                           if spo in doc.graph and spo not in graph_inter)
        score_union += sum(score_edge(spo, candidate, self.corpus) for spo in graph_union
                           if spo in candidate.graph and spo not in graph_inter)

        if score_union == 0.0:
            return 0.0

        return score_inter / score_union
