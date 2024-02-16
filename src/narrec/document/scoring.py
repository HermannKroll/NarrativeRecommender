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
    return 0.5 * confidence + 0.5 * tfidf


def score_edge_sentence(statement: tuple, document: RecommenderDocument, corpus: DocumentCorpus):
    assert len(statement) == 3

    confidence = max(document.spo2confidences[statement])
    assert 0.0 <= confidence <= 1.0

    tf = document.spo2frequency[statement] / document.max_statement_frequency
    idf = corpus.get_idf_score(statement)
    tfidf = tf * idf
    assert 0.0 <= tfidf <= 1.0

    sentence_weight = []
    for sentence in document.spo2sentences[statement]:
        sentence_weight.append(1.0 / len(document.sentence2spo[sentence]))

    sentence_weight = sum(sentence_weight) / len(sentence_weight)
    assert 0.0 <= sentence_weight <= 1.0


    return 0.25 * confidence + 0.25 * tfidf + 0.5 * sentence_weight

