from kgextractiontoolbox.document.narrative_document import StatementExtraction
from narrec.document.corpus import DocumentCorpus
from narrec.document.document import RecommenderDocument
from narrec.run_config import CONFIDENCE_WEIGHT, TFIDF_WEIGHT


def score_edge(statement: tuple, document: RecommenderDocument, corpus: DocumentCorpus):
    assert len(statement) == 3

    confidence = max(document.spo2confidences[statement])
    assert 0.0 <= confidence <= 1.0

    tf = document.spo2frequency[statement] / document.max_statement_frequency
    idf = corpus.get_idf_score(statement)
    tfidf = tf * idf

    assert 0.0 <= tfidf <= 1.0
    return CONFIDENCE_WEIGHT * confidence + TFIDF_WEIGHT * tfidf