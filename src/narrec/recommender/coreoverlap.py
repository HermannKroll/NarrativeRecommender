from narrec.citation.graph import CitationGraph
from narrec.document.core import NarrativeCoreExtractor
from narrec.document.document import RecommenderDocument
from narrec.recommender.base import RecommenderBase


class CoreOverlap(RecommenderBase):

    def __init__(self, extractor: NarrativeCoreExtractor, name="CoreOverlap"):
        super().__init__(name=name)
        self.extractor = extractor

    def recommend_documents(self, doc: RecommenderDocument, docs_from: [RecommenderDocument],
                            citation_graph: CitationGraph) -> [RecommenderDocument]:
        # Compute the cores
        # scores are sorted by their size
        core = self.extractor.extract_narrative_core_from_document(doc)
        if not core:
            return [(d.id, 1.0) for d in docs_from]

        # Core statements are also sorted by their score
        document_ids_scored = {d.id: 0.0 for d in docs_from}
        for candidate in docs_from:
            cand_core = self.extractor.extract_narrative_core_from_document(candidate)

            for stmt in core.intersect(cand_core):
                document_ids_scored[candidate.id] += stmt.score

        # Get the maximum score to normalize the scores
        max_score = max(document_ids_scored.values())
        # Convert to list
        if max_score > 0.0:
            document_ids_scored = [(k, v / max_score) for k, v in document_ids_scored.items()]
        else:
            document_ids_scored = [(k, v) for k, v in document_ids_scored.items()]
        # Sort by score and then doc desc
        document_ids_scored.sort(key=lambda x: (x[1], x[0]), reverse=True)
        # Ensure cutoff
        return document_ids_scored
