from narrec.citation.graph import CitationGraph
from narrec.document.core import NarrativeCoreExtractor
from narrec.document.document import RecommenderDocument
from narrec.recommender.base import RecommenderBase


class StatementOverlap(RecommenderBase):

    def __init__(self, extractor: NarrativeCoreExtractor, name="StatementOverlap"):
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
        # If a statement of the core is contained within a document, we increase the score
        # of the document by the score of the corresponding edge
        for stmt in core.statements:
            for candidate in docs_from:
                if (stmt.subject_id, stmt.relation, stmt.object_id) in candidate.graph:
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
