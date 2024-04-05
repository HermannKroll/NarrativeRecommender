import pandas as pd
import pyterrier as pt

from narrec.citation.graph import CitationGraph
from narrec.document.corpus import DocumentCorpus
from narrec.document.document import RecommenderDocument
from narrec.recommender.base import RecommenderBase
from narrec.recommender.jaccard_concepts_weighted import JaccardConceptWeighted
from narrec.recommender.jaccard_graph_weighted import JaccardGraphWeighted


class JaccardCombinedWeightedWithBM25(RecommenderBase):

    def __init__(self, corpus: DocumentCorpus,
                 jaccard_graph: JaccardGraphWeighted,
                 jaccard_concept: JaccardConceptWeighted,
                 bm25_index,
                 name="CombinedWeightedWithBM25"):
        super().__init__(name=name)
        if not pt.started():
            pt.init()

        self.corpus = corpus
        self.jaccard_graph = jaccard_graph
        self.jaccard_concept = jaccard_concept

        if bm25_index:
            self.bm25pipeline = pt.BatchRetrieve(
                bm25_index,
                wmodel='BM25',
                properties={'termpipelines': 'Stopwords,PorterStemmer'}
            )
        else:
            self.bm25pipeline = None

    def set_index(self, bm25_index):
        bm25_index = pt.IndexFactory.of(bm25_index, memory=True)
        self.bm25pipeline = pt.BatchRetrieve(
            bm25_index,
            wmodel='BM25',
            properties={'termpipelines': 'Stopwords,PorterStemmer'}
        )

    def filter_query_string(self, query):
        return "".join([x if x.isalnum() else " " for x in query])

    def compute_document_score(self, doc: RecommenderDocument, candidate: RecommenderDocument,
                               citation_graph: CitationGraph) -> float:
        scores = []
        scores.append(self.jaccard_graph.compute_document_score(doc, candidate, citation_graph))
        scores.append(self.jaccard_concept.compute_document_score(doc, candidate, citation_graph))

        df = pd.DataFrame([["q0", self.filter_query_string(doc.get_text_content()), str(candidate.id)]],
                          columns=["qid", "query", "docno"])
        rtr = self.bm25pipeline(df)

        for index, row in rtr.iterrows():
            # transform document id back to internal representation, e.g. PubMed_123 -> 123
            scores.append(((row["docno"]), max(float(row["score"]), 0.0)))
            break

        return sum(scores) / len(scores)
