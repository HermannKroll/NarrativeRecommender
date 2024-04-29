from typing import Dict

from narrec.citation.graph import CitationGraph
from narrec.document.document import RecommenderDocument
from narrec.recommender.graph_base import GraphBase
from narrec.scoring.BM25Scorer import BM25Scorer


class BM25Recommender(GraphBase):
    def __init__(self, bm25scorer: BM25Scorer):
        super().__init__(name="BM25Recommender")
        self.bm25_scorer = bm25scorer

    def recommend_documents(self, doc: RecommenderDocument, docs_from: [RecommenderDocument],
                            citation_graph: CitationGraph) -> [RecommenderDocument]:
        # then score every document with BM25
        document_ids_scored_bm25 = self.bm25_scorer.score_document_ids_with_bm25(doc, [d.id for d in docs_from])

        # Sort by score and then doc desc
        document_ids_scored_bm25 = sorted([(k, v) for k, v in document_ids_scored_bm25.items()],
                                          key=lambda x: (x[1], x[0]), reverse=True)
        # Ensure cutoff
        return document_ids_scored_bm25
