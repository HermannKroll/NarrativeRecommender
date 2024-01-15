from narrec.citation.graph import CitationGraph
from narrec.document.document import RecommenderDocument
from narrec.recommender.base import RecommenderBase


class RecommenderSimple(RecommenderBase):
    
    def __init__(self):
        super().__init__(name="RecommenderSimple")
    
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
        return [(d, 1.0) for d in docs_from]
