from narrec.document.corpus import DocumentCorpus
from narrec.document.document import RecommenderDocument


def score_edge_confidence(statement: tuple, document: RecommenderDocument, corpus: DocumentCorpus):
    assert len(statement) == 3

    confidence = max(document.spo2confidences[statement])
    assert 0.0 <= confidence <= 1.0

    return confidence


def score_edge_tfidf(statement: tuple, document: RecommenderDocument, corpus: DocumentCorpus):
    assert len(statement) == 3

    tf = document.spo2frequency[statement] / document.max_statement_frequency
    idf = corpus.get_idf_score(statement)
    tfidf = tf * idf

    return tfidf


def score_edge_tfidf_sentences(statement: tuple, document: RecommenderDocument, corpus: DocumentCorpus):
    assert len(statement) == 3

    tf = len(document.spo2sentences[statement]) / document.max_statement_frequency
    idf = corpus.get_idf_score(statement)
    tfidf = tf * idf

    return tfidf


def score_edge(statement: tuple, document: RecommenderDocument, corpus: DocumentCorpus):
    assert len(statement) == 3

    confidence = max(document.spo2confidences[statement])
    assert 0.0 <= confidence <= 1.0

    tf = document.spo2frequency[statement] / document.max_statement_frequency
    idf = corpus.get_idf_score(statement)
    tfidf = tf * idf

    assert 0.0 <= tfidf <= 1.0
    return 0.5 * confidence + 0.5 * tfidf


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
    tf_s = document.get_concept_tf(statement[0]) / document.max_concept_frequency
    tf_o = document.get_concept_tf(statement[2]) / document.max_concept_frequency
    idf_s = corpus.get_concept_ifd_score(statement[0])
    idf_o = corpus.get_concept_ifd_score(statement[2])
    # idf_statement = corpus.get_idf_score(statement)

    tfidf = PREDICATE_TO_SCORE[statement[1]] * ((tf_s * idf_s) + (tf_o * idf_o))

    position_score = min(document.get_concept_relative_text_position(statement[0]),
                         document.get_concept_relative_text_position(statement[2]))

    # tfidf = tf * ((idf_s + idf_o) * 0.5)

    # assert 0.0 <= tf <= 1.0

    return position_score * confidence * tfidf


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


def score_edge_connectivity(statement: tuple, document: RecommenderDocument, corpus: DocumentCorpus):
    nodes = {statement[0], statement[2]}

    counter = 0
    for s, _, o in document.graph:
        # don't count edges between the fragment
        if s in nodes and o in nodes:
            continue
        if s in nodes or o in nodes:
            counter += 1

    return counter
