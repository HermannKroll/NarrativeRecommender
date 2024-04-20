from typing import List

from kgextractiontoolbox.document.narrative_document import StatementExtraction
from narrec.document.corpus import DocumentCorpus
from narrec.document.document import RecommenderDocument
from narrec.run_config import NARRATIVE_CORE_THRESHOLD, CORE_TOP_K
from narrec.scoring.concept import score_concept_by_tf_idf_and_coverage
from narrec.scoring.edge import score_edge_by_tf_and_concept_idf


class ScoredConcept:

    def __init__(self, concept: str, score: float, coverage: float, support: int):
        self.concept = concept
        self.score = score
        self.coverage = coverage
        self.support = support

    def __str__(self):
        return f'{round(self.score, 2)}: {self.concept} (coverage: {self.coverage} / support: {self.support})'

    def __repr__(self):
        return self.__str__()


class ScoredStatementExtraction(StatementExtraction):

    def __init__(self, stmt: StatementExtraction, score: float):
        super().__init__(subject_id=stmt.subject_id, subject_type=stmt.subject_type, subject_str=stmt.subject_str,
                         predicate=stmt.predicate, relation=stmt.relation,
                         object_id=stmt.object_id, object_type=stmt.object_type, object_str=stmt.object_str,
                         sentence_id=stmt.sentence_id, confidence=stmt.confidence)
        self.score = score

    def get_triple(self):
        return self.subject_id, self.relation, self.object_id

    def is_equal(self, other):
        if not isinstance(other, ScoredStatementExtraction):
            return False

        a = (self.subject_id == other.subject_id and self.object_id == other.object_id)
        b = (self.object_id == other.subject_id and self.subject_id == other.object_id)
        return a or b

    def __str__(self):
        return f'{self.score}: ({self.subject_id}, {self.relation}, {self.object_id})'

    def __repr__(self):
        return self.__str__()


class NarrativeConceptCore:

    def __init__(self, concepts: List[ScoredConcept]):
        self.concepts = concepts


class NarrativeCore:

    def __init__(self, statements: List[ScoredStatementExtraction]):
        self.statements = statements
        self.statements.sort(key=lambda x: x.score, reverse=True)
        self.size = len(statements)
        self.graph = {(s.subject_id, s.relation, s.object_id) for s in self.statements}

    def contains_statement(self, spo) -> bool:
        return spo in self.graph

    def intersect(self, other):
        if not isinstance(other, NarrativeCore):
            return None

        statements = []
        for a in self.statements:
            found = False
            for b in other.statements:
                if a.is_equal(b):
                    found = True
                    break
            if found:
                statements.append(a)
        return NarrativeCore(statements)


class NarrativeCoreExtractor:

    def __init__(self, corpus: DocumentCorpus):
        self.corpus = corpus
        self.cache = dict()

    def extract_concept_core(self, document: RecommenderDocument) -> NarrativeConceptCore:
        if not document.concepts:
            return None

        scored_concepts = []
        for concept in document.concepts:
            score = score_concept_by_tf_idf_and_coverage(concept, document, self.corpus)
            coverage = document.get_concept_coverage(concept)
            support = self.corpus.get_concept_support(concept)
            if score >= NARRATIVE_CORE_THRESHOLD and support <= 1000000:
                scored_concepts.append(ScoredConcept(concept, score, coverage, support))

        # sort remaining ones by score
        scored_concepts.sort(key=lambda x: x.score, reverse=True)

        return NarrativeConceptCore(scored_concepts)

    def extract_narrative_core_from_document(self, document: RecommenderDocument) -> NarrativeCore:
        if document.id in self.cache:
            return self.cache[document.id]

        if not document.extracted_statements:
            return None

        filtered_statements = []
        s_scores = []
        for statement in document.extracted_statements:
            spo = (statement.subject_id, statement.relation, statement.object_id)

            s_score = score_edge_by_tf_and_concept_idf(spo, document, self.corpus)
            if s_score >= NARRATIVE_CORE_THRESHOLD:
                s_scores.append(s_score)
                filtered_statements.append(ScoredStatementExtraction(stmt=statement, score=s_score))

        if not filtered_statements:
            return None

        # sort filtered statements by score
        filtered_statements.sort(key=lambda x: x.score, reverse=True)

        core_node_pairs = set()
        # The following algorithm will be design select the highest scored edges between two
        # nodes because filtered statements are sorted by their score desc
        # for connected_nodes, size in connected_components:
        core_statements = []
        for statement in filtered_statements:
            # add only the strongest edge between two nodes (could be caused by multiple extractions)
            so = (statement.subject_id, statement.object_id)
            os = (statement.object_id, statement.subject_id)
            # Check whether we already added an edge between s and o or o and s
            if so in core_node_pairs or os in core_node_pairs:
                continue

            # if statement.subject_id in connected_nodes and statement.object_id in connected_nodes:
            core_statements.append(statement)
            core_node_pairs.add(so)

        core = NarrativeCore(core_statements)
        self.cache[document.id] = core
        return core
