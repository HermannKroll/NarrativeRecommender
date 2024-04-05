from narrec.citation.graph import CitationGraph
from narrec.document.corpus import DocumentCorpus
from narrec.document.document import RecommenderDocument
from narrec.recommender.base import RecommenderBase
from narrec.scoring.concept import score_concept_by_tf_idf_and_coverage


class JaccardConceptWeighted(RecommenderBase):

    def __init__(self, corpus: DocumentCorpus, name="JaccardConceptWeighted"):
        super().__init__(name=name)
        self.corpus = corpus

    def compute_document_score(self, doc: RecommenderDocument, candidate: RecommenderDocument,
                               citation_graph: CitationGraph) -> float:
        if len(doc.concepts) == 0 or len(candidate.concepts) == 0:
            return 0.0

        concepts_inter = doc.concepts.intersection(candidate.concepts)
        concepts_union = doc.concepts.union(candidate.concepts)

        assert concepts_inter <= concepts_union
        assert len(concepts_inter) <= len(doc.concepts)
        assert len(concepts_union) <= len(doc.concepts) + len(candidate.concepts)

        # Score each edge by its mean between the edge score of both documents
        # It is sure that the edge belongs to both documents
        score_inter = sum([(0.5 * (score_concept_by_tf_idf_and_coverage(c, doc, self.corpus)
                                   + score_concept_by_tf_idf_and_coverage(c, candidate, self.corpus)))
                           for c in concepts_inter])

        score_union = sum([(0.5 * (score_concept_by_tf_idf_and_coverage(c, doc, self.corpus)
                                   + score_concept_by_tf_idf_and_coverage(c, candidate, self.corpus)))
                           for c in concepts_union
                           if c in doc.concepts and c in candidate.concepts])

        score_union += sum(score_concept_by_tf_idf_and_coverage(c, doc, self.corpus)
                           for c in concepts_union
                           if c in doc.concepts and c not in concepts_inter)
        score_union += sum(score_concept_by_tf_idf_and_coverage(c, candidate, self.corpus)
                           for c in concepts_union
                           if c in candidate.concepts and c not in concepts_inter)

        if score_union == 0.0:
            return 0.0

        return score_inter / score_union
