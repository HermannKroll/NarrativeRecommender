from narrec.citation.graph import CitationGraph
from narrec.document.document import RecommenderDocument


class RecommenderBase:

    def __init__(self, name):
        self.name = name

    def recommend_documents(self, doc: RecommenderDocument, docs_from: [RecommenderDocument],
                            citation_graph: CitationGraph) -> [RecommenderDocument]:
        """
        This abstract method must be implemented in a subclass. The goal is to create a ranked list of relevant
        documents from docs_from which should be recommended for doc
        :param doc: the document for which recommendations should be generated
        :param docs_from: the list of possible documents to recommend
        :param citation_graph: citation network
        :return: a ranked list of recommended documents
        """
        document_ids_scored = dict()
        for candidate in docs_from:
            document_ids_scored[candidate.id] = self.compute_document_score(doc, candidate, citation_graph)

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

    def compute_document_score(self, doc: RecommenderDocument, candidate: RecommenderDocument,
                               citation_graph: CitationGraph) -> float:
        raise NotImplementedError
