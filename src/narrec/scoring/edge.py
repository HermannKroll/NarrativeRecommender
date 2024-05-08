from narrec.document.corpus import DocumentCorpus
from narrec.document.document import RecommenderDocument

PREDICATE_TO_SCORE = {
    "associated": 0.25,
    "administered": 1.0,
    "compares": 1.0,
    "decreases": 0.5,
    "induces": 1.0,
    "interacts": 0.5,
    "inhibits": 1.0,
    "metabolises": 1.0,
    "treats": 1.0,
    "method": 1.0
}


def score_edge_by_tf_and_concept_idf(statement: tuple, document: RecommenderDocument, corpus: DocumentCorpus):
    assert len(statement) == 3

    confidence = max(document.spo2confidences[statement])
    assert 0.0 <= confidence <= 1.0

    # tf = len(document.spo2sentences[statement]) / document.max_statement_frequency
    if document.concept_count > 0:
        tf_s = document.get_concept_tf(statement[0]) / document.concept_count
        tf_o = document.get_concept_tf(statement[2]) / document.concept_count
    else:
        tf_s = 0.0
        tf_o = 0.0
    idf_s = corpus.get_concept_ifd_score(statement[0])
    idf_o = corpus.get_concept_ifd_score(statement[2])

    tfidf = PREDICATE_TO_SCORE[statement[1]] * (0.5 * ((tf_s * idf_s) + (tf_o * idf_o)))

    coverage = min(document.get_concept_coverage(statement[0]), document.get_concept_coverage(statement[2]))

    assert 0.0 <= tfidf <= 1.0
    assert 0.0 <= confidence <= 1.0
    assert 0.0 <= coverage <= 1.0

    return coverage * confidence * tfidf
