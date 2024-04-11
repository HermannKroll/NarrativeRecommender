from typing import Dict

from narrec.citation.graph import CitationGraph
from narrec.document.document import RecommenderDocument
from narrec.recommender.base import RecommenderBase
from narrec.recommender.graph_base import GraphBase
from narrec.run_config import BM25_WEIGHT, GRAPH_WEIGHT
from narrec.scoring.BM25Scorer import BM25Scorer


class GraphBaseFallbackBM25(GraphBase):
    def __init__(self, bm25scorer: BM25Scorer, graph_recommender: RecommenderBase):
        name = f'{graph_recommender.name}_BM25Fallback'
        super().__init__(name=name)
        self.bm25_scorer = bm25scorer
        self.graph_recommender = graph_recommender

    @staticmethod
    def normalize_scores(document_ids_scored: Dict[str, float]) -> Dict[str, float]:
        # Get the maximum score to normalize the scores
        max_score = max(document_ids_scored.values())
        # Convert to list
        if max_score > 0.0:
            document_ids_scored = {k: (v / max_score) for k, v in document_ids_scored.items()}
        # Ensure cutoff
        return document_ids_scored

    def recommend_documents(self, doc: RecommenderDocument, docs_from: [RecommenderDocument],
                            citation_graph: CitationGraph) -> [RecommenderDocument]:
        # first score every document with the implemented graph strategy
        document_ids_scored_graph = self.graph_recommender.recommend_documents(doc, docs_from, citation_graph)
        # convert to dictionary
        document_ids_scored_graph = {k: v for k, v in document_ids_scored_graph}
        document_ids_scored_graph = GraphBaseFallbackBM25.normalize_scores(document_ids_scored_graph)

        # then score every document with BM25
        document_ids_scored_bm25 = self.bm25_scorer.score_document_ids_with_bm25(doc, [d.id for d in docs_from])
        document_ids_scored_bm25 = GraphBaseFallbackBM25.normalize_scores(document_ids_scored_bm25)

        document_ids_scored = {}
        for d, graph_score in document_ids_scored_graph.items():
            document_ids_scored[d] = GRAPH_WEIGHT * graph_score + BM25_WEIGHT * document_ids_scored_bm25[d]

        # Sort by score and then doc desc
        document_ids_scored = sorted([(k, v) for k, v in document_ids_scored.items()],
                                     key=lambda x: (x[1], x[0]), reverse=True)
        # Ensure cutoff
        return document_ids_scored
