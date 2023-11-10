from narrec.citation.graph import CitationGraph
from narrec.document.document import RecommenderDocument


class RecommenderBase:

    def __init__(self, citation_graph: CitationGraph):
        self.citation_graph: CitationGraph = citation_graph
        pass

    def recommend_documents(self, doc: RecommenderDocument, docs_from: [RecommenderDocument]) -> [RecommenderDocument]:
        """
        This abstract method must be implemented in a subclass. The goal is to create a ranked list of relevant
        documents from docs_from which should be recommended for doc
        :param doc: the document for which recommendations should be generated
        :param docs_from: the list of possible documents to recommend
        :return: a ranked list of recommended documents
        """
        raise NotImplementedError
