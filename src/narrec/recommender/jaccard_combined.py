from narrec.citation.graph import CitationGraph
from narrec.document.corpus import DocumentCorpus
from narrec.document.document import RecommenderDocument
from narrec.recommender.base import RecommenderBase
from narrec.recommender.jaccard_graph_weighted import JaccardGraphWeighted
from narrec.recommender.jaccard_concepts_weighted import JaccardConceptWeighted


class JaccardCombinedWeighted(RecommenderBase):

    def __init__(self, corpus: DocumentCorpus,
                 jaccard_graph: JaccardGraphWeighted,
                 jaccard_concept: JaccardConceptWeighted,
                 name="JaccardCombinedWeighted"):
        super().__init__(name=name)
        self.corpus = corpus
        self.jaccard_graph = jaccard_graph
        self.jaccard_concept = jaccard_concept

    def compute_document_score(self, doc: RecommenderDocument, candidate: RecommenderDocument,
                               citation_graph: CitationGraph) -> float:
        scores = []
        scores.append(self.jaccard_graph.compute_document_score(doc, candidate, citation_graph))
        scores.append(self.jaccard_concept.compute_document_score(doc, candidate, citation_graph))

        return sum(scores) / len(scores)
