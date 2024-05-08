from narrec.document.corpus import DocumentCorpus
from narrec.document.document import RecommenderDocument


def score_concept_by_tf_idf_and_coverage(concept: str, document: RecommenderDocument, corpus: DocumentCorpus):
    tf = document.get_concept_tf(concept) / document.concept_count
    idf = corpus.get_concept_ifd_score(concept)
    tfidf = tf * idf

    coverage = document.get_concept_coverage(concept)

    return coverage * tfidf
