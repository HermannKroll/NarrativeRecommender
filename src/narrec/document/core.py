from typing import List

import networkx as nx

from kgextractiontoolbox.document.narrative_document import StatementExtraction
from narrec.document.corpus import DocumentCorpus
from narrec.document.document import RecommenderDocument
from narrec.run_config import CONFIDENCE_WEIGHT, TFIDF_WEIGHT, NARRATIVE_CORE_THRESHOLD


class ScoredStatementExtraction(StatementExtraction):

    def __init__(self, stmt: StatementExtraction, score: float):
        super().__init__(subject_id=stmt.subject_id, subject_type=stmt.subject_type, subject_str=stmt.subject_str,
                         predicate=stmt.predicate, relation=stmt.relation,
                         object_id=stmt.object_id, object_type=stmt.object_type, object_str=stmt.object_str,
                         sentence_id=stmt.sentence_id, confidence=stmt.confidence)
        self.score = score


class NarrativeCore:

    def __init__(self, statements: List[ScoredStatementExtraction]):
        self.statements = statements
        self.statements.sort(key=lambda x: x.score, reverse=True)
        self.size = len(statements)


class NarrativeCoreExtractor:

    def __init__(self, corpus: DocumentCorpus):
        self.corpus = corpus

    def score_edge(self, statement: StatementExtraction, document: RecommenderDocument):
        confidence = statement.confidence
        assert 0.0 <= confidence <= 1.0

        spo = (statement.subject_id, statement.relation, statement.object_id)

        tf = document.spo2frequency[spo] / document.max_statement_frequency
        idf = self.corpus.get_idf_score((statement.subject_id, statement.relation, statement.object_id))
        tfidf = tf * idf

        assert 0.0 <= tfidf <= 1.0
        return CONFIDENCE_WEIGHT * confidence + TFIDF_WEIGHT * tfidf

    def extract_narrative_core_from_document(self, document: RecommenderDocument,
                                             threshold=NARRATIVE_CORE_THRESHOLD) -> List[NarrativeCore]:
        if not document.extracted_statements:
            return []

        filtered_statements = []
        for statement in document.extracted_statements:
            s_score = self.score_edge(statement, document)
            if s_score >= threshold:
                filtered_statements.append((statement, s_score))

        if not filtered_statements:
            return []

        graph = nx.Graph()
        for statement, score in filtered_statements:
            graph.add_edge(statement.subject_id, statement.object_id)

        # Find all connected components and sort them by their size (No. of nodes)
        # Will produce a sorted list of nodes
        connected_components = [(c, len(c)) for c in sorted(nx.connected_components(graph), key=len, reverse=True)]

        cores = []
        for connected_nodes, size in connected_components:
            core_statements = []
            for statement, score in filtered_statements:
                if statement.subject_id in connected_nodes and statement.object_id in connected_nodes:
                    core_statements.append(ScoredStatementExtraction(stmt=statement, score=score))

            cores.append(NarrativeCore(core_statements))

        return cores
